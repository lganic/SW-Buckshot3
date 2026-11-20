"""
The editable tile: 11 geometry layers (vertices + triangles) and 10 line
channels (points + edges), with a single undo / redo history covering both.

Every container is a Graph: id-keyed vertices and id-keyed polygons (3 vertex
ids for a triangle, 2 for a line edge). Containers are addressed by a key:
('layer', 'Land') or ('line', 0).
"""
from contextlib import contextmanager

import numpy as np
from PySide6 import QtCore

from .constants import RENDER_ORDER, NUM_CHANNELS


class Graph:

    def __init__(self, arity: int):
        self.arity = arity
        self.verts: dict[int, tuple[float, float]] = {}
        self.polys: dict[int, tuple[int, ...]] = {}
        self.vert_polys: dict[int, set[int]] = {}
        self.version = 0
        self._next_id = 1
        self._arrays = None   # cached numpy views for hit testing

    def new_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    # Low level setters. value None = remove. Only Document should call these.
    def _set_vert(self, vid, value):
        if value is None:
            self.verts.pop(vid, None)
            self.vert_polys.pop(vid, None)
        else:
            self.verts[vid] = value
            self.vert_polys.setdefault(vid, set())
            self._next_id = max(self._next_id, vid + 1)
        self._touch()

    def _set_poly(self, pid, value):
        old = self.polys.get(pid)
        if old is not None:
            for v in old:
                s = self.vert_polys.get(v)
                if s is not None:
                    s.discard(pid)
        if value is None:
            self.polys.pop(pid, None)
        else:
            self.polys[pid] = value
            for v in value:
                self.vert_polys.setdefault(v, set()).add(pid)
            self._next_id = max(self._next_id, pid + 1)
        self._touch()

    def _touch(self):
        self.version += 1
        self._arrays = None

    def is_empty(self):
        return not self.verts and not self.polys

    def neighbours(self, vid):
        """Vertex ids sharing a polygon with vid."""
        out = set()
        for pid in self.vert_polys.get(vid, ()):
            out.update(self.polys[pid])
        out.discard(vid)
        return out

    def find_poly(self, vids) -> int | None:
        target = frozenset(vids)
        for pid in self.vert_polys.get(next(iter(vids)), ()):
            if frozenset(self.polys[pid]) == target:
                return pid
        return None

    def arrays(self):
        """(vert_ids, vert_xy, poly_ids, poly_xy) numpy arrays, cached until the next edit."""
        if self._arrays is None:
            vids = np.fromiter(self.verts.keys(), np.int64, len(self.verts))
            vxy = np.array(list(self.verts.values()), np.float64).reshape(-1, 2)
            pids = np.fromiter(self.polys.keys(), np.int64, len(self.polys))
            if self.polys:
                index = {v: i for i, v in enumerate(vids.tolist())}
                pidx = np.array([[index[v] for v in p] for p in self.polys.values()], np.int64)
                pxy = vxy[pidx]
            else:
                pxy = np.zeros((0, self.arity, 2))
            self._arrays = (vids, vxy, pids, pxy)
        return self._arrays

    def compact(self):
        """(verts list, polys index list) with contiguous indices."""
        ids = list(self.verts)
        index = {v: i for i, v in enumerate(ids)}
        verts = [self.verts[v] for v in ids]
        polys = [tuple(index[v] for v in p) for p in self.polys.values()
                 if all(v in index for v in p)]
        return verts, polys


