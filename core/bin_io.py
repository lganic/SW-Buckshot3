"""
Reading and writing Stormworks map geometry .bin files through sw_ducky.

Lines live in the editor as connected points; on export they are walked
into continuous paths and handed to MapGeometry.add_path, so ducky can
mitre join each run (what playground/add_lines.py did by proximity).
"""
import math
from dataclasses import dataclass, field

import numpy as np

from .constants import RENDER_ORDER, NUM_CHANNELS
from .contours import walk_paths

try:
    from sw_ducky import MapGeometry
    DUCKY_ERROR = None
except Exception as e:   # pragma: no cover - environment dependent
    MapGeometry = None
    DUCKY_ERROR = e


def require_ducky():
    if MapGeometry is None:
        raise RuntimeError(f'sw_ducky could not be imported ({DUCKY_ERROR}). '
                           'Install SW-Ducky into this Python environment.')


@dataclass
class TileData:
    """Plain tile contents: {layer: (verts, tris)} and per-channel (points, edges)."""
    layers: dict = field(default_factory=dict)
    channels: list = field(default_factory=list)
    segments: list = field(default_factory=list)   # per channel, raw (a, b) segments for drawing

    def tri_count(self):
        return sum(len(t) for _, t in self.layers.values())

    def line_count(self):
        return sum(len(s) for s in self.segments)


def _quad_to_segment(quad):
    (a, b, c, d) = quad[:4]
    return (((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), ((c[0] + d[0]) / 2, (c[1] + d[1]) / 2))


def load_bin(path: str) -> TileData:
    require_ducky()
    mg = MapGeometry.from_file(path)
    td = TileData()
    for name in RENDER_ORDER:
        verts = [(float(x), float(y)) for x, y in mg.terrain_vertices.get(name, [])]
        tris = [tuple(int(i) for i in t) for t in mg.terrain_tris.get(name, [])]
        td.layers[name] = (verts, tris)

    for ch in range(NUM_CHANNELS):
        quads = mg.line_data[ch] if ch < len(mg.line_data) else []
        segs = [_quad_to_segment(q) for q in quads if len(q) >= 4]
        td.segments.append(segs)
        td.channels.append(segments_to_graph(segs))
    return td


def segments_to_graph(segs, weld=1e-3):
    """Weld loose segments into (points, edges) so consecutive quads become one line."""
    if not segs:
        return ([], [])
    arr = np.array(segs, np.float64).reshape(-1, 2, 2)
    flat = arr.reshape(-1, 2)
    keys = np.round(flat / weld).astype(np.int64)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    pts = np.zeros((len(uniq), 2))
    pts[inv] = flat
    edges = inv.reshape(-1, 2)
    edges = edges[edges[:, 0] != edges[:, 1]]
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    return (pts.tolist(), edges.tolist())


# ---- export ----

def _signed_area2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def graph_paths(graph):
    """Continuous point paths for one line channel."""
    verts, edges = graph.compact()
    return [[verts[i] for i in p] for p in walk_paths(edges)]


def split_for_mitre(path, min_len=1e-3, max_turn_deg=135.0):
    """
    Remove duplicate points and break paths at near-reversals, where a mitre
    join would explode into a huge spike (or divide by zero in ducky).
    """
    pts = []
    for p in path:
        if not pts or math.dist(p, pts[-1]) > min_len:
            pts.append(tuple(p))
    if len(pts) < 2:
        return []
    limit = math.cos(math.radians(max_turn_deg))
    out, cur = [], [pts[0], pts[1]]
    for p in pts[2:]:
        a, b = cur[-2], cur[-1]
        u = (b[0] - a[0], b[1] - a[1])
        v = (p[0] - b[0], p[1] - b[1])
        cosang = (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))
        if cosang < limit:
            out.append(cur)
            cur = [b, p]
        else:
            cur.append(p)
    out.append(cur)
    return out


def build_map_geometry(doc):
    require_ducky()
    mg = MapGeometry()
    stats = {'tris': 0, 'paths': 0, 'quads': 0}
    for name in RENDER_ORDER:
        verts, tris = doc.layers[name].compact()
        fixed = []
        for i, j, k in tris:
            area = _signed_area2(verts[i], verts[j], verts[k])
            if area == 0:
                continue
            fixed.append((i, j, k) if area > 0 else (i, k, j))   # counter-clockwise, +Y up
        mg.terrain_vertices[name] = [tuple(v) for v in verts]
        mg.terrain_tris[name] = fixed
        stats['tris'] += len(fixed)

    mg.clear_all_lines()
    for ch in range(NUM_CHANNELS):
        for path in graph_paths(doc.channels[ch]):
            for piece in split_for_mitre(path):
                before = len(mg.line_data[ch])
                mg.add_path(ch, piece)
                stats['paths'] += 1
                stats['quads'] += len(mg.line_data[ch]) - before
    return mg, stats


def export_bin(doc, path):
    mg, stats = build_map_geometry(doc)
    mg.save_as(path)
    return stats


def doc_to_tiledata(doc) -> TileData:
    td = TileData()
    for name in RENDER_ORDER:
        td.layers[name] = doc.layers[name].compact()
    for ch in range(NUM_CHANNELS):
        pts, edges = doc.channels[ch].compact()
        td.channels.append((pts, edges))
        td.segments.append([(pts[a], pts[b]) for a, b in edges])
    return td
