"""
Mesh render dialog: build a scene from .mesh files, watch it draw (the animated
render from grunk2/r3, now inside the app), generate contour lines, then choose
where the result goes.
"""
import math
import os
import time

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import PRESETS, GROUND, GROUND_GROUP, GROUND_PRESETS, NUM_CHANNELS
from ..core.contours import extract_contours
from ..core.meshfile import MeshPlacement, build_scene
from ..core.tile_render import SceneRasteriser
from .import_dialogs import PlacementPicker
from .preset_picker import PresetPicker

COLS = ['Mesh file', 'X', 'Height', 'Z', 'Yaw°', 'Contours']

LINE_GROUPS = [
    # key, label, defaults
    ('shore', 'Shoreline', dict(imp=True, paint=False, channel=1, single=True, level=0.0)),
    ('height', 'Height contours', dict(imp=True, paint=False, channel=2, single=False,
                                       interval=106 / 9, count=9)),
    ('under', 'Undersea contours', dict(imp=False, paint=True, channel=1, single=True,
                                        interval=11.5, count=4)),
]
PAINT_COLORS = {'shore': [(0, 0, 255)], 'height': [(255, 0, 0), (255, 0, 255)],
                'under': [(255, 0, 0), (255, 0, 255)]}

# Ground placements first (the terrain usually goes in before the buildings), then buildings.
ALL_PRESETS = {**GROUND_PRESETS, **PRESETS}
PRESET_NOTES = {f'{GROUND_GROUP}: {tile}': f'Ground mesh: {mesh}' for tile, (mesh, _p, _y) in GROUND.items()}


def default_settings():
    return {
        'meshes': [],
        'resolution': 4096,
        'base_color': [255, 0, 255],
        'tolerance': 0.25,
        'replace_lines': True,
        'name_channels': True,
        'groups': {k: dict(d) for k, _, d in LINE_GROUPS},
    }


