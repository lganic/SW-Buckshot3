"""Buckshot 3 main window: combined geometry / line editor plus import and export."""
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import bin_io, project_io
from ..core.constants import SNAP_AMOUNTS, NUM_CHANNELS, RENDER_ORDER, SLOT_NAMES
from ..core.model import Document
from ..core.tile_render import render_tiledata
from .canvas import Canvas
from .import_dialogs import ImportScreen, BinImportDialog, ImageImportDialog
from .mesh_dialog import MeshRenderDialog
from .panels import LayersPanel, ReferencePanel
from .paths import PathCache
from .state import EditorState, ImageRef, Neighbour

TOOL_INFO = {
    ('geometry', 'select'): ('Select / move', 'G',
                             'Click or box-drag to select · drag to move · Shift adds · Del deletes'),
    ('geometry', 'vertex'): ('Add vertex', 'V', 'Click to place a vertex (snaps to grid and nearby points; Alt = free)'),
    ('geometry', 'triangle'): ('Triangle', 'T',
                               'Click 3 vertices (or empty space to make one) · Shift-click the 3rd to keep strip-building · right-click cancels'),
    ('lines', 'select'): ('Select / move', 'G',
                          'Drag points (drop on another point to weld) · double-click a line to insert a point · Del deletes'),
    ('lines', 'draw'): ('Draw lines', 'V',
                        'Click point to point · click an existing point or line to connect · double-click / right-click / Enter ends'),
}


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.doc = Document()
        self.state = EditorState()
        self.paths = PathCache(self.doc)
        self.project_path = None

        self.canvas = Canvas(self.doc, self.state, self.paths)
        self.setCentralWidget(self.canvas)

        self.layers_panel = LayersPanel(self.doc, self.state, self.paths, self.canvas)
        dock = QtWidgets.QDockWidget('Layer stack', self)
        dock.setObjectName('layers')
        dock.setWidget(self.layers_panel)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

        self.ref_panel = ReferencePanel(self.state)
        self.ref_panel.importRequested.connect(self.import_anything)
        dock2 = QtWidgets.QDockWidget('View && references', self)
        dock2.setObjectName('refs')
        dock2.setWidget(self.ref_panel)
        dock2.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock2)
        self.resizeDocks([dock], [360], QtCore.Qt.Horizontal)

        self._build_actions()
        self._build_status()
        QtWidgets.QApplication.instance().installEventFilter(self)

        self.doc.historyChanged.connect(self._update_title)
        self.state.changed.connect(self._on_state_changed)
        self.canvas.hint.connect(lambda m: self.statusBar().showMessage(m, 4000))
        self._on_state_changed('mode')
        self._update_title()

    # ------------------------------------------------------------------ actions
    def _act(self, text, slot=None, shortcut=None, checkable=False, tip=None):
        a = QtGui.QAction(text, self)
        if shortcut:
            a.setShortcuts(shortcut if isinstance(shortcut, list) else [QtGui.QKeySequence(shortcut)])
        if checkable:
            a.setCheckable(True)
        if tip:
            a.setToolTip(tip)
            a.setStatusTip(tip)
        if slot:
            a.triggered.connect(slot)
        return a

    def _build_actions(self):
        mb = self.menuBar()
        fm = mb.addMenu('&File')
        fm.addAction(self._act('New tile', self.new_project, 'Ctrl+N'))
        fm.addAction(self._act('Open project…', self.open_project, 'Ctrl+O'))
        fm.addAction(self._act('Save project', self.save_project, 'Ctrl+S'))
        fm.addAction(self._act('Save project as…', self.save_project_as, 'Ctrl+Shift+S'))
        fm.addSeparator()
        self.import_action = self._act('Import…', self.import_anything, 'Ctrl+I',
                                       tip='Import a .mesh render, a .bin tile or an image')
        fm.addAction(self.import_action)
        fm.addAction(self._act('Import .mesh render…', lambda: self.import_choice('mesh')))
        fm.addAction(self._act('Import .bin tile…', lambda: self.import_choice('bin')))
        fm.addAction(self._act('Import reference image…', lambda: self.import_choice('image')))
        fm.addSeparator()
        self.export_action = self._act('Export .bin…', self.export_bin, 'Ctrl+E',
                                       tip='Write the tile and its lines to a Stormworks map geometry .bin')
        fm.addAction(self.export_action)
        fm.addSeparator()
        fm.addAction(self._act('Exit', self.close, 'Ctrl+Q'))

        em = mb.addMenu('&Edit')
        self.undo_action = self._act('Undo', self.undo, [QtGui.QKeySequence('Ctrl+Z')])
        self.redo_action = self._act('Redo', self.redo, [QtGui.QKeySequence('Ctrl+Y'), QtGui.QKeySequence('Ctrl+Shift+Z')])
        em.addAction(self.undo_action)
        em.addAction(self.redo_action)
        em.addSeparator()
        em.addAction(self._act('Delete selected  (Del)', self.canvas.delete_selected))
        em.addAction(self._act('Select all', self.canvas.select_all, 'Ctrl+A'))
        em.addSeparator()
        em.addAction(self._act('Clear active layer / channel', self.clear_active))

        vm = mb.addMenu('&View')
        vm.addAction(self._act('Fit tile', self.canvas.fit_tile, 'F'))
        vm.addAction(self._act('Fit tile and neighbours', self.canvas.fit_all, 'Shift+F'))
        vm.addAction(self._act('Switch layer stack / render preview', self.layers_panel.toggle_view, 'R'))

        # mode + tools
        tb = self.addToolBar('Tools')
        tb.setObjectName('tools')
        tb.setMovable(False)
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.mode_group = QtGui.QActionGroup(self)
        self.mode_actions = {}
        for mode, label in (('geometry', 'Geometry'), ('lines', 'Lines')):
            a = self._act(f'{label}', lambda _=False, m=mode: self.state.set_mode(m), None, True,
                          f'{label} mode (Tab toggles)')
            self.mode_group.addAction(a)
            self.mode_actions[mode] = a
            tb.addAction(a)
        for a in self.mode_actions.values():
            w = tb.widgetForAction(a)
            w.setMinimumWidth(80)
            f = w.font(); f.setBold(True); w.setFont(f)
        toggle = QtGui.QShortcut(QtGui.QKeySequence('Tab'), self)
        toggle.activated.connect(lambda: self.state.set_mode('lines' if self.state.mode == 'geometry' else 'geometry'))
        mm = mb.addMenu('&Mode')
        for a in self.mode_actions.values():
            mm.addAction(a)
        tb.addSeparator()

        self.tool_group = QtGui.QActionGroup(self)
        self.tool_actions = {}
        for (mode, tool), (label, key, tip) in TOOL_INFO.items():
            a = self._act(f'{label} ({key})', lambda _=False, t=tool: self.state.set_tool(t), None, True, tip)
            self.tool_group.addAction(a)
            self.tool_actions[(mode, tool)] = a
            tb.addAction(a)
            mm.addAction(a)
        # G selects in both modes; V places points (a vertex, or the next point of a line)
        for key, tools in (('G', ('select',)), ('V', ('vertex', 'draw')), ('T', ('triangle',))):
            sc = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            sc.activated.connect(lambda ts=tools: [self._shortcut_tool(t) for t in ts])
        for i, key in enumerate('1234567890'):
            sc = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            sc.activated.connect(lambda i=i: self._number_key(i))
        tb.addSeparator()

        tb.addWidget(QtWidgets.QLabel(' Snap '))
        self.snap_combo = QtWidgets.QComboBox()
        for s in SNAP_AMOUNTS:
            self.snap_combo.addItem('Off' if s == 0 else f'{s:g} m', s)
        self.snap_combo.setCurrentIndex(SNAP_AMOUNTS.index(self.state.snap))
        self.snap_combo.currentIndexChanged.connect(
            lambda i: (setattr(self.state, 'snap', SNAP_AMOUNTS[i]), self.state.emit('view')))
        self.snap_combo.setToolTip('Grid snap. Existing points always snap within a few pixels; hold Alt for none.')
        tb.addWidget(self.snap_combo)
        tb.addSeparator()
        tb.addAction(self.undo_action)
        tb.addAction(self.redo_action)
        tb.addSeparator()
        tb.addAction(self.import_action)
        tb.addAction(self.export_action)

    def _shortcut_tool(self, tool):
        tools = EditorState.GEOMETRY_TOOLS if self.state.mode == 'geometry' else EditorState.LINE_TOOLS
        if tool in tools:
            self.state.set_tool(tool)

    PAN_KEYS = {QtCore.Qt.Key_W, QtCore.Qt.Key_A, QtCore.Qt.Key_S, QtCore.Qt.Key_D}

    def eventFilter(self, obj, e):
        t = e.type()
        if t in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease) and e.key() in self.PAN_KEYS:
            if not isinstance(obj, QtGui.QWindow) or not obj.isActive():
                return False         # handle each key once, at the window level
            if t == QtCore.QEvent.KeyRelease and not e.isAutoRepeat():
                self.canvas.set_pan_key(e.key(), False)     # always release, so keys never stick
            focus = QtWidgets.QApplication.focusWidget()
            typing = isinstance(focus, (QtWidgets.QLineEdit, QtWidgets.QAbstractSpinBox,
                                        QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit))
            mods = e.modifiers() & (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier | QtCore.Qt.MetaModifier)
            if typing or mods or QtWidgets.QApplication.activeModalWidget() is not None:
                return False
            if t == QtCore.QEvent.KeyPress and not e.isAutoRepeat():
                self.canvas.set_pan_key(e.key(), True)
            return True
        if t == QtCore.QEvent.ApplicationDeactivate:
            self.canvas.clear_pan_keys()
        return False

    def _number_key(self, i):
        if self.state.mode == 'lines':
            self.state.set_active_channel(i)
        elif i < len(RENDER_ORDER):
            self.state.set_active_layer(RENDER_ORDER[i])

    def _build_status(self):
        sb = self.statusBar()
        self.coord_label = QtWidgets.QLabel()
        self.sel_label = QtWidgets.QLabel()
        sb.addPermanentWidget(self.sel_label)
        sb.addPermanentWidget(self.coord_label)
        self.canvas.cursorMoved.connect(
            lambda x, y, k: self.coord_label.setText(f'  x {x:8.2f}   y {y:8.2f}  {("· " + k) if k else ""}  '))
        self.canvas.selectionChanged.connect(lambda n: self.sel_label.setText(f'{n} selected  ' if n else ''))

    def _on_state_changed(self, what):
        st = self.state
        if what in ('mode', 'tool', 'active'):
            self.mode_actions[st.mode].setChecked(True)
            for (mode, tool), a in self.tool_actions.items():
                a.setVisible(mode == st.mode)
                if mode == st.mode and tool == st.tool:
                    a.setChecked(True)
            self.statusBar().showMessage(TOOL_INFO[(st.mode, st.tool)][2])
        if what == 'names':
            self.canvas.update()
        if what == 'refs':
            self.canvas.update()

    def _update_title(self):
        name = os.path.basename(self.project_path) if self.project_path else 'Untitled tile'
        self.setWindowTitle(f'{"* " if self.doc.is_dirty() else ""}{name} - Buckshot 3')
        u = self.doc.undo_stack[-1][0] if self.doc.undo_stack else None
        r = self.doc.redo_stack[-1][0] if self.doc.redo_stack else None
        self.undo_action.setText(f'Undo {u}' if u else 'Undo')
        self.undo_action.setEnabled(u is not None)
        self.redo_action.setText(f'Redo {r}' if r else 'Redo')
        self.redo_action.setEnabled(r is not None)

    # ------------------------------------------------------------------ editing
    def undo(self):
        label = self.doc.undo()
        if label:
            self.statusBar().showMessage(f'Undid: {label}', 3000)

    def redo(self):
        label = self.doc.redo()
        if label:
            self.statusBar().showMessage(f'Redid: {label}', 3000)

    def clear_active(self):
        key = self.state.active_key()
        name = key[1] if key[0] == 'layer' else self.doc.channel_names[key[1]]
        if self.doc.graph(key).is_empty():
            return
        if QtWidgets.QMessageBox.question(self, 'Clear', f'Remove everything in {name}? (Undoable)') \
                != QtWidgets.QMessageBox.Yes:
            return
        with self.doc.edit(f'Clear {name}'):
            self.doc.clear_container(key)

    # ------------------------------------------------------------------ import
    def import_anything(self, show_blank=False):
        dlg = ImportScreen(self, show_blank=show_blank)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        self.import_choice(dlg.choice())

    def import_choice(self, choice):
        try:
            if choice == 'mesh':
                self.import_mesh()
            elif choice == 'bin':
                self.import_bin()
            elif choice == 'image':
                self.import_image()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Import failed', f'{type(e).__name__}: {e}')

    def _ask_file(self, title, filt):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, self.state.last_dir, filt)
        if path:
            self.state.last_dir = os.path.dirname(path)
        return path

    def import_mesh(self):
        dlg = MeshRenderDialog(self, self.state, self.state.last_mesh_settings)
        ok = dlg.exec() == QtWidgets.QDialog.Accepted
        self.state.last_mesh_settings = dlg.collect_settings()
        if not ok:
            return
        res = dlg.render_result()
        ref = ImageRef(res['image'], res['label'])
        slot = res['slot']
        if slot == 'C':
            self.state.background = ref
            self._add_generated_lines(res['line_sets'], res['settings'])
        else:
            self.state.neighbours[slot] = Neighbour(slot, 'mesh', ref, settings=res['settings'])
            self.state.neighbours[slot].compute_edge_points()
        self.state.emit('refs')
        self.statusBar().showMessage(f'Placed render in {SLOT_NAMES[slot]}', 5000)

    def _add_generated_lines(self, line_sets, settings):
        if not line_sets:
            return
        by_channel = {}
        for ch, name, polys in line_sets:
            by_channel.setdefault(ch, []).append((name, polys))
        with self.doc.edit('Import generated lines'):
            for ch, entries in by_channel.items():
                key = ('line', ch)
                if settings.get('replace_lines', True):
                    self.doc.clear_container(key)
                for _name, polys in entries:
                    for poly in polys:
                        self.doc.add_polyline(key, [tuple(p) for p in poly.tolist()])
        if settings.get('name_channels', True):
            for ch, entries in by_channel.items():
                names = [n for n, _ in entries]
                self.doc.channel_names[ch] = names[0] if len(names) == 1 else f'{names[0]} … ({len(names)} levels)'
            self.state.emit('names')
        n = sum(len(p) for _, _, p in line_sets)
        self.statusBar().showMessage(f'Added {n} generated lines to {len(by_channel)} channel(s) - Ctrl+Z to undo', 6000)

    def _confirm_replace_tile(self):
        if self.doc.is_empty() or not self.doc.is_dirty():
            return True
        r = QtWidgets.QMessageBox.question(
            self, 'Replace tile', 'Replace the tile you are editing? Unsaved changes will be lost.',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        return r == QtWidgets.QMessageBox.Yes

    def import_bin(self, path=None):
        path = path or self._ask_file('Import map geometry', 'Map geometry (*.bin);;All files (*)')
        if not path:
            return
        td = bin_io.load_bin(path)
        dlg = BinImportDialog(self, self.state, path, td, self.doc.is_empty())
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        slot = dlg.picker.slot()
        if slot == 'C':
            if not self._confirm_replace_tile():
                return
            self.canvas.reset_interaction()
            self.doc.reset(td.layers, td.channels if dlg.lines.isChecked() else None)
            self.statusBar().showMessage(f'Loaded {os.path.basename(path)}: {td.tri_count()} triangles', 5000)
        else:
            self._place_bin_neighbour(slot, path, dlg.res.value(), td)
        self._update_title()

    def _place_bin_neighbour(self, slot, path, res, td=None):
        td = td or bin_io.load_bin(path)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            img = render_tiledata(td, res)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        nb = Neighbour(slot, 'bin', ImageRef(img, os.path.basename(path), path), path, res, td)
        nb.compute_edge_points()
        self.state.neighbours[slot] = nb
        self.state.emit('refs')
        if not self.canvas.view_world_rect().contains(QtCore.QRectF(-1500, -1500, 3000, 3000)):
            self.canvas.fit_all()

    def import_image(self, path=None):
        path = path or self._ask_file('Import reference image',
                                      'Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff);;All files (*)')
        if not path:
            return
        dlg = ImageImportDialog(self, self.state, path)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        ref = ImageRef(project_io.load_image(path), os.path.basename(path), path)
        slot = dlg.picker.slot()
        if slot == 'C':
            self.state.background = ref
        else:
            self.state.neighbours[slot] = Neighbour(slot, 'image', ref, path)
            self.state.neighbours[slot].compute_edge_points()
        self.state.emit('refs')

    # ------------------------------------------------------------------ export
    def export_bin(self):
        start = os.path.splitext(self.project_path)[0] + '.bin' if self.project_path else self.state.last_dir
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export map geometry', start, 'Map geometry (*.bin)')
        if not path:
            return
        if not path.lower().endswith('.bin'):
            path += '.bin'
        try:
            stats = bin_io.export_bin(self.doc, path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Export failed', f'{type(e).__name__}: {e}')
            return
        self.state.last_dir = os.path.dirname(path)
        self.statusBar().showMessage(
            f'Exported {os.path.basename(path)}: {stats["tris"]} triangles, '
            f'{stats["paths"]} mitred line paths ({stats["quads"]} quads)', 8000)

    # ------------------------------------------------------------------ projects
    def _confirm_discard(self):
        if not self.doc.is_dirty():
            return True
        r = QtWidgets.QMessageBox.question(
            self, 'Unsaved changes', 'Save the project before continuing?',
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        if r == QtWidgets.QMessageBox.Save:
            return self.save_project()
        return r == QtWidgets.QMessageBox.Discard

    def new_project(self):
        if not self._confirm_discard():
            return
        self.canvas.reset_interaction()
        self.doc.reset()
        self.state.background = None
        self.state.neighbours.clear()
        self.state.emit('refs')
        self.project_path = None
        self._update_title()

    def open_project(self, path=None):
        if not self._confirm_discard():
            return
        path = path or self._ask_file('Open project', 'Buckshot 3 project (*.bs3);;All files (*)')
        if not path:
            return
        try:
            layers, channels, names, refs, data = project_io.load_project(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Open failed', str(e))
            return
        self.canvas.reset_interaction()
        self.doc.reset(layers, channels, names)
        st = self.state
        st.background = None
        st.neighbours.clear()
        st.last_mesh_settings = data.get('mesh_settings')
        view = data.get('view', {})
        if view.get('snap') in SNAP_AMOUNTS:
            self.snap_combo.setCurrentIndex(SNAP_AMOUNTS.index(view['snap']))
        problems = []
        for r in refs:
            try:
                if r['kind'] == 'bin':
                    self._place_bin_neighbour(r['slot'], r['path'], r.get('resolution', 2048))
                else:
                    ref = ImageRef(project_io.load_image(r['image']), r.get('label', ''),
                                   None if r['kind'] == 'mesh' else r['image'])
                    if r['slot'] == 'C':
                        st.background = ref
                    else:
                        st.neighbours[r['slot']] = Neighbour(r['slot'], r['kind'], ref, settings=r.get('settings', {}))
                        st.neighbours[r['slot']].compute_edge_points()
            except Exception as e:
                problems.append(f'{r.get("slot")}: {e}')
        st.emit('refs')
        st.emit('names')
        self.project_path = path
        st.last_dir = os.path.dirname(path)
        self._update_title()
        if problems:
            QtWidgets.QMessageBox.warning(self, 'Some references were not loaded', '\n'.join(problems))

    def save_project(self):
        if not self.project_path:
            return self.save_project_as()
        try:
            project_io.save_project(self.project_path, self.doc, self.state)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Save failed', str(e))
            return False
        self.doc.mark_saved()
        self.statusBar().showMessage(f'Saved {os.path.basename(self.project_path)}', 4000)
        return True

    def save_project_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save project', self.state.last_dir,
                                                        'Buckshot 3 project (*.bs3)')
        if not path:
            return False
        if not path.lower().endswith('.bs3'):
            path += '.bs3'
        self.project_path = path
        return self.save_project()

    def closeEvent(self, e):
        if self._confirm_discard():
            e.accept()
        else:
            e.ignore()