class Document(QtCore.QObject):

    changed = QtCore.Signal(object)       # set of container keys that changed
    historyChanged = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.layers = {name: Graph(3) for name in RENDER_ORDER}
        self.channels = [Graph(2) for _ in range(NUM_CHANNELS)]
        self.channel_names = [f'Channel {i + 1}' for i in range(NUM_CHANNELS)]
        self.undo_stack: list = []
        self.redo_stack: list = []
        self._txn = None
        self._txn_depth = 0
        self._txn_label = ''
        self._pending = set()
        self._emit_scheduled = False
        self.saved_index = 0
        self._history_counter = 0

    # ---- addressing ----
    def graph(self, key) -> Graph:
        kind, name = key
        return self.layers[name] if kind == 'layer' else self.channels[name]

    def all_keys(self):
        return [('layer', n) for n in RENDER_ORDER] + [('line', i) for i in range(NUM_CHANNELS)]

    def is_empty(self):
        return all(self.graph(k).is_empty() for k in self.all_keys())

    # ---- change notification (coalesced per event loop pass) ----
    def _notify(self, key):
        self._pending.add(key)
        if not self._emit_scheduled:
            self._emit_scheduled = True
            QtCore.QTimer.singleShot(0, self._flush)

    def _flush(self):
        self._emit_scheduled = False
        keys, self._pending = self._pending, set()
        if keys:
            self.changed.emit(keys)

    # ---- transactions ----
    @contextmanager
    def edit(self, label: str):
        self.begin(label)
        try:
            yield
        except Exception:
            self.cancel()
            raise
        else:
            self.commit()

    def begin(self, label: str):
        if self._txn_depth == 0:
            self._txn = {}
            self._txn_label = label
        self._txn_depth += 1

    def commit(self):
        self._txn_depth -= 1
        if self._txn_depth > 0:
            return
        changes = [(k, old, new) for k, (old, new) in self._txn.items() if old != new]
        self._txn = None
        if changes:
            self._history_counter += 1
            self.undo_stack.append((self._txn_label, changes, self._history_counter))
            self.redo_stack.clear()
            self.historyChanged.emit()

    def cancel(self):
        """Roll back the open transaction."""
        if self._txn is None:
            return
        for (key, kind, i), (old, _new) in reversed(list(self._txn.items())):
            self._apply(key, kind, i, old)
        self._txn = None
        self._txn_depth = 0

    def in_edit(self):
        return self._txn is not None

    def _record(self, key, kind, i, old, new):
        assert self._txn is not None, 'Edits must happen inside Document.edit()'
        k = (key, kind, i)
        if k in self._txn:
            self._txn[k] = (self._txn[k][0], new)
        else:
            self._txn[k] = (old, new)

    def _apply(self, key, kind, i, value):
        g = self.graph(key)
        (g._set_vert if kind == 'v' else g._set_poly)(i, value)
        self._notify(key)

    # ---- primitive edits ----
    def set_vert(self, key, vid, pos):
        g = self.graph(key)
        pos = None if pos is None else (float(pos[0]), float(pos[1]))
        self._record(key, 'v', vid, g.verts.get(vid), pos)
        self._apply(key, 'v', vid, pos)

    def set_poly(self, key, pid, verts):
        g = self.graph(key)
        verts = None if verts is None else tuple(verts)
        self._record(key, 'p', pid, g.polys.get(pid), verts)
        self._apply(key, 'p', pid, verts)

    # ---- helpers ----
    def add_vert(self, key, pos) -> int:
        vid = self.graph(key).new_id()
        self.set_vert(key, vid, pos)
        return vid

    def add_poly(self, key, verts) -> int | None:
        g = self.graph(key)
        if len(set(verts)) != len(verts) or g.find_poly(verts) is not None:
            return None
        pid = g.new_id()
        self.set_poly(key, pid, verts)
        return pid

    def delete(self, key, vids=(), pids=(), remove_orphans=False):
        g = self.graph(key)
        pids = set(pids)
        for v in vids:
            pids |= g.vert_polys.get(v, set())
        touched = set()
        for p in pids:
            if p in g.polys:
                touched.update(g.polys[p])
                self.set_poly(key, p, None)
        for v in vids:
            if v in g.verts:
                self.set_vert(key, v, None)
        if remove_orphans:
            for v in touched:
                if v in g.verts and not g.vert_polys.get(v):
                    self.set_vert(key, v, None)

    def merge_vert(self, key, src, dst):
        """Re-point every polygon using src at dst, then delete src (line welding)."""
        g = self.graph(key)
        for pid in list(g.vert_polys.get(src, ())):
            new = tuple(dst if v == src else v for v in g.polys[pid])
            if len(set(new)) != len(new) or g.find_poly(new) is not None:
                self.set_poly(key, pid, None)
            else:
                self.set_poly(key, pid, new)
        self.set_vert(key, src, None)

    def split_edge(self, key, pid, pos) -> int:
        a, b = self.graph(key).polys[pid]
        m = self.add_vert(key, pos)
        self.set_poly(key, pid, None)
        self.add_poly(key, (a, m))
        self.add_poly(key, (m, b))
        return m

    def add_polyline(self, key, points):
        ids = [self.add_vert(key, p) for p in points]
        closed = len(points) > 2 and tuple(points[0]) == tuple(points[-1])
        if closed:
            self.set_vert(key, ids[-1], None)
            ids[-1] = ids[0]
        for a, b in zip(ids[:-1], ids[1:]):
            self.add_poly(key, (a, b))

    def clear_container(self, key):
        g = self.graph(key)
        self.delete(key, list(g.verts), list(g.polys))

    # ---- undo / redo ----
    def undo(self):
        if self._txn is not None or not self.undo_stack:
            return None
        label, changes, n = self.undo_stack.pop()
        for (key, kind, i), old, _new in reversed(changes):
            self._apply(key, kind, i, old)
        self.redo_stack.append((label, changes, n))
        self.historyChanged.emit()
        return label

    def redo(self):
        if self._txn is not None or not self.redo_stack:
            return None
        label, changes, n = self.redo_stack.pop()
        for (key, kind, i), _old, new in changes:
            self._apply(key, kind, i, new)
        self.undo_stack.append((label, changes, n))
        self.historyChanged.emit()
        return label

    def history_marker(self):
        return self.undo_stack[-1][2] if self.undo_stack else 0

    def mark_saved(self):
        self.saved_index = self.history_marker()
        self.historyChanged.emit()

    def is_dirty(self):
        return self.history_marker() != self.saved_index

    def reset(self, layers=None, channels=None, names=None):
        """Replace everything without recording history (file open / new)."""
        self.cancel()
        self.layers = {name: Graph(3) for name in RENDER_ORDER}
        self.channels = [Graph(2) for _ in range(NUM_CHANNELS)]
        if names:
            self.channel_names = list(names)
        else:
            self.channel_names = [f'Channel {i + 1}' for i in range(NUM_CHANNELS)]
        for name, (verts, tris) in (layers or {}).items():
            _fill(self.layers[name], verts, tris)
        for i, (pts, edges) in enumerate(channels or []):
            _fill(self.channels[i], pts, edges)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.saved_index = 0
        self.historyChanged.emit()
        for k in self.all_keys():
            self._notify(k)


def _fill(g: Graph, verts, polys):
    ids = []
    for p in verts:
        vid = g.new_id()
        g.verts[vid] = (float(p[0]), float(p[1]))
        g.vert_polys[vid] = set()
        ids.append(vid)
    seen = set()
    for poly in polys:
        if len(set(poly)) != len(poly) or max(poly) >= len(ids) or min(poly) < 0:
            continue
        mapped = tuple(ids[i] for i in poly)
        f = frozenset(mapped)
        if f in seen:
            continue
        seen.add(f)
        pid = g.new_id()
        g.polys[pid] = mapped
        for v in mapped:
            g.vert_polys[v].add(pid)
    g._touch()