class PreviewWidget(QtWidgets.QWidget):
    """
    Shows the render. Wheel zooms about the cursor, left / middle / right drag pans,
    double-click (or 0) fits it back. When zoomed past the small preview image's
    resolution it draws from the full resolution image instead.
    """
    MAX_ZOOM = 64.0

    def __init__(self):
        super().__init__()
        self.image = None          # small preview image (always drawn into)
        self.full = None           # full resolution image, used when zoomed in
        self.setMinimumSize(360, 360)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setToolTip('Wheel: zoom · drag: pan · double-click: fit')
        self.message = 'Add meshes, then press Render'
        self.zoom = 1.0
        self.offset = QtCore.QPointF(0, 0)   # pan, in units of the fitted side length
        self._drag = None

    # ---------------------------------------------------------------- view maths
    def _side(self):
        return max(1.0, min(self.width(), self.height()) - 16.0)

    def _fit_rect(self):
        side = self._side()
        return QtCore.QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

    def _view_rect(self):
        """The image's on-screen rect at the current zoom / pan."""
        side = self._side()
        s = side * self.zoom
        return QtCore.QRectF(self.width() / 2 - s / 2 + self.offset.x() * side,
                             self.height() / 2 - s / 2 + self.offset.y() * side, s, s)

    def _clamp(self):
        # the image edges can't come inside the fitted square, so nothing is lost off-screen
        # and zooming back out to 1x always lands exactly on the fit
        lim = (self.zoom - 1) / 2
        self.offset = QtCore.QPointF(max(-lim, min(lim, self.offset.x())),
                                     max(-lim, min(lim, self.offset.y())))

    def zoom_at(self, factor, pos=None):
        if pos is None:
            pos = QtCore.QPointF(self.width() / 2, self.height() / 2)
        r = self._view_rect()
        u = (pos.x() - r.x()) / r.width()
        v = (pos.y() - r.y()) / r.height()
        self.zoom = max(1.0, min(self.MAX_ZOOM, self.zoom * factor))
        side = self._side()
        s = side * self.zoom
        # keep the image point under pos fixed
        self.offset = QtCore.QPointF((pos.x() - u * s - (self.width() / 2 - s / 2)) / side,
                                     (pos.y() - v * s - (self.height() / 2 - s / 2)) / side)
        self._clamp()
        self.update()

    def reset_view(self):
        self.zoom = 1.0
        self.offset = QtCore.QPointF(0, 0)
        self.update()

    # ---------------------------------------------------------------- input
    def wheelEvent(self, e):
        steps = e.angleDelta().y() / 120.0
        if steps:
            self.zoom_at(1.25 ** steps, e.position())
        e.accept()

    def mousePressEvent(self, e):
        if e.button() in (QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._drag = (e.position(), QtCore.QPointF(self.offset))
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            start, off0 = self._drag
            d = (e.position() - start) / self._side()
            self.offset = off0 + d
            self._clamp()
            self.update()

    def mouseReleaseEvent(self, e):
        if self._drag is not None and not (e.buttons() & (QtCore.Qt.LeftButton | QtCore.Qt.MiddleButton
                                                          | QtCore.Qt.RightButton)):
            self._drag = None
            self.unsetCursor()

    def mouseDoubleClickEvent(self, e):
        self.reset_view()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
            self.zoom_at(1.25)
        elif k == QtCore.Qt.Key_Minus:
            self.zoom_at(0.8)
        elif k == QtCore.Qt.Key_0:
            self.reset_view()
        else:
            super().keyPressEvent(e)

    # ---------------------------------------------------------------- drawing
    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(18, 20, 24))
        r = self._view_rect()
        if self.image is not None:
            # use the full resolution image once the preview would be upscaled, as long as
            # that doesn't mean shrinking the full image more than 4x (it aliases badly)
            img = self.image
            if (self.full is not None and r.width() > img.width()
                    and r.width() >= self.full.width() / 4):
                img = self.full
            px = r.width() / img.width()             # screen px per image px
            # only scale the visible part (the full image can be 16k px wide)
            vis = r.intersected(QtCore.QRectF(self.rect()))
            if not vis.isEmpty():
                src = QtCore.QRectF((vis.x() - r.x()) / px, (vis.y() - r.y()) / px,
                                    vis.width() / px, vis.height() / px)
                # crisp pixels when zoomed right in, smooth otherwise
                p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, px < 4)
                p.drawImage(vis, img, src)
        else:
            p.setPen(QtGui.QColor(150, 155, 165))
            p.drawText(self._fit_rect(), QtCore.Qt.AlignCenter, self.message)
        p.setPen(QtGui.QPen(QtGui.QColor(235, 70, 70), 1, QtCore.Qt.DashLine))
        p.drawRect(r)
        if self.zoom > 1.0:
            txt = f'{self.zoom * 100:.0f}%  ·  double-click to fit'
            fm = p.fontMetrics()
            box = QtCore.QRectF(6, self.height() - fm.height() - 10, fm.horizontalAdvance(txt) + 12,
                                fm.height() + 4)
            p.fillRect(box, QtGui.QColor(0, 0, 0, 160))
            p.setPen(QtGui.QColor(220, 222, 228))
            p.drawText(box, QtCore.Qt.AlignCenter, txt)
        p.end()


