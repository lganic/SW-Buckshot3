"""Rasterising tiles and mesh scenes into QImages."""
from PySide6 import QtCore, QtGui

from .constants import RENDER_ORDER, LAYER_COLORS, BASE_COLOR, TILE_HALF, TILE_SIZE


def tile_transform(size: int) -> QtGui.QTransform:
    """Tile coords (-500..500, +Y up) -> image pixels (0..size, +Y down)."""
    s = size / TILE_SIZE
    return QtGui.QTransform(s, 0, 0, -s, TILE_HALF * s, TILE_HALF * s)


# Triangles per drawPath call. One antialiased winding-fill path per layer gets
# very slow as it grows; ~50-triangle paths draw about twice as fast, look the
# same (the hairline outline covers the seams between batches, at most a few
# levels of shading on edge pixels), and give regular points to report progress.
RENDER_BATCH = 50
LINE_COST = 0.05      # progress weight of one line segment, relative to a triangle


def render_tiledata(td, size: int, draw_lines=True, progress=None) -> QtGui.QImage:
    """progress(fraction) is called between batches; it may raise to abort the render."""
    total = sum(len(t) for _, t in td.layers.values() if t) or 1
    if draw_lines:
        total += LINE_COST * sum(len(s) for s in td.segments)
    done = 0.0
    img = QtGui.QImage(size, size, QtGui.QImage.Format_RGB32)
    img.fill(QtGui.QColor(*BASE_COLOR))
    p = QtGui.QPainter(img)
    try:
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setTransform(tile_transform(size))
        for name in RENDER_ORDER:
            verts, tris = td.layers.get(name, ([], []))
            if not tris:
                continue
            color = QtGui.QColor(*LAYER_COLORS[name])
            p.setPen(QtGui.QPen(color, 0))
            p.setBrush(color)
            for start in range(0, len(tris), RENDER_BATCH):
                batch = tris[start:start + RENDER_BATCH]
                path = QtGui.QPainterPath()
                path.setFillRule(QtCore.Qt.WindingFill)
                for i, j, k in batch:
                    try:
                        a, b, c = verts[i], verts[j], verts[k]
                    except IndexError:
                        continue
                    if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0:
                        b, c = c, b          # same winding for all, so overlaps never cancel
                    path.addPolygon(QtGui.QPolygonF([QtCore.QPointF(*a), QtCore.QPointF(*b),
                                                     QtCore.QPointF(*c), QtCore.QPointF(*a)]))
                p.drawPath(path)
                done += len(batch)
                if progress:
                    progress(done / total)
        if draw_lines:
            pen = QtGui.QPen(QtGui.QColor(70, 70, 70), max(1.0, size / 1000))
            pen.setCosmetic(True)
            p.setPen(pen)
            for segs in td.segments:
                for a, b in segs:
                    p.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
                done += LINE_COST * len(segs)
                if progress:
                    progress(done / total)
    finally:
        p.end()
    return img


class SceneRasteriser:
    """
    Incrementally draws a SceneTris into a full resolution image and a small
    preview image, a batch at a time (this is what drives the draw animation).
    """

    def __init__(self, scene, size: int, base_color, preview_size=800):
        self.scene = scene
        self.size = size
        self.image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB32)
        self.image.fill(QtGui.QColor(*base_color))
        self.preview = QtGui.QImage(preview_size, preview_size, QtGui.QImage.Format_RGB32)
        self.preview.fill(QtGui.QColor(*base_color))
        self.index = 0
        self.total = len(scene.pts)
        self._t_full = tile_transform(size)
        self._t_prev = tile_transform(preview_size)
        self.last_batch = (0, 0)

    def done(self):
        return self.index >= self.total

    def step(self, count: int):
        start = self.index
        end = min(self.total, start + max(1, count))
        pts = self.scene.pts[start:end]
        cols = self.scene.colors[start:end]
        for img, tr, aa in ((self.image, self._t_full, False), (self.preview, self._t_prev, True)):
            p = QtGui.QPainter(img)
            p.setRenderHint(QtGui.QPainter.Antialiasing, aa)
            p.setTransform(tr)
            for tri, c in zip(pts.tolist(), cols.tolist()):
                color = QtGui.QColor(c[0], c[1], c[2])
                p.setPen(QtGui.QPen(color, 0))   # hairline outline closes seams, like PIL polygon
                p.setBrush(color)
                p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(*tri[0]), QtCore.QPointF(*tri[1]),
                                               QtCore.QPointF(*tri[2])]))
            p.end()
        self.index = end
        self.last_batch = (start, end)

    def paint_lines(self, polylines, color, width_px):
        """Burn contour polylines into both images (the old magenta / blue overlay)."""
        for img, tr, scale in ((self.image, self._t_full, 1.0),
                               (self.preview, self._t_prev, self.preview.width() / self.size)):
            p = QtGui.QPainter(img)
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            p.setTransform(tr)
            pen = QtGui.QPen(QtGui.QColor(*color), max(1.0, width_px * scale))
            pen.setCosmetic(True)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            p.setPen(pen)
            for poly in polylines:
                p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in poly]))
            # green dot on every point of every line (each segment's start and end),
            # to help line things up
            p.resetTransform()
            r = max(1.5, width_px * scale * 1.5)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(0, 255, 0))
            for poly in polylines:
                for x, y in poly:
                    p.drawEllipse(tr.map(QtCore.QPointF(float(x), float(y))), r, r)
            p.end()
