"""
Flat preview of the finished tile: base colour, every geometry layer filled in
render order at full strength, and optionally the lines, neighbour tiles and
the reference image. It ignores the editor's visibility ticks, so it always
shows what the exported .bin contains.

It doubles as a minimap: the main canvas viewport is outlined, click or drag
to move the canvas there, and the wheel zooms the canvas.
"""
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import (RENDER_ORDER, LAYER_COLORS, CHANNEL_COLORS, NUM_CHANNELS,
                              BASE_COLOR, SLOT_OFFSETS, TILE_HALF)

LINE_WIDTH = 4.0     # world units, matches the quad width sw_ducky gives exported paths
MARGIN = 6


class RenderView(QtWidgets.QWidget):

    def __init__(self, doc, state, paths, canvas=None):
        super().__init__()
        self.doc, self.state, self.paths, self.canvas = doc, state, paths, canvas
        self.setMinimumHeight(220)
        self.setMouseTracking(True)
        self.show_lines = True
        self.show_neighbours = True
        self.show_reference = False
        self.show_viewport = True
        self._cache = None            # (key, QPixmap)
        self._dragging = False
        self.hover_text = ''
        doc.changed.connect(self._invalidate)
        state.changed.connect(self._on_state)
        if canvas is not None and hasattr(canvas, 'viewChanged'):
            canvas.viewChanged.connect(self.update)
        self.setToolTip('The finished tile, as it will be exported.\n'
                        'Click or drag to move the editor there; scroll to zoom the editor.')

    def sizeHint(self):
        return QtCore.QSize(300, 340)

    # ------------------------------------------------------------------ options
    def set_option(self, name, value):
        setattr(self, name, value)
        self._invalidate()

    def _on_state(self, what):
        if what == 'refs':
            self._invalidate()
        else:
            self.update()

    def _invalidate(self, *_):
        self._cache = None
        self.update()

    # ------------------------------------------------------------------ geometry
    def _world_extent(self) -> QtCore.QRectF:
        r = QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000)
        if self.show_neighbours:
            for slot in self.state.neighbours:
                ox, oy = SLOT_OFFSETS[slot]
                r = r.united(QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000))
        return r

    def _transform(self) -> QtGui.QTransform:
        ext = self._world_extent()
        w, h = max(1, self.width() - 2 * MARGIN), max(1, self.height() - 2 * MARGIN)
        s = min(w / ext.width(), h / ext.height())
        t = QtGui.QTransform()
        t.translate(self.width() / 2, self.height() / 2)
        t.scale(s, -s)
        t.translate(-ext.center().x(), -ext.center().y())
        return t

    def _to_world(self, pos):
        inv, ok = self._transform().inverted()
        p = inv.map(QtCore.QPointF(pos))
        return p.x(), p.y()

    # ------------------------------------------------------------------ painting
    def _render_key(self):
        st = self.state
        return (self.width(), self.height(), self.devicePixelRatioF(),
                self.show_lines, self.show_neighbours, self.show_reference,
                id(st.background), tuple(sorted((s, id(n)) for s, n in st.neighbours.items())))

    def _build_pixmap(self):
        dpr = self.devicePixelRatioF()
        pm = QtGui.QPixmap(int(self.width() * dpr), int(self.height() * dpr))
        pm.setDevicePixelRatio(dpr)
        pm.fill(self.palette().color(QtGui.QPalette.Base))
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        T = self._transform()
        st = self.state

        def draw_image(ref, ox, oy, opacity=1.0):
            screen = T.mapRect(QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000))
            img = ref.pixmap_for(screen.width() * dpr)
            p.save()
            p.setOpacity(opacity)
            p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
            p.drawPixmap(screen, img, QtCore.QRectF(img.rect()))
            p.restore()

        if self.show_neighbours:
            for slot, nb in st.neighbours.items():
                ox, oy = SLOT_OFFSETS[slot]
                draw_image(nb.image, ox, oy)

        tile = T.mapRect(QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000))
        p.fillRect(tile, QtGui.QColor(*BASE_COLOR))

        p.setTransform(T)
        p.setPen(QtCore.Qt.NoPen)
        for name in RENDER_ORDER:
            if not self.doc.layers[name].polys:
                continue
            color = QtGui.QColor(*LAYER_COLORS[name])
            p.setBrush(color)
            p.drawPath(self.paths.fill(('layer', name)))

        if self.show_lines:
            px = abs(T.m11())
            pen_w = max(1.0, LINE_WIDTH * px)
            p.setBrush(QtCore.Qt.NoBrush)
            for ch in range(NUM_CHANNELS):
                if not self.doc.channels[ch].polys:
                    continue
                pen = QtGui.QPen(QtGui.QColor(CHANNEL_COLORS[ch]), pen_w,
                                 QtCore.Qt.SolidLine, QtCore.Qt.FlatCap, QtCore.Qt.MiterJoin)
                pen.setCosmetic(True)
                p.setPen(pen)
                p.drawPath(self.paths.path(('line', ch)))
        p.setTransform(QtGui.QTransform())

        if self.show_reference and st.background is not None:
            draw_image(st.background, 0, 0, 0.5)

        # tile frames
        if self.show_neighbours and st.neighbours:
            p.setPen(QtGui.QPen(QtGui.QColor(120, 130, 145, 160), 1))
            p.setBrush(QtCore.Qt.NoBrush)
            for slot in st.neighbours:
                ox, oy = SLOT_OFFSETS[slot]
                p.drawRect(T.mapRect(QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000)))
        p.setPen(QtGui.QPen(QtGui.QColor(235, 70, 70, 200), 1))
        p.drawRect(tile)
        p.end()
        return pm

    def paintEvent(self, e):
        key = self._render_key()
        if self._cache is None or self._cache[0] != key:
            self._cache = (key, self._build_pixmap())
        p = QtGui.QPainter(self)
        p.drawPixmap(0, 0, self._cache[1])

        if self.show_viewport and self.canvas is not None:
            vr = self._transform().mapRect(self.canvas.view_world_rect())
            vr = vr.intersected(QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1))
            if not vr.isEmpty():
                p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150), 3))
                p.setBrush(QtCore.Qt.NoBrush)
                p.drawRect(vr)
                p.setPen(QtGui.QPen(QtGui.QColor(255, 220, 90), 1.2))
                p.setBrush(QtGui.QColor(255, 220, 90, 28))
                p.drawRect(vr)

        if self.hover_text:
            fm = p.fontMetrics()
            r = QtCore.QRectF(4, self.height() - fm.height() - 8, fm.horizontalAdvance(self.hover_text) + 12,
                              fm.height() + 4)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(15, 17, 21, 200))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(QtGui.QColor(230, 232, 236))
            p.drawText(r, QtCore.Qt.AlignCenter, self.hover_text)
        p.end()

    # ------------------------------------------------------------------ hover info
    def _describe(self, x, y):
        pt = QtCore.QPointF(x, y)
        if abs(x) > TILE_HALF or abs(y) > TILE_HALF:
            for slot, (ox, oy) in SLOT_OFFSETS.items():
                if slot in self.state.neighbours and abs(x - ox) <= TILE_HALF and abs(y - oy) <= TILE_HALF:
                    return f'{x:.0f}, {y:.0f}  ·  neighbour {slot}'
            return ''
        top = 'Base'
        for name in reversed(RENDER_ORDER):
            if self.doc.layers[name].polys and self.paths.fill(('layer', name)).contains(pt):
                top = name
                break
        return f'{x:.0f}, {y:.0f}  ·  {top}'

    # ------------------------------------------------------------------ input
    def _goto(self, pos):
        if self.canvas is None:
            return
        x, y = self._to_world(pos)
        self.canvas.center = QtCore.QPointF(x, y)
        self.canvas.update()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self._goto(e.position())

    def mouseMoveEvent(self, e):
        if self._dragging:
            self._goto(e.position())
        text = self._describe(*self._to_world(e.position()))
        if text != self.hover_text:
            self.hover_text = text
            self.update()

    def mouseReleaseEvent(self, e):
        self._dragging = False

    def leaveEvent(self, e):
        self.hover_text = ''
        self.update()

    def wheelEvent(self, e):
        if self.canvas is None or not e.angleDelta().y():
            return
        c = self.canvas
        c.zoom = max(0.02, min(500.0, c.zoom * (1.18 if e.angleDelta().y() > 0 else 1 / 1.18)))
        c.update()