class MeshRenderDialog(QtWidgets.QDialog):

    def __init__(self, parent, state, settings=None):
        super().__init__(parent)
        self.setWindowTitle('Render meshes')
        self.state = state
        self.settings = settings or default_settings()
        self.mesh_cache = {}
        self.raster = None
        self.scene = None
        self.line_sets = []        # [(channel index, name, polylines)] to import
        self.paint_sets = []       # [(group, level index, polylines)]
        self.result_image = None
        self.stale = True
        self._loading = False

        root = QtWidgets.QHBoxLayout(self)
        left = QtWidgets.QVBoxLayout()
        root.addLayout(left, 3)
        right = QtWidgets.QVBoxLayout()
        root.addLayout(right, 2)

        # ---- meshes
        gb = QtWidgets.QGroupBox('Meshes')
        gl = QtWidgets.QVBoxLayout(gb)
        self.table = QtWidgets.QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for c in range(1, len(COLS)):
            self.table.horizontalHeader().setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(130)
        self.table.setToolTip('Each mesh is rotated by Yaw about the vertical axis, then moved by X / Height / Z.\n'
                              'Tile X = mesh X, tile Y (north) = mesh Z. Height shifts contour levels.\n'
                              'Untick Contours for meshes (e.g. hangars) that should not make lines.')
        gl.addWidget(self.table)
        row = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton('Add mesh…')
        add.clicked.connect(self._add_meshes)
        self.preset_btn = QtWidgets.QPushButton('Apply placement preset…')
        self.preset_btn.setToolTip('Search the known ground (terrain) and building / runway placements '
                                   'and apply one to the selected mesh row(s)')
        self.preset_btn.clicked.connect(self._open_presets)
        self.preset_picker = None   # built on first use, then kept so the last search is remembered
        rem = QtWidgets.QPushButton('Remove')
        rem.clicked.connect(self._remove_rows)
        row.addWidget(add)
        row.addWidget(self.preset_btn)
        row.addStretch(1)
        row.addWidget(rem)
        gl.addLayout(row)
        left.addWidget(gb)

        # ---- render
        gb = QtWidgets.QGroupBox('Render')
        fl = QtWidgets.QFormLayout(gb)
        self.res = QtWidgets.QSpinBox()
        self.res.setRange(256, 16384)
        self.res.setSingleStep(512)
        self.res.setSuffix(' px')
        self.res.setValue(self.settings['resolution'])
        fl.addRow('Resolution', self.res)
        self.color_btn = QtWidgets.QPushButton()
        self.color_btn.clicked.connect(self._pick_color)
        fl.addRow('Background colour', self.color_btn)
        self._set_color(self.settings['base_color'])
        left.addWidget(gb)

        # ---- lines
        gb = QtWidgets.QGroupBox('Generated lines')
        grid = QtWidgets.QGridLayout(gb)
        heads = ['', 'Add as lines', 'Paint on image', 'Channel', 'Channels', 'Interval / level (m)', 'Levels']
        for c, h in enumerate(heads):
            grid.addWidget(QtWidgets.QLabel(f'<small>{h}</small>'), 0, c)
        self.group_widgets = {}
        for r, (key, label, _d) in enumerate(LINE_GROUPS, start=1):
            g = self.settings['groups'][key]
            w = {}
            grid.addWidget(QtWidgets.QLabel(f'<b>{label}</b>'), r, 0)
            w['imp'] = QtWidgets.QCheckBox()
            w['imp'].setChecked(g['imp'])
            grid.addWidget(w['imp'], r, 1, QtCore.Qt.AlignCenter)
            w['paint'] = QtWidgets.QCheckBox()
            w['paint'].setChecked(g['paint'])
            grid.addWidget(w['paint'], r, 2, QtCore.Qt.AlignCenter)
            w['channel'] = QtWidgets.QSpinBox()
            w['channel'].setRange(1, NUM_CHANNELS)
            w['channel'].setValue(g['channel'])
            grid.addWidget(w['channel'], r, 3)
            w['single'] = QtWidgets.QComboBox()
            w['single'].addItems(['One per level', 'All in one'])
            w['single'].setCurrentIndex(1 if g['single'] else 0)
            grid.addWidget(w['single'], r, 4)
            if key == 'shore':
                w['level'] = QtWidgets.QDoubleSpinBox()
                w['level'].setRange(-1000, 1000)
                w['level'].setDecimals(2)
                w['level'].setValue(g['level'])
                w['level'].setToolTip('Sea level height')
                grid.addWidget(w['level'], r, 5)
                w['single'].setEnabled(False)
            else:
                w['interval'] = QtWidgets.QDoubleSpinBox()
                w['interval'].setRange(0.1, 1000)
                w['interval'].setDecimals(3)
                w['interval'].setValue(g['interval'])
                w['interval'].setToolTip('Height step between contour levels ' +
                                         ('(above sea level)' if key == 'height' else '(below sea level)'))
                grid.addWidget(w['interval'], r, 5)
                w['count'] = QtWidgets.QSpinBox()
                w['count'].setRange(1, 50)
                w['count'].setValue(g['count'])
                grid.addWidget(w['count'], r, 6)
            self.group_widgets[key] = w
        r = len(LINE_GROUPS) + 1
        self.tol = QtWidgets.QDoubleSpinBox()
        self.tol.setRange(0, 20)
        self.tol.setDecimals(2)
        self.tol.setSingleStep(0.05)
        self.tol.setSuffix(' m')
        self.tol.setValue(self.settings['tolerance'])
        self.tol.setToolTip('Simplify generated lines: points closer than this to the straight line are dropped.\n0 keeps every triangle crossing.')
        grid.addWidget(QtWidgets.QLabel('Simplify'), r, 0)
        grid.addWidget(self.tol, r, 1, 1, 2)
        self.replace = QtWidgets.QCheckBox('Replace existing lines in those channels')
        self.replace.setChecked(self.settings['replace_lines'])
        grid.addWidget(self.replace, r + 1, 0, 1, 4)
        self.name_channels = QtWidgets.QCheckBox('Name channels after their levels')
        self.name_channels.setChecked(self.settings['name_channels'])
        grid.addWidget(self.name_channels, r + 1, 4, 1, 3)
        left.addWidget(gb)
        left.addStretch(1)

        # ---- preview side
        self.preview = PreviewWidget()
        right.addWidget(self.preview, 1)
        self.progress = QtWidgets.QProgressBar()
        right.addWidget(self.progress)
        sp = QtWidgets.QHBoxLayout()
        sp.addWidget(QtWidgets.QLabel('Draw speed'))
        self.speed = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed.setRange(0, 100)
        self.speed.setValue(45)
        self.speed.setToolTip('Triangles drawn per frame (far right is instant)')
        sp.addWidget(self.speed, 1)
        right.addLayout(sp)
        br = QtWidgets.QHBoxLayout()
        self.render_btn = QtWidgets.QPushButton('Render')
        self.render_btn.setDefault(True)
        self.render_btn.clicked.connect(self.start_render)
        self.skip_btn = QtWidgets.QPushButton('Skip animation')
        self.skip_btn.setEnabled(False)
        self.skip_btn.clicked.connect(self._skip)
        br.addWidget(self.render_btn)
        br.addWidget(self.skip_btn)
        right.addLayout(br)
        self.info = QtWidgets.QLabel()
        self.info.setWordWrap(True)
        right.addWidget(self.info)

        right.addWidget(QtWidgets.QLabel('<b>Place result</b>'))
        self.picker = PlacementPicker(state, 'C')
        right.addWidget(self.picker, 0, QtCore.Qt.AlignHCenter)
        self.place_note = QtWidgets.QLabel()
        self.place_note.setWordWrap(True)
        right.addWidget(self.place_note)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.place_btn = bb.button(QtWidgets.QDialogButtonBox.Ok)
        self.place_btn.setText('Place')
        self.place_btn.setEnabled(False)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        right.addWidget(bb)
        self.picker.changed.connect(self._update_place_note)
        self._update_place_note('C')

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

        for m in self.settings['meshes']:
            self._append_row(MeshPlacement.from_dict(m))
        self._connect_stale()
        self.resize(1240, 760)

    # ------------------------------------------------------------ meshes table
    def _append_row(self, pl: MeshPlacement):
        self._loading = True
        r = self.table.rowCount()
        self.table.insertRow(r)
        it = QtWidgets.QTableWidgetItem(os.path.basename(pl.path))
        it.setToolTip(pl.path)
        it.setData(QtCore.Qt.UserRole, pl.path)
        it.setFlags(it.flags() & ~QtCore.Qt.ItemIsEditable)
        self.table.setItem(r, 0, it)
        for c, v in enumerate((pl.x, pl.y, pl.z, pl.yaw), start=1):
            self.table.setItem(r, c, QtWidgets.QTableWidgetItem(f'{v:g}'))
        cb = QtWidgets.QTableWidgetItem()
        cb.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        cb.setCheckState(QtCore.Qt.Checked if pl.contours else QtCore.Qt.Unchecked)
        self.table.setItem(r, 5, cb)
        self._loading = False
        self._mark_stale()

    def _add_meshes(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Add meshes', self.state.last_dir,
                                                          'Stormworks mesh (*.mesh);;All files (*)')
        for p in paths:
            self.state.last_dir = os.path.dirname(p)
            self._append_row(MeshPlacement(p))

    def _remove_rows(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)
        self._mark_stale()

    def _selected_rows(self):
        return sorted({i.row() for i in self.table.selectedIndexes()})

    def _open_presets(self):
        if not self._selected_rows():
            QtWidgets.QMessageBox.information(self, 'Preset', 'Select the mesh row(s) to apply the preset to first.')
            return
        if self.preset_picker is None:
            self.preset_picker = PresetPicker(ALL_PRESETS, self, PRESET_NOTES)
            self.preset_picker.picked.connect(self._apply_preset)
        self.preset_picker.popup(self.preset_btn)

    def _apply_preset(self, name):
        rows = self._selected_rows()
        if not rows:
            QtWidgets.QMessageBox.information(self, 'Preset', 'Select the mesh row(s) to apply the preset to first.')
            return
        (x, y, z), yaw = ALL_PRESETS[name]
        # ground meshes make the shore / height lines; buildings shouldn't
        contours = QtCore.Qt.Checked if name in GROUND_PRESETS else QtCore.Qt.Unchecked
        for r in rows:
            for c, v in enumerate((x, y, z, yaw), start=1):
                self.table.item(r, c).setText(f'{v:g}')
            self.table.item(r, 5).setCheckState(contours)

    def placements(self):
        out = []
        for r in range(self.table.rowCount()):
            vals = []
            for c in range(1, 5):
                try:
                    vals.append(float(self.table.item(r, c).text()))
                except (ValueError, AttributeError):
                    vals.append(0.0)
            out.append(MeshPlacement(self.table.item(r, 0).data(QtCore.Qt.UserRole), *vals,
                                     contours=self.table.item(r, 5).checkState() == QtCore.Qt.Checked))
        return out

    # ------------------------------------------------------------ settings
    def _set_color(self, rgb):
        self.base_color = tuple(rgb)
        pm = QtGui.QPixmap(40, 14)
        pm.fill(QtGui.QColor(*rgb))
        self.color_btn.setIcon(QtGui.QIcon(pm))
        self.color_btn.setText(' #%02x%02x%02x' % tuple(rgb))

    def _pick_color(self):
        c = QtWidgets.QColorDialog.getColor(QtGui.QColor(*self.base_color), self, 'Background colour')
        if c.isValid():
            self._set_color((c.red(), c.green(), c.blue()))
            self._mark_stale()

    def collect_settings(self):
        s = {
            'meshes': [p.to_dict() for p in self.placements()],
            'resolution': self.res.value(),
            'base_color': list(self.base_color),
            'tolerance': self.tol.value(),
            'replace_lines': self.replace.isChecked(),
            'name_channels': self.name_channels.isChecked(),
            'groups': {},
        }
        for key, w in self.group_widgets.items():
            g = {'imp': w['imp'].isChecked(), 'paint': w['paint'].isChecked(),
                 'channel': w['channel'].value(), 'single': w['single'].currentIndex() == 1}
            if key == 'shore':
                g['level'] = w['level'].value()
            else:
                g['interval'] = w['interval'].value()
                g['count'] = w['count'].value()
            s['groups'][key] = g
        return s

    def _connect_stale(self):
        self.table.itemChanged.connect(lambda *_: None if self._loading else self._mark_stale())
        for wdg in [self.res, self.tol]:
            wdg.valueChanged.connect(self._mark_stale)
        for w in self.group_widgets.values():
            for k, wdg in w.items():
                if isinstance(wdg, QtWidgets.QCheckBox):
                    wdg.toggled.connect(self._mark_stale)
                elif isinstance(wdg, QtWidgets.QComboBox):
                    wdg.currentIndexChanged.connect(self._mark_stale)
                else:
                    wdg.valueChanged.connect(self._mark_stale)

    def _mark_stale(self, *_):
        if self.raster is not None and not self.stale:
            self.info.setText('Settings changed - press Render again.')
        self.stale = True
        self.place_btn.setEnabled(False)

    def _update_place_note(self, slot):
        if slot == 'C':
            self.place_note.setText('Centre: the render becomes the reference image under your tile, '
                                    'and the "Add as lines" groups are added as editable lines (undoable).')
        else:
            self.place_note.setText('Neighbour: only the image is placed, as a reference beside your tile.')

    # ------------------------------------------------------------ rendering
    def _levels(self, key, g):
        if key == 'shore':
            return [g['level']]
        sign = 1 if key == 'height' else -1
        base = self.group_widgets['shore']['level'].value()
        return [base + sign * g['interval'] * (k + 1) for k in range(g['count'])]

    def start_render(self):
        placements = self.placements()
        if not placements:
            QtWidgets.QMessageBox.information(self, 'Render', 'Add at least one .mesh file first.')
            return
        self.timer.stop()
        s = self.collect_settings()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            t0 = time.time()
            self.scene = build_scene(placements, self.mesh_cache)
            self.line_sets, self.paint_sets = [], []
            notes = []
            for key, label, _ in LINE_GROUPS:
                g = s['groups'][key]
                if not (g['imp'] or g['paint']):
                    continue
                for k, level in enumerate(self._levels(key, g)):
                    polys = extract_contours(self.scene.contour_meshes, level, s['tolerance'])
                    if g['paint']:
                        self.paint_sets.append((key, k, polys))
                    if g['imp']:
                        ch = g['channel'] - 1 + (0 if g['single'] else k)
                        if ch >= NUM_CHANNELS:
                            notes.append(f'{label} {level:.1f} m skipped (past channel 10)')
                            continue
                        self.line_sets.append((ch, f'{label.split()[0]} {round(level, 1):g} m', polys))
            t_contours = time.time() - t0
        except Exception as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, 'Render failed', str(e))
            return
        QtWidgets.QApplication.restoreOverrideCursor()

        self.raster = SceneRasteriser(self.scene, s['resolution'], self.base_color)
        self.preview.image = self.raster.preview
        self.preview.full = self.raster.image
        self.progress.setRange(0, max(1, self.raster.total))
        self.progress.setValue(0)
        self.stale = False
        self.place_btn.setEnabled(False)
        self.skip_btn.setEnabled(True)
        n_lines = sum(len(p) for _, _, p in self.line_sets)
        self.info.setText(f'{self.raster.total} visible triangles from {len(placements)} mesh(es). '
                          f'{n_lines} line pieces in {len({c for c, _, _ in self.line_sets})} channel(s) '
                          f'({t_contours:.1f}s).' + (' ' + '; '.join(notes) if notes else ''))
        self.timer.start()

    def _per_frame(self):
        v = self.speed.value()
        if v >= 100:
            return 10 ** 9
        return max(1, int(round(10 ** (v / 100 * 4))))

    def _tick(self):
        if self.raster is None:
            self.timer.stop()
            return
        self.raster.step(self._per_frame())
        self.progress.setValue(self.raster.index)
        self.preview.update()
        if self.raster.done():
            self._finish()

    def _skip(self):
        if self.raster is None:
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        while not self.raster.done():
            self.raster.step(20000)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.progress.setValue(self.raster.index)
        self._finish()

    def _finish(self):
        self.timer.stop()
        self.skip_btn.setEnabled(False)
        width = max(2.0, self.raster.size / 2000)
        for key, k, polys in self.paint_sets:
            colors = PAINT_COLORS[key]
            self.raster.paint_lines(polys, colors[k % len(colors)], width)
        self.result_image = self.raster.image
        self.preview.update()
        self.place_btn.setEnabled(not self.stale)

    def render_result(self):
        return {
            'image': self.result_image,
            'slot': self.picker.slot(),
            'line_sets': self.line_sets,
            'settings': self.collect_settings(),
            'label': ', '.join(os.path.basename(p.path) for p in self.placements()),
        }

    def reject(self):
        self.timer.stop()
        super().reject()
