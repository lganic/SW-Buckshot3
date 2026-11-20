"""QPainterPath caches for layers and line channels (rebuilt only when a graph changes)."""
from PySide6 import QtCore, QtGui


class PathCache:

    def __init__(self, doc):
        self.doc = doc
        self._cache = {}
        self._fills = {}
        self._edges = {}

    def path(self, key) -> QtGui.QPainterPath:
        g = self.doc.graph(key)
        hit = self._cache.get(key)
        if hit is not None and hit[0] is g:
            if hit[1] == g.version:
                return hit[2]
        path = QtGui.QPainterPath()
        V = g.verts
        if g.arity == 3:
            # Every triangle is added counter-clockwise, so overlaps always add up under the
            # winding rule. Mixed windings would cancel and punch holes, but in game
            # overlapping triangles always draw on top of each other.
            path.setFillRule(QtCore.Qt.WindingFill)
            for a, b, c in g.polys.values():
                pa = V.get(a); pb = V.get(b); pc = V.get(c)
                if pa is None or pb is None or pc is None:
                    continue
                if (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0]) < 0:
                    pb, pc = pc, pb
                path.moveTo(*pa)
                path.lineTo(*pb)
                path.lineTo(*pc)
                path.closeSubpath()
        else:
            for a, b in g.polys.values():
                pa = V.get(a); pb = V.get(b)
                if pa is None or pb is None:
                    continue
                path.moveTo(*pa)
                path.lineTo(*pb)
        self._cache[key] = (g, g.version, path)
        return path

    def fill(self, key) -> QtGui.QPainterPath:
        """A layer's triangles merged into one outline, for filling. Qt fills this ~20x faster
        than the raw overlapping triangles when anti-aliasing, and it has no seams between triangles."""
        g = self.doc.graph(key)
        hit = self._fills.get(key)
        if hit is not None and hit[0] is g and hit[1] == g.version:
            return hit[2]
        path = self.path(key).simplified()
        self._fills[key] = (g, g.version, path)
        return path

    def edges(self, key) -> list:
        """Each triangle edge once, as QLineF. Stroking these with drawLines is much faster
        than stroking the triangle path, which draws shared edges twice with joins."""
        g = self.doc.graph(key)
        hit = self._edges.get(key)
        if hit is not None and hit[0] is g and hit[1] == g.version:
            return hit[2]
        seen = set()
        V = g.verts
        lines = []
        for poly in g.polys.values():
            n = len(poly)
            for i in range(n if n > 2 else 1):
                a, b = poly[i], poly[(i + 1) % n]
                e = (a, b) if a < b else (b, a)
                if e in seen or a not in V or b not in V:
                    continue
                seen.add(e)
                lines.append(QtCore.QLineF(*V[a], *V[b]))
        self._edges[key] = (g, g.version, lines)
        return lines
