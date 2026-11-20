"""
Contour (iso-height) line extraction from 3D meshes, plus polyline helpers.

Replaces GrunkShoreline from rendering/grunk2.py: same half-open convention
(vertices exactly at the level count as above), but vectorised, welded into
connected polylines, simplified, and clipped to the tile.
"""
from collections import defaultdict

import numpy as np

from .constants import TILE_HALF


def contour_segments(pos: np.ndarray, tris: np.ndarray, level: float) -> np.ndarray:
    """Return (K, 2, 2) segments in tile coords (x, mesh z) where the mesh crosses `level`."""
    if len(tris) == 0:
        return np.zeros((0, 2, 2))

    tp = pos[tris]                                  # (M, 3, 3)
    above = tp[:, :, 1] >= level                    # (M, 3)
    points = np.zeros((len(tris), 3, 2))
    crosses = np.zeros((len(tris), 3), bool)

    for e, (i, j) in enumerate(((0, 1), (1, 2), (2, 0))):
        a, b = tp[:, i], tp[:, j]
        # Order each edge's endpoints canonically, so the shared edge of two
        # neighbouring triangles produces bit-identical crossing points.
        swap = (a[:, 0] > b[:, 0]) | ((a[:, 0] == b[:, 0]) & ((a[:, 2] > b[:, 2]) |
                                       ((a[:, 2] == b[:, 2]) & (a[:, 1] > b[:, 1]))))
        a, b = np.where(swap[:, None], b, a), np.where(swap[:, None], a, b)
        c = above[:, i] != above[:, j]
        ya, yb = a[:, 1] - level, b[:, 1] - level
        denom = np.where(c, ya - yb, 1.0)
        t = np.where(c, ya / denom, 0.0)
        points[:, e, 0] = a[:, 0] + t * (b[:, 0] - a[:, 0])
        points[:, e, 1] = a[:, 2] + t * (b[:, 2] - a[:, 2])
        crosses[:, e] = c

    sel = crosses.sum(axis=1) == 2
    if not sel.any():
        return np.zeros((0, 2, 2))
    pts, cr = points[sel], crosses[sel]
    which = np.argsort(~cr, axis=1, kind='stable')[:, :2]
    seg = np.take_along_axis(pts, which[:, :, None], axis=1)
    keep = np.any(seg[:, 0] != seg[:, 1], axis=1)
    return seg[keep]


def chain_segments(segments: np.ndarray, weld: float = 1e-4):
    """Weld segment endpoints and chain them into polylines. Returns list of (P, 2) arrays."""
    if len(segments) == 0:
        return []
    flat = segments.reshape(-1, 2)
    keys = np.round(flat / weld).astype(np.int64)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    node_pos = np.zeros((len(uniq), 2))
    node_pos[inv] = flat
    edges = inv.reshape(-1, 2)
    edges = edges[edges[:, 0] != edges[:, 1]]
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    return [node_pos[p] for p in walk_paths(edges.tolist())]


def walk_paths(edges):
    """
    Decompose an undirected graph (list of (a, b) node pairs) into simple paths.
    Paths run between nodes whose degree is not 2; leftover cycles are returned
    closed (first node repeated at the end).
    """
    adj = defaultdict(list)
    for ei, (a, b) in enumerate(edges):
        adj[a].append((b, ei))
        adj[b].append((a, ei))
    used = [False] * len(edges)
    paths = []

    def walk(start, nxt, ei):
        used[ei] = True
        path = [start, nxt]
        cur = nxt
        while len(adj[cur]) == 2 and cur != start:
            step = next(((n, e) for n, e in adj[cur] if not used[e]), None)
            if step is None:
                break
            used[step[1]] = True
            cur = step[0]
            path.append(cur)
        return path

    for node, nbrs in adj.items():
        if len(nbrs) != 2:
            for n, ei in nbrs:
                if not used[ei]:
                    paths.append(walk(node, n, ei))
    for ei, (a, b) in enumerate(edges):
        if not used[ei]:
            paths.append(walk(a, b, ei))   # a cycle: walk comes back to `a`
    return paths


def simplify(poly: np.ndarray, tol: float) -> np.ndarray:
    """Ramer-Douglas-Peucker. Closed polylines (first == last) keep their closure."""
    if tol <= 0 or len(poly) < 3:
        return poly
    closed = np.allclose(poly[0], poly[-1])
    if closed:
        # Split the loop at the point farthest from the start so RDP has two real ends.
        far = int(np.argmax(np.hypot(*(poly - poly[0]).T)))
        if far == 0:
            return poly
        a = _rdp(poly[:far + 1], tol)
        b = _rdp(poly[far:], tol)
        return np.vstack([a, b[1:]])
    return _rdp(poly, tol)


def _rdp(poly, tol):
    keep = np.zeros(len(poly), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(poly) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = poly[i], poly[j]
        seg = poly[i + 1:j]
        d = b - a
        L = np.hypot(*d)
        if L == 0:
            dist = np.hypot(*(seg - a).T)
        else:
            dist = np.abs(d[0] * (seg[:, 1] - a[1]) - d[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack.append((i, m))
            stack.append((m, j))
    return poly[keep]


def clip_polyline(poly: np.ndarray, lo=-TILE_HALF, hi=TILE_HALF):
    """Clip a polyline to the square [lo, hi]^2, returning a list of pieces."""
    pieces, cur = [], []
    for p, q in zip(poly[:-1], poly[1:]):
        r = _clip_segment(p, q, lo, hi)
        if r is None:
            if len(cur) >= 2:
                pieces.append(np.array(cur))
            cur = []
            continue
        a, b, a_clipped, b_clipped = r
        if not cur or a_clipped:
            if len(cur) >= 2:
                pieces.append(np.array(cur))
            cur = [a]
        cur.append(b)
        if b_clipped:
            pieces.append(np.array(cur))
            cur = []
    if len(cur) >= 2:
        pieces.append(np.array(cur))
    return pieces


def _clip_segment(p, q, lo, hi):
    """Liang-Barsky. Returns (a, b, a_was_clipped, b_was_clipped) or None."""
    t0, t1 = 0.0, 1.0
    d = q - p
    for k in (0, 1):
        for pk, qk in ((-d[k], p[k] - lo), (d[k], hi - p[k])):
            if pk == 0:
                if qk < 0:
                    return None
            else:
                t = qk / pk
                if pk < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
    if t0 > t1:
        return None
    return p + t0 * d, p + t1 * d, t0 > 0, t1 < 1


def extract_contours(contour_meshes, level: float, tol: float, clip=True):
    """All polylines for one level across every mesh that contributes contours."""
    segs = [contour_segments(pos, tris, level) for pos, tris in contour_meshes]
    segs = [s for s in segs if len(s)]
    if not segs:
        return []
    out = []
    for poly in chain_segments(np.concatenate(segs)):
        poly = simplify(poly, tol)
        if clip:
            out.extend(clip_polyline(poly))
        else:
            out.append(poly)
    return [p for p in out if len(p) >= 2]
