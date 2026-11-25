"""
The editor canvas. One widget handles both modes:

  Geometry mode  - select / move vertices and triangles, add vertices, build triangles.
  Lines mode     - draw connected lines point to point, move points, split edges, weld points.

Tile coordinates are +Y up; the neighbour tiles sit at +-1000 m around the centre tile.
Navigation: wheel or held Up / Down = zoom, middle / right drag (or Space + left drag) = pan.
"""
import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import (RENDER_ORDER, LAYER_COLORS, BASE_COLOR, NUM_CHANNELS,
                              CHANNEL_COLORS, SLOT_OFFSETS, TILE_HALF)

PICK_PX = 9
TRI_PICK_PX = 22     # triangle tool: how close (screen px) a click must be to grab a vertex
SNAP_PX = 9
DRAG_START_PX = 3


def _clamp_tile(x, y):
    return (min(TILE_HALF, max(-TILE_HALF, x)), min(TILE_HALF, max(-TILE_HALF, y)))


class Canvas(QtWidgets.QWidget):

    cursorMoved = QtCore.Signal(float, float, str)   # world x, y, snap description
    hint = QtCore.Signal(str)
    selectionChanged = QtCore.Signal(int)
    viewChanged = QtCore.Signal()

    def __init__(self, doc, state, paths):
        super().__init__()
        self.doc = doc
        self.state = state
        self.paths = paths
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMinimumSize(400, 300)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, True)

        self.zoom = 0.8
        self.center = QtCore.QPointF(0, 0)
        self._fitted = False
        self._last_view = None

        self.selection: set = set()      # ('v', id) / ('p', id) inside the active container
        self.tri_pick: list = []         # vertex ids picked by the triangle tool
        self.chain = None                # line draw tool: ('id', vid) | ('pos', (x, y))
        self.drag = None
        self.pan = None
        self.space_down = False
        self.mouse_screen = QtCore.QPointF()
        self.mouse_world = (0.0, 0.0)
        self.snapped = None              # (x, y, kind) of the current snapped cursor

        # WASD panning / Up-Down zooming: held keys move the view at a steady on-screen speed
        self.pan_keys = set()
        self._pan_timer = QtCore.QTimer(self)
        self._pan_timer.setInterval(16)
        self._pan_timer.timeout.connect(self._pan_tick)
        self._pan_clock = QtCore.QElapsedTimer()

        doc.changed.connect(self._on_doc_changed)
        state.changed.connect(self._on_state_changed)

    # ------------------------------------------------------------------ transforms
    def transform(self) -> QtGui.QTransform:
        t = QtGui.QTransform()
        t.translate(self.width() / 2, self.height() / 2)
        t.scale(self.zoom, -self.zoom)
        t.translate(-self.center.x(), -self.center.y())
        return t

    def to_world(self, sp) -> tuple:
        return ((sp.x() - self.width() / 2) / self.zoom + self.center.x(),
                -(sp.y() - self.height() / 2) / self.zoom + self.center.y())

    def to_screen(self, x, y) -> QtCore.QPointF:
        return QtCore.QPointF((x - self.center.x()) * self.zoom + self.width() / 2,
                              -(y - self.center.y()) * self.zoom + self.height() / 2)

    def view_world_rect(self) -> QtCore.QRectF:
        x0, y1 = self.to_world(QtCore.QPointF(0, 0))
        x1, y0 = self.to_world(QtCore.QPointF(self.width(), self.height()))
        return QtCore.QRectF(x0, y0, x1 - x0, y1 - y0)

    def fit_rect(self, r: QtCore.QRectF, margin=30):
        w, h = max(1, self.width() - 2 * margin), max(1, self.height() - 2 * margin)
        self.zoom = min(w / r.width(), h / r.height())
        self.center = r.center()
        self.update()

    def fit_tile(self):
        self.fit_rect(QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000))

    def fit_all(self):
        r = QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000)
        for slot in self.state.neighbours:
            ox, oy = SLOT_OFFSETS[slot]
            r = r.united(QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000))
        self.fit_rect(r)

    # ------------------------------------------------------------------ keyboard panning / zooming
    PAN_SPEED = 900.0      # screen px per second (Shift = 3x)
    PAN_DIRS = {QtCore.Qt.Key_W: (0, 1), QtCore.Qt.Key_S: (0, -1),
                QtCore.Qt.Key_A: (-1, 0), QtCore.Qt.Key_D: (1, 0)}
    ZOOM_SPEED = 2.0       # zoom doublings per second (Shift = 3x)
    ZOOM_DIRS = {QtCore.Qt.Key_Up: 1, QtCore.Qt.Key_Down: -1}

    def zoom_at(self, factor, screen_pos=None):
        """Multiply the zoom by factor, keeping the world point under screen_pos fixed."""
        if screen_pos is None:
            screen_pos = QtCore.QPointF(self.width() / 2, self.height() / 2)
        before = self.to_world(screen_pos)
        self.zoom = max(0.02, min(500.0, self.zoom * factor))
        after = self.to_world(screen_pos)
        self.center += QtCore.QPointF(before[0] - after[0], before[1] - after[1])

    def set_pan_key(self, key, down):
        if down:
            self.pan_keys.add(key)
            if not self._pan_timer.isActive():
                self._pan_clock.start()
                self._pan_timer.start()
        else:
            self.pan_keys.discard(key)
            if not self.pan_keys:
                self._pan_timer.stop()

    def clear_pan_keys(self):
        self.pan_keys.clear()
        self._pan_timer.stop()

    def _pan_tick(self):
        dt = min(0.1, self._pan_clock.restart() / 1000.0)
        dx = sum(self.PAN_DIRS[k][0] for k in self.pan_keys if k in self.PAN_DIRS)
        dy = sum(self.PAN_DIRS[k][1] for k in self.pan_keys if k in self.PAN_DIRS)
        dz = sum(self.ZOOM_DIRS[k] for k in self.pan_keys if k in self.ZOOM_DIRS)
        if not dx and not dy and not dz:
            return
        fast = 3 if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier else 1
        if dz:
            # zoom about the cursor when it is over the canvas, otherwise about the view centre
            self.zoom_at(2 ** (dz * self.ZOOM_SPEED * fast * dt),
                         self.mouse_screen if self.underMouse() else None)
        if dx or dy:
            n = (dx * dx + dy * dy) ** 0.5
            step = self.PAN_SPEED * fast * dt / self.zoom
            self.center += QtCore.QPointF(dx / n * step, dy / n * step)
        if self.underMouse():
            # the world slides under a still cursor: refresh snapping, drags and tool previews
            self.mouseMoveEvent(QtGui.QMouseEvent(
                QtCore.QEvent.MouseMove, self.mouse_screen, self.mapToGlobal(self.mouse_screen),
                QtCore.Qt.NoButton, QtWidgets.QApplication.mouseButtons(),
                QtWidgets.QApplication.keyboardModifiers()))
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        if not self._fitted:
            self._fitted = True
            QtCore.QTimer.singleShot(0, self.fit_tile)

    # ------------------------------------------------------------------ change hooks
    def _on_doc_changed(self, keys):
        g = self.doc.graph(self.state.active_key())
        before = len(self.selection)
        self.selection = {s for s in self.selection
                          if (s[1] in g.verts if s[0] == 'v' else s[1] in g.polys)}
        self.tri_pick = [v for v in self.tri_pick if v in g.verts]
        if self.chain and self.chain[0] == 'id' and self.chain[1] not in g.verts:
            self.chain = None
        if len(self.selection) != before:
            self.selectionChanged.emit(len(self.selection))
        self.update()

    def _on_state_changed(self, what):
        if what in ('mode', 'active', 'tool'):
            self.reset_interaction(keep_selection=(what == 'tool'))
            self._update_cursor()
        self.update()

    def reset_interaction(self, keep_selection=False):
        if self.drag and self.drag.get('started'):
            self.doc.cancel()
        self.drag = None
        self.tri_pick = []
        self.chain = None
        if not keep_selection:
            self.set_selection(set())

    def set_selection(self, sel):
        self.selection = set(sel)
        self.selectionChanged.emit(len(self.selection))
        self.update()

    def _update_cursor(self):
        tool = self.state.tool
        if self.space_down or self.pan:
            self.setCursor(QtCore.Qt.ClosedHandCursor if self.pan else QtCore.Qt.OpenHandCursor)
        elif tool == 'select':
            self.setCursor(QtCore.Qt.ArrowCursor)
        else:
            self.setCursor(QtCore.Qt.CrossCursor)

    # ------------------------------------------------------------------ hit testing
    def hit_vert(self, key, sp, exclude=(), radius=PICK_PX):
        vids, vxy, _, _ = self.doc.graph(key).arrays()
        if not len(vids):
            return None
        wx, wy = self.to_world(sp)
        d = np.hypot(vxy[:, 0] - wx, vxy[:, 1] - wy) * self.zoom
        if exclude:
            d[np.isin(vids, list(exclude))] = np.inf
        i = int(np.argmin(d))
        return int(vids[i]) if d[i] <= radius else None

    def hit_poly(self, key, sp):
        g = self.doc.graph(key)
        _, _, pids, pxy = g.arrays()
        if not len(pids):
            return None, None
        wx, wy = self.to_world(sp)
        if g.arity == 3:
            a, b, c = pxy[:, 0], pxy[:, 1], pxy[:, 2]

            def side(p, q):
                return (q[:, 0] - p[:, 0]) * (wy - p[:, 1]) - (q[:, 1] - p[:, 1]) * (wx - p[:, 0])
            s1, s2, s3 = side(a, b), side(b, c), side(c, a)
            inside = ((s1 >= 0) & (s2 >= 0) & (s3 >= 0)) | ((s1 <= 0) & (s2 <= 0) & (s3 <= 0))
            idx = np.nonzero(inside)[0]
            return (int(pids[idx[-1]]), None) if len(idx) else (None, None)
        a, b = pxy[:, 0], pxy[:, 1]
        d = b - a
        L2 = (d ** 2).sum(axis=1)
        t = np.clip(((wx - a[:, 0]) * d[:, 0] + (wy - a[:, 1]) * d[:, 1]) / np.where(L2 == 0, 1, L2), 0, 1)
        px, py = a[:, 0] + t * d[:, 0], a[:, 1] + t * d[:, 1]
        dist = np.hypot(px - wx, py - wy) * self.zoom
        i = int(np.argmin(dist))
        if dist[i] <= PICK_PX - 2:
            return int(pids[i]), (float(px[i]), float(py[i]))
        return None, None

    # ------------------------------------------------------------------ snapping
    def snap_targets(self, exclude_key=None, exclude_ids=()):
        """Yield (N, 2) arrays of points the cursor can snap to."""
        st = self.state
        for name in RENDER_ORDER:
            if not st.layer_visible[name]:
                continue
            if st.mode == 'lines' and not st.show_geometry_in_lines:
                continue
            key = ('layer', name)
            vids, vxy, _, _ = self.doc.graph(key).arrays()
            if key == exclude_key and exclude_ids:
                vxy = vxy[~np.isin(vids, list(exclude_ids))]
            yield vxy
        for ch in range(NUM_CHANNELS):
            if not st.channel_visible[ch]:
                continue
            key = ('line', ch)
            vids, vxy, _, _ = self.doc.graph(key).arrays()
            if key == exclude_key and exclude_ids:
                vxy = vxy[~np.isin(vids, list(exclude_ids))]
            yield vxy
        for nb in st.neighbours.values():
            if nb.edge_points is not None:
                yield nb.edge_points

    def snap(self, sp, modifiers=None, exclude_key=None, exclude_ids=()):
        """Snap a screen point: existing points first, then grid. Hold Alt to disable."""
        wx, wy = self.to_world(sp)
        mods = modifiers if modifiers is not None else QtWidgets.QApplication.keyboardModifiers()
        if mods & QtCore.Qt.AltModifier:
            x, y = _clamp_tile(wx, wy)
            return x, y, 'free'
        best, bd = None, SNAP_PX / self.zoom
        for arr in self.snap_targets(exclude_key, exclude_ids):
            if not len(arr):
                continue
            d = np.hypot(arr[:, 0] - wx, arr[:, 1] - wy)
            i = int(np.argmin(d))
            if d[i] <= bd:
                bd, best = d[i], arr[i]
        if best is not None:
            x, y = _clamp_tile(float(best[0]), float(best[1]))
            return x, y, 'point'
        s = self.state.snap
        if s:
            wx, wy = round(wx / s) * s, round(wy / s) * s
        x, y = _clamp_tile(wx, wy)
        return x, y, 'grid' if s else 'free'

    # ------------------------------------------------------------------ painting
    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pal = self.palette()
        p.fillRect(self.rect(), QtGui.QColor(24, 27, 32))
        st = self.state
        T = self.transform()

        # neighbours + reference image
        for slot, nb in st.neighbours.items():
            ox, oy = SLOT_OFFSETS[slot]
            self._draw_image(p, nb.image, ox, oy, st.neighbour_opacity)
            self._draw_tile_frame(p, ox, oy, QtGui.QColor(120, 130, 145), slot)

        tile_rect = T.mapRect(QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000))
        p.fillRect(tile_rect, QtGui.QColor(*BASE_COLOR))
        if st.background is not None:
            self._draw_image(p, st.background, 0, 0, st.background_opacity)

        # geometry layers
        geo_mode = st.mode == 'geometry'
        p.setTransform(T)
        for name in RENDER_ORDER:
            if not st.layer_visible[name]:
                continue
            if not geo_mode and not st.show_geometry_in_lines:
                continue
            g = self.doc.layers[name]
            if not g.polys:
                continue
            active = geo_mode and name == st.active_layer
            color = QtGui.QColor(*LAYER_COLORS[name])
            alpha = st.fill_opacity * (1.0 if (active or not geo_mode) else st.inactive_opacity)
            p.setOpacity(alpha)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(color)
            p.drawPath(self.paths.fill(('layer', name)))
            if active:
                p.setOpacity(1.0)
                pen = QtGui.QPen(color.darker(170), 1.4)
                pen.setCosmetic(True)
                p.setPen(pen)
                p.drawLines(self.paths.edges(('layer', name)))
        p.setOpacity(1.0)

        self._draw_grid(p)
        p.setTransform(QtGui.QTransform())
        self._draw_tile_frame(p, 0, 0, QtGui.QColor(235, 70, 70), None, dashed=True)

        # neighbour edge snap markers
        if st.neighbours:
            p.setPen(QtGui.QPen(QtGui.QColor(255, 210, 90), 1))
            p.setBrush(QtGui.QColor(255, 210, 90, 120))
            for nb in st.neighbours.values():
                if nb.edge_points is None or not len(nb.edge_points):
                    continue
                for x, y in nb.edge_points.tolist():
                    s = self.to_screen(x, y)
                    p.drawPolygon(QtGui.QPolygonF([s + QtCore.QPointF(0, -5), s + QtCore.QPointF(5, 0),
                                                   s + QtCore.QPointF(0, 5), s + QtCore.QPointF(-5, 0)]))

        # line channels
        if not geo_mode or st.show_lines_in_geometry:
            p.setTransform(T)
            order = [c for c in range(NUM_CHANNELS) if c != st.active_channel] + [st.active_channel]
            for ch in order:
                if not st.channel_visible[ch] or not self.doc.channels[ch].polys:
                    continue
                active = (not geo_mode) and ch == st.active_channel
                color = QtGui.QColor(CHANNEL_COLORS[ch])
                path = self.paths.path(('line', ch))
                if active:
                    halo = QtGui.QPen(QtGui.QColor(10, 12, 16, 200), 5)
                    halo.setCosmetic(True)
                    p.setPen(halo)
                    p.drawPath(path)
                pen = QtGui.QPen(color, 2.4 if active else 1.3)
                pen.setCosmetic(True)
                if geo_mode:
                    p.setOpacity(0.55)
                elif not active:
                    p.setOpacity(0.6)
                    pen.setStyle(QtCore.Qt.DashLine)
                p.setPen(pen)
                p.setBrush(QtCore.Qt.NoBrush)
                p.drawPath(path)
                p.setOpacity(1.0)
            p.setTransform(QtGui.QTransform())
            self._draw_line_points(p, geo_mode)

        self._draw_selection_and_handles(p)
        self._draw_tool_overlay(p)
        self._draw_hud(p)
        p.end()
        view = (self.center.x(), self.center.y(), self.zoom, self.width(), self.height())
        if view != self._last_view:
            self._last_view = view
            self.viewChanged.emit()

    def _draw_image(self, p, ref, ox, oy, opacity):
        T = self.transform()
        world = QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000)
        screen = T.mapRect(world)
        vis = screen.intersected(QtCore.QRectF(self.rect()))
        if vis.isEmpty():
            return
        pm = ref.pixmap_for(screen.width())
        sx = pm.width() / screen.width()
        sy = pm.height() / screen.height()
        src = QtCore.QRectF((vis.x() - screen.x()) * sx, (vis.y() - screen.y()) * sy,
                            vis.width() * sx, vis.height() * sy)
        p.save()
        p.setOpacity(opacity)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, sx > 1)
        p.drawPixmap(vis, pm, src)
        p.restore()

    def _draw_tile_frame(self, p, ox, oy, color, label, dashed=False):
        r = self.transform().mapRect(QtCore.QRectF(ox - TILE_HALF, oy - TILE_HALF, 1000, 1000))
        pen = QtGui.QPen(color, 1.5, QtCore.Qt.DashLine if dashed else QtCore.Qt.SolidLine)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRect(r)
        if label:
            p.setPen(color)
            p.drawText(r.adjusted(6, 4, -6, -4), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, label)

    def _draw_grid(self, p):
        s = self.state.snap
        if not self.state.show_grid or not s:
            return
        step = s
        while step * self.zoom < 8:
            step *= 10 if step * 10 * self.zoom < 8 else 5
            if step > 1000:
                return
        r = self.view_world_rect().intersected(QtCore.QRectF(-TILE_HALF, -TILE_HALF, 1000, 1000))
        if r.isEmpty():
            return
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 28), 1)
        pen.setCosmetic(True)
        p.setPen(pen)
        x = math.ceil(r.left() / step) * step
        lines = []
        while x <= r.right():
            lines.append(QtCore.QLineF(x, r.top(), x, r.bottom()))
            x += step
        y = math.ceil(r.top() / step) * step
        while y <= r.bottom():
            lines.append(QtCore.QLineF(r.left(), y, r.right(), y))
            y += step
        if len(lines) < 4000:
            p.drawLines(lines)

    def _screen_points(self, xy):
        if not len(xy):
            return []
        sx = (xy[:, 0] - self.center.x()) * self.zoom + self.width() / 2
        sy = -(xy[:, 1] - self.center.y()) * self.zoom + self.height() / 2
        m = (sx > -10) & (sx < self.width() + 10) & (sy > -10) & (sy < self.height() + 10)
        return [QtCore.QPointF(a, b) for a, b in zip(sx[m].tolist(), sy[m].tolist())]

    def _dot_sprite(self, color, size, outline, border):
        """A pre-rendered round handle; stamping pixmaps is far faster than wide round-capped pens."""
        dpr = self.devicePixelRatioF()
        key = (color.rgba(), outline.rgba(), size, border, dpr)
        cache = self.__dict__.setdefault('_sprites', {})
        pm = cache.get(key)
        if pm is None:
            d = size + 2 * border
            px = int(d * dpr + 3)
            pm = QtGui.QPixmap(px, px)
            pm.setDevicePixelRatio(dpr)
            pm.fill(QtCore.Qt.transparent)
            sp = QtGui.QPainter(pm)
            sp.setRenderHint(QtGui.QPainter.Antialiasing)
            c = QtCore.QPointF(px / dpr / 2, px / dpr / 2)
            sp.setPen(QtCore.Qt.NoPen)
            sp.setBrush(outline)
            sp.drawEllipse(c, d / 2, d / 2)
            sp.setBrush(color)
            sp.drawEllipse(c, size / 2, size / 2)
            sp.end()
            cache[key] = pm
        return pm

    def _draw_points(self, p, pts, color, size, outline=QtGui.QColor(10, 12, 16), border=1.25):
        if not pts:
            return
        pm = self._dot_sprite(color, size, outline, border)
        h = pm.width() / pm.devicePixelRatio() / 2
        off = QtCore.QPointF(h, h)
        draw = p.drawPixmap
        for pt in pts:
            draw(pt - off, pm)

    def _draw_line_points(self, p, geo_mode):
        """White dots on every line point, so lines are easy to line up with triangle vertices."""
        st = self.state
        pts = []
        for ch in range(NUM_CHANNELS):
            g = self.doc.channels[ch]
            if not st.channel_visible[ch] or not g.polys:
                continue
            if not geo_mode and ch == st.active_channel:
                continue            # the active channel gets its own editing handles
            _, vxy, _, _ = g.arrays()
            if len(vxy) > 40000 and self.zoom < 2:
                continue
            pts += self._screen_points(vxy)
        if not pts or self.zoom < 0.15:
            return
        self._draw_points(p, pts, QtGui.QColor(255, 255, 255), 4.5, QtGui.QColor(0, 0, 0, 200), 1.5)

    def _draw_selection_and_handles(self, p):
        st = self.state
        key = st.active_key()
        g = self.doc.graph(key)
        T = self.transform()

        # selected polygons
        sel_polys = [g.polys[i] for k, i in self.selection if k == 'p' and i in g.polys]
        if sel_polys:
            p.setTransform(T)
            pen = QtGui.QPen(QtGui.QColor(255, 230, 80), 3)
            pen.setCosmetic(True)
            p.setPen(pen)
            p.setBrush(QtGui.QColor(255, 230, 80, 60) if g.arity == 3 else QtCore.Qt.NoBrush)
            for poly in sel_polys:
                pts = [QtCore.QPointF(*g.verts[v]) for v in poly if v in g.verts]
                if g.arity == 3:
                    p.drawPolygon(QtGui.QPolygonF(pts))
                elif len(pts) == 2:
                    p.drawLine(pts[0], pts[1])
            p.setTransform(QtGui.QTransform())

        vids, vxy, _, _ = g.arrays()
        if len(vids) == 0:
            return
        if len(vids) > 40000 and self.zoom < 2:
            return
        if key[0] == 'layer':
            color = QtGui.QColor(*LAYER_COLORS[key[1]]).lighter(115)
            self._draw_points(p, self._screen_points(vxy), color, 6.5, QtGui.QColor(0, 0, 0), 2.0)
        else:
            color = QtGui.QColor(CHANNEL_COLORS[key[1]])
            deg = np.array([len(g.vert_polys.get(int(v), ())) for v in vids])
            self._draw_points(p, self._screen_points(vxy[deg == 2]), color, 5)
            self._draw_points(p, self._screen_points(vxy[deg != 2]), color, 8.5)

        sel_v = [i for k, i in self.selection if k == 'v' and i in g.verts]
        if sel_v:
            self._draw_points(p, [self.to_screen(*g.verts[v]) for v in sel_v],
                              QtGui.QColor(255, 230, 80), 9)
        if self.tri_pick:
            self._draw_points(p, [self.to_screen(*g.verts[v]) for v in self.tri_pick],
                              QtGui.QColor(255, 140, 40), 10)

    def _draw_tool_overlay(self, p):
        st = self.state
        g = self.doc.graph(st.active_key())
        if self.drag and self.drag['kind'] == 'box' and self.drag.get('started'):
            r = QtCore.QRectF(self.drag['start'], self.mouse_screen).normalized()
            p.setPen(QtGui.QPen(QtGui.QColor(112, 201, 255), 1.5, QtCore.Qt.DashLine))
            p.setBrush(QtGui.QColor(112, 201, 255, 30))
            p.drawRect(r)

        if self.snapped is None or self.pan or st.tool == 'select':
            return
        x, y, kind = self.snapped
        cur = self.to_screen(x, y)
        helper = QtGui.QPen(QtGui.QColor(255, 255, 255, 190), 1.6, QtCore.Qt.DashLine)

        if st.tool == 'triangle' and self.tri_pick:
            pts = [self.to_screen(*g.verts[v]) for v in self.tri_pick] + [cur]
            p.setPen(helper)
            p.setBrush(QtGui.QColor(255, 255, 255, 30))
            if len(pts) == 2:
                p.drawLine(pts[0], pts[1])
            else:
                p.drawPolygon(QtGui.QPolygonF(pts))
        if st.tool == 'draw' and self.chain is not None:
            start = g.verts.get(self.chain[1]) if self.chain[0] == 'id' else self.chain[1]
            if start is not None:
                p.setPen(QtGui.QPen(QtGui.QColor(CHANNEL_COLORS[st.active_channel]), 2, QtCore.Qt.DashLine))
                p.drawLine(self.to_screen(*start), cur)
                if self.chain[0] == 'pos':
                    self._draw_points(p, [self.to_screen(*start)], QtGui.QColor(CHANNEL_COLORS[st.active_channel]), 8)

        # cursor marker
        p.setBrush(QtCore.Qt.NoBrush)
        if kind == 'point':
            p.setPen(QtGui.QPen(QtGui.QColor(255, 210, 90), 2))
            p.drawEllipse(cur, 8, 8)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 220), 1))
        p.drawLine(cur + QtCore.QPointF(-6, 0), cur + QtCore.QPointF(6, 0))
        p.drawLine(cur + QtCore.QPointF(0, -6), cur + QtCore.QPointF(0, 6))

    def _draw_hud(self, p):
        st = self.state
        if st.mode == 'geometry':
            text = f'GEOMETRY  ·  {st.active_layer}  ·  {st.tool}'
            color = QtGui.QColor(*LAYER_COLORS[st.active_layer])
        else:
            text = f'LINES  ·  {self.doc.channel_names[st.active_channel]}  ·  {st.tool}'
            color = QtGui.QColor(CHANNEL_COLORS[st.active_channel])
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        fm = QtGui.QFontMetrics(f)
        r = QtCore.QRectF(10, 10, fm.horizontalAdvance(text) + 30, fm.height() + 10)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(15, 17, 21, 210))
        p.drawRoundedRect(r, 6, 6)
        p.setBrush(color)
        p.drawEllipse(QtCore.QPointF(r.left() + 12, r.center().y()), 5, 5)
        p.setPen(QtGui.QColor(230, 232, 236))
        p.drawText(r.adjusted(22, 0, 0, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, text)

    # ------------------------------------------------------------------ input
    def wheelEvent(self, e):
        dy = e.angleDelta().y()
        if not dy:
            return
        self.zoom_at(1.18 if dy > 0 else 1 / 1.18, e.position())
        self.update()

    def keyPressEvent(self, e):
        k = e.key()
        if k == QtCore.Qt.Key_Space and not e.isAutoRepeat():
            self.space_down = True
            self._update_cursor()
        elif k in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.delete_selected()
        elif k == QtCore.Qt.Key_Escape:
            if self.drag or self.tri_pick or self.chain:
                self.reset_interaction(keep_selection=True)
            else:
                self.set_selection(set())
            self.update()
        elif k in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.chain = None
            self.update()
        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Space and not e.isAutoRepeat():
            self.space_down = False
            self._update_cursor()
        super().keyReleaseEvent(e)

    def mousePressEvent(self, e):
        self.setFocus()
        pos = e.position()
        self.mouse_screen = pos
        btn = e.button()
        if btn in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton) or (btn == QtCore.Qt.LeftButton and self.space_down):
            self.pan = {'last': pos, 'start': pos, 'button': btn, 'moved': False}
            self._update_cursor()
            return
        if btn != QtCore.Qt.LeftButton:
            return
        tool = self.state.tool
        if tool == 'select':
            self._press_select(e)
        elif tool == 'vertex':
            self._press_add_vertex(e)
        elif tool == 'triangle':
            self._press_triangle(e)
        elif tool == 'draw':
            self._press_draw(e)
        self.update()

    def mouseMoveEvent(self, e):
        pos = e.position()
        self.mouse_screen = pos
        self.mouse_world = self.to_world(pos)
        if self.pan:
            d = pos - self.pan['last']
            if (pos - self.pan['start']).manhattanLength() > DRAG_START_PX:
                self.pan['moved'] = True
            self.pan['last'] = pos
            self.center -= QtCore.QPointF(d.x() / self.zoom, -d.y() / self.zoom)
            self.update()
            return
        if self.drag:
            self._move_drag(e)
        if self.state.tool == 'triangle' and not self.drag:
            # the triangle tool only ever picks existing vertices, so the cursor marker shows
            # exactly which one a click would take
            self.snapped = self._triangle_target(pos)
        elif self.state.tool != 'select' or self.drag:
            exclude = self.drag.get('ids', ()) if self.drag else ()
            self.snapped = self.snap(pos, e.modifiers(), self.state.active_key(), exclude)
        else:
            self.snapped = None
        x, y = self.snapped[:2] if self.snapped else self.mouse_world
        self.cursorMoved.emit(x, y, self.snapped[2] if self.snapped else '')
        self.update()

    def mouseReleaseEvent(self, e):
        if self.pan and e.button() == self.pan['button']:
            was = self.pan
            self.pan = None
            self._update_cursor()
            if was['button'] == QtCore.Qt.RightButton and not was['moved']:
                # right click: finish the current line / cancel a triangle pick
                self.chain = None
                self.tri_pick = []
                self.update()
            return
        if e.button() == QtCore.Qt.LeftButton and self.drag:
            self._finish_drag(e)
            self.update()

    def mouseDoubleClickEvent(self, e):
        if e.button() != QtCore.Qt.LeftButton:
            return
        st = self.state
        if st.tool == 'draw':
            self.chain = None     # the press before this already placed the point
            self.update()
            return
        if st.tool == 'triangle':
            # Qt delivers the second of two quick clicks as a double-click instead of a press;
            # treat it as a normal click so fast picking doesn't drop vertices
            self.mousePressEvent(e)
            return
        if st.tool == 'select' and st.mode == 'lines':
            key = st.active_key()
            pid, proj = self.hit_poly(key, e.position())
            if pid is not None and self.hit_vert(key, e.position()) is None:
                with self.doc.edit('Insert point'):
                    m = self.doc.split_edge(key, pid, proj)
                self.set_selection({('v', m)})

    def leaveEvent(self, e):
        self.snapped = None
        self.update()

    # ---- select tool
    def _press_select(self, e):
        key = self.state.active_key()
        g = self.doc.graph(key)
        sp = e.position()
        shift = bool(e.modifiers() & (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier))
        v = self.hit_vert(key, sp)
        if v is not None:
            item = ('v', v)
            if shift:
                self.set_selection(self.selection ^ {item})
                return
            if item not in self.selection:
                self.set_selection({item})
            self._start_move(key, anchor_vert=v, sp=sp)
            return
        pid, _ = self.hit_poly(key, sp)
        if pid is not None:
            item = ('p', pid)
            if shift:
                self.set_selection(self.selection ^ {item})
                return
            if item not in self.selection:
                self.set_selection({item})
            self._start_move(key, anchor_vert=None, sp=sp)
            return
        self.drag = {'kind': 'box', 'start': sp, 'additive': shift, 'started': False}
        if not shift:
            self.set_selection(set())

    def _selected_vert_ids(self, g):
        ids = {i for k, i in self.selection if k == 'v' and i in g.verts}
        for k, i in self.selection:
            if k == 'p' and i in g.polys:
                ids.update(g.polys[i])
        return ids

    def _start_move(self, key, anchor_vert, sp):
        g = self.doc.graph(key)
        ids = self._selected_vert_ids(g)
        self.drag = {
            'kind': 'move', 'key': key, 'ids': ids, 'anchor_vert': anchor_vert,
            'orig': {i: g.verts[i] for i in ids}, 'start': sp, 'start_world': self.to_world(sp),
            'started': False,
        }

    def _move_drag(self, e):
        d = self.drag
        sp = e.position()
        if not d['started']:
            if (sp - d['start']).manhattanLength() < DRAG_START_PX:
                return
            d['started'] = True
            if d['kind'] == 'move':
                self.doc.begin('Move')
        if d['kind'] == 'box':
            return
        if d['anchor_vert'] is not None:
            x, y, _ = self.snap(sp, e.modifiers(), d['key'], d['ids'])
            ax, ay = d['orig'][d['anchor_vert']]
            dx, dy = x - ax, y - ay
        else:
            wx, wy = self.to_world(sp)
            sx, sy = d['start_world']
            dx, dy = wx - sx, wy - sy
            s = self.state.snap
            if s and not (e.modifiers() & QtCore.Qt.AltModifier):
                dx, dy = round(dx / s) * s, round(dy / s) * s
        for i, (ox, oy) in d['orig'].items():
            self.doc.set_vert(d['key'], i, _clamp_tile(ox + dx, oy + dy))

    def _finish_drag(self, e):
        d, self.drag = self.drag, None
        if d['kind'] == 'box':
            if not d['started']:
                return
            a = self.to_world(d['start'])
            b = self.to_world(e.position())
            x0, x1 = sorted((a[0], b[0]))
            y0, y1 = sorted((a[1], b[1]))
            g = self.doc.graph(self.state.active_key())
            inside = {v for v, (x, y) in g.verts.items() if x0 <= x <= x1 and y0 <= y <= y1}
            sel = {('v', v) for v in inside}
            sel |= {('p', pid) for pid, poly in g.polys.items() if all(v in inside for v in poly)}
            self.set_selection((self.selection | sel) if d['additive'] else sel)
            return
        if not d['started']:
            return
        key = d['key']
        # Lines: dropping a single point onto another point welds them together.
        if key[0] == 'line' and len(d['ids']) == 1 and not (e.modifiers() & QtCore.Qt.AltModifier):
            (vid,) = d['ids']
            target = self.hit_vert(key, e.position(), exclude=d['ids'])
            if target is not None:
                self.doc.merge_vert(key, vid, target)
                self.selection = {('v', target)}
                self.hint.emit('Points welded')
        self.doc.commit()

    # ---- geometry tools
    def _press_add_vertex(self, e):
        key = self.state.active_key()
        v = self.hit_vert(key, e.position())
        if v is not None:
            self.set_selection({('v', v)})
            return
        x, y, _ = self.snap(e.position(), e.modifiers(), key)
        with self.doc.edit('Add vertex'):
            v = self.doc.add_vert(key, (x, y))
        self.set_selection({('v', v)})

    def _triangle_target(self, sp):
        """Snapped-cursor tuple for the vertex of the active layer the triangle tool would pick."""
        key = self.state.active_key()
        v = self.hit_vert(key, sp, radius=TRI_PICK_PX)
        if v is None:
            x, y = self.to_world(sp)
            return x, y, ''      # nothing in reach: plain crosshair, no snap ring
        x, y = self.doc.graph(key).verts[v]
        return x, y, 'point'

    def _press_triangle(self, e):
        key = self.state.active_key()
        g = self.doc.graph(key)
        v = self.hit_vert(key, e.position(), radius=TRI_PICK_PX)
        if v is None:
            self.hint.emit('Triangles can only use existing vertices - add one with the Vertex tool (V)')
            return
        if v in self.tri_pick:
            self.tri_pick.remove(v)
            return
        self.tri_pick.append(v)
        if len(self.tri_pick) == 3:
            a, b, c = (g.verts[i] for i in self.tri_pick)
            area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(area) < 1e-9:
                self.hint.emit('Those three vertices are in a line - no triangle made')
            else:
                with self.doc.edit('Add triangle'):
                    if self.doc.add_poly(key, tuple(self.tri_pick)) is None:
                        self.hint.emit('That triangle already exists')
            # keep the last two picked so you can fan / strip triangles quickly with Shift
            self.tri_pick = self.tri_pick[1:] if e.modifiers() & QtCore.Qt.ShiftModifier else []

    # ---- line draw tool
    def _press_draw(self, e):
        key = self.state.active_key()
        sp = e.position()
        exclude = ()
        v = self.hit_vert(key, sp)
        if v is not None:
            target = ('id', v)
        else:
            pid, proj = self.hit_poly(key, sp)
            if pid is not None:
                target = ('edge', pid, proj)
            else:
                x, y, _ = self.snap(sp, e.modifiers(), key)
                target = ('pos', (x, y))

        if self.chain is None:
            if target[0] == 'edge':
                with self.doc.edit('Split line'):
                    m = self.doc.split_edge(key, target[1], target[2])
                self.chain = ('id', m)
            elif target[0] == 'id':
                self.chain = target
            else:
                self.chain = target
            return

        if self.chain == target or (target[0] == 'pos' and self.chain[0] == 'pos' and self.chain[1] == target[1]):
            self.chain = None   # clicked the same spot twice: finish
            return
        with self.doc.edit('Draw line'):
            start = self.chain[1] if self.chain[0] == 'id' else self.doc.add_vert(key, self.chain[1])
            if target[0] == 'id':
                end = target[1]
            elif target[0] == 'edge':
                end = self.doc.split_edge(key, target[1], target[2])
            else:
                end = self.doc.add_vert(key, target[1])
            if start != end:
                self.doc.add_poly(key, (start, end))
        self.chain = ('id', end)

    # ------------------------------------------------------------------ commands
    def delete_selected(self):
        key = self.state.active_key()
        g = self.doc.graph(key)
        vids = [i for k, i in self.selection if k == 'v' and i in g.verts]
        pids = [i for k, i in self.selection if k == 'p' and i in g.polys]
        if not vids and not pids:
            return
        with self.doc.edit('Delete'):
            self.doc.delete(key, vids, pids, remove_orphans=(key[0] == 'line'))
        self.set_selection(set())

    def select_all(self):
        g = self.doc.graph(self.state.active_key())
        self.set_selection({('v', v) for v in g.verts} | {('p', p) for p in g.polys})
