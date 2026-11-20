"""
Exploded view of the tile: every geometry layer drawn as its own tilted sheet,
stacked in render order (bottom of the list is drawn first), with the line
channels as a final sheet on top. Click a sheet to make it active.
"""
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import RENDER_ORDER, LAYER_COLORS, CHANNEL_COLORS, NUM_CHANNELS, BASE_COLOR

SHEAR = 0.55     # how far the back edge leans right
DEPTH = 0.30     # sheet depth relative to width
LABEL_W = 74


class StackView(QtWidgets.QWidget):

    def __init__(self, doc, state, paths):
        super().__init__()
        self.doc, self.state, self.paths = doc, state, paths
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        self.hover = None
        self.sheets = list(RENDER_ORDER) + ['Lines']
        doc.changed.connect(lambda _k: self.update())
        state.changed.connect(lambda _w: self.update())
        self.setToolTip('Exploded layer stack - bottom sheet is drawn first.\nClick a sheet to edit it.')

    def sizeHint(self):
        return QtCore.QSize(300, 340)

    def _geometry(self):
        W, H = self.width(), self.height()
        a = (W - LABEL_W - 12) / (1000 * (1 + SHEAR))
        depth = 1000 * DEPTH * a
        n = len(self.sheets)
        gap = max(8.0, (H - depth - 18) / max(1, n - 1))
        return a, depth, gap

    def _sheet_transform(self, i):
        a, depth, gap = self._geometry()
        front = self.height() - 8 - i * gap          # y of the sheet's front (south) edge
        x0 = LABEL_W
        # sx = x0 + (x + 500) a + (y + 500) SHEAR a ;  sy = front - (y + 500) DEPTH a
        return QtGui.QTransform(a, 0, SHEAR * a, -DEPTH * a,
                                x0 + 500 * a + 500 * SHEAR * a, front - 500 * DEPTH * a)

    def _sheet_poly(self, i):
        T = self._sheet_transform(i)
        return T.map(QtGui.QPolygonF([QtCore.QPointF(-500, -500), QtCore.QPointF(500, -500),
                                      QtCore.QPointF(500, 500), QtCore.QPointF(-500, 500)]))

    def _label_rect(self, i):
        a, depth, gap = self._geometry()
        front = self.height() - 8 - i * gap
        return QtCore.QRectF(2, front - depth / 2 - 9, LABEL_W - 6, 18)

    def _is_active(self, name):
        st = self.state
        if name == 'Lines':
            return st.mode == 'lines'
        return st.mode == 'geometry' and st.active_layer == name

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(self.rect(), self.palette().color(QtGui.QPalette.Base))
        st = self.state
        font = p.font()

        for i, name in enumerate(self.sheets):
            poly = self._sheet_poly(i)
            active = self._is_active(name)
            hovered = self.hover == i
            if name == 'Lines':
                visible = any(st.channel_visible)
                empty = all(not c.polys for c in self.doc.channels)
                color = QtGui.QColor(200, 200, 210)
            else:
                visible = st.layer_visible[name]
                empty = not self.doc.layers[name].polys
                color = QtGui.QColor(*LAYER_COLORS[name])

            # the sheet itself
            p.setPen(QtCore.Qt.NoPen)
            base = QtGui.QColor(*BASE_COLOR) if i == 0 else QtGui.QColor(30, 34, 40)
            base.setAlpha(235 if i == 0 else (150 if active else 70))
            p.setBrush(base)
            p.drawPolygon(poly)

            p.save()
            p.setTransform(self._sheet_transform(i))
            p.setOpacity(1.0 if visible else 0.25)
            if name == 'Lines':
                for ch in range(NUM_CHANNELS):
                    if not st.channel_visible[ch] or not self.doc.channels[ch].polys:
                        continue
                    pen = QtGui.QPen(QtGui.QColor(CHANNEL_COLORS[ch]), 1.2)
                    pen.setCosmetic(True)
                    p.setPen(pen)
                    p.setBrush(QtCore.Qt.NoBrush)
                    p.drawPath(self.paths.path(('line', ch)))
            elif not empty:
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(color)
                p.drawPath(self.paths.fill(('layer', name)))
            p.restore()

            # outline
            if active:
                pen = QtGui.QPen(QtGui.QColor(255, 220, 90), 2)
            elif hovered:
                pen = QtGui.QPen(QtGui.QColor(200, 210, 230), 1.5)
            else:
                pen = QtGui.QPen(QtGui.QColor(110, 118, 130, 160), 1, QtCore.Qt.DashLine if empty else QtCore.Qt.SolidLine)
            p.setPen(pen)
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawPolygon(poly)

            # label + leader
            lr = self._label_rect(i)
            f = QtGui.QFont(font)
            f.setBold(active)
            f.setStrikeOut(not visible)
            p.setFont(f)
            txt = self.palette().color(QtGui.QPalette.Text)
            if empty and not active:
                txt.setAlpha(110)
            p.setPen(txt)
            p.drawText(lr.adjusted(14, 0, 0, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, name)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(QtCore.QRectF(lr.left() + 1, lr.center().y() - 5, 10, 10), 2, 2)
            p.setPen(QtGui.QPen(QtGui.QColor(120, 128, 140, 120), 1, QtCore.Qt.DotLine))
            p.drawLine(QtCore.QPointF(lr.right() - 2, lr.center().y()), poly[0] * 0.5 + poly[3] * 0.5)
        p.end()

    def _hit(self, pos):
        for i in reversed(range(len(self.sheets))):
            if self._label_rect(i).contains(pos):
                return i
        for i in reversed(range(len(self.sheets))):
            if self._sheet_poly(i).containsPoint(pos, QtCore.Qt.OddEvenFill):
                return i
        return None

    def mouseMoveEvent(self, e):
        h = self._hit(e.position())
        if h != self.hover:
            self.hover = h
            self.update()

    def leaveEvent(self, e):
        self.hover = None
        self.update()

    def mousePressEvent(self, e):
        i = self._hit(e.position())
        if i is None:
            return
        name = self.sheets[i]
        if name == 'Lines':
            self.state.set_mode('lines')
        else:
            self.state.set_active_layer(name)
