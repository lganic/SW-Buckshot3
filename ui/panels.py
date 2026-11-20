"""Side panels: layer list, line channel list, and reference / display settings."""
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import RENDER_ORDER, LAYER_COLORS, CHANNEL_COLORS, NUM_CHANNELS, SLOT_NAMES
from .stack_view import StackView
from .render_view import RenderView


def swatch(color: QtGui.QColor, size=14) -> QtGui.QIcon:
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 140), 1))
    p.setBrush(color)
    p.drawRoundedRect(QtCore.QRectF(0.5, 0.5, size - 1, size - 1), 3, 3)
    p.end()
    return QtGui.QIcon(pm)


class LayerList(QtWidgets.QTreeWidget):
    """Layers listed top-most first (the reverse of draw order), like an image editor."""

    def __init__(self, doc, state):
        super().__init__()
        self.doc, self.state = doc, state
        self.setHeaderLabels(['Layer (top drawn last)', 'Tris'])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.items = {}
        self._sync = False
        for i, name in reversed(list(enumerate(RENDER_ORDER))):
            it = QtWidgets.QTreeWidgetItem([f'{i + 1:>2}. {name}', '0'])
            it.setIcon(0, swatch(QtGui.QColor(*LAYER_COLORS[name])))
            it.setFlags(it.flags() | QtCore.Qt.ItemIsUserCheckable)
            it.setCheckState(0, QtCore.Qt.Checked)
            it.setData(0, QtCore.Qt.UserRole, name)
            it.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            it.setToolTip(0, 'Tick to show / hide. Click to edit this layer.')
            self.addTopLevelItem(it)
            self.items[name] = it
        self.itemChanged.connect(self._on_item_changed)
        self.currentItemChanged.connect(self._on_current)
        doc.changed.connect(lambda _k: self.refresh())
        state.changed.connect(lambda _w: self.refresh())
        self.refresh()

    def refresh(self):
        self._sync = True
        for name, it in self.items.items():
            n = len(self.doc.layers[name].polys)
            it.setText(1, str(n))
            it.setForeground(0, self.palette().color(QtGui.QPalette.Text if n else QtGui.QPalette.PlaceholderText))
            it.setCheckState(0, QtCore.Qt.Checked if self.state.layer_visible[name] else QtCore.Qt.Unchecked)
        cur = self.items[self.state.active_layer]
        if self.currentItem() is not cur:
            self.setCurrentItem(cur)
        self._sync = False

    def _on_item_changed(self, it, col):
        if self._sync:
            return
        name = it.data(0, QtCore.Qt.UserRole)
        vis = it.checkState(0) == QtCore.Qt.Checked
        if self.state.layer_visible[name] != vis:
            self.state.layer_visible[name] = vis
            self.state.emit('visibility')

    def _on_current(self, cur, _prev):
        if self._sync or cur is None:
            return
        self.state.set_active_layer(cur.data(0, QtCore.Qt.UserRole))


class ChannelList(QtWidgets.QTreeWidget):

    def __init__(self, doc, state):
        super().__init__()
        self.doc, self.state = doc, state
        self.setHeaderLabels(['Line channel (double-click to rename)', 'Edges'])
        self.setRootIsDecorated(False)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self._sync = False
        self.items = []
        for ch in range(NUM_CHANNELS):
            it = QtWidgets.QTreeWidgetItem([doc.channel_names[ch], '0'])
            it.setIcon(0, swatch(QtGui.QColor(CHANNEL_COLORS[ch])))
            it.setFlags(it.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
            it.setCheckState(0, QtCore.Qt.Checked)
            it.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.addTopLevelItem(it)
            self.items.append(it)
        self.itemChanged.connect(self._on_item_changed)
        self.currentItemChanged.connect(self._on_current)
        doc.changed.connect(lambda _k: self.refresh())
        state.changed.connect(lambda _w: self.refresh())
        self.refresh()

    def refresh(self):
        self._sync = True
        for ch, it in enumerate(self.items):
            n = len(self.doc.channels[ch].polys)
            it.setText(0, self.doc.channel_names[ch])
            it.setText(1, str(n))
            it.setCheckState(0, QtCore.Qt.Checked if self.state.channel_visible[ch] else QtCore.Qt.Unchecked)
        cur = self.items[self.state.active_channel]
        if self.currentItem() is not cur:
            self.setCurrentItem(cur)
        self._sync = False

    def _on_item_changed(self, it, col):
        if self._sync:
            return
        ch = self.items.index(it)
        vis = it.checkState(0) == QtCore.Qt.Checked
        name = it.text(0).strip() or f'Channel {ch + 1}'
        if name != self.doc.channel_names[ch]:
            self.doc.channel_names[ch] = name
            self.state.emit('names')
        if self.state.channel_visible[ch] != vis:
            self.state.channel_visible[ch] = vis
            self.state.emit('visibility')

    def _on_current(self, cur, _prev):
        if self._sync or cur is None:
            return
        self.state.set_active_channel(self.items.index(cur))


class LayersPanel(QtWidgets.QWidget):
    """Exploded stack or flat render on top (switchable), then the layer / channel lists
    (tab follows the edit mode)."""

    def __init__(self, doc, state, paths, canvas=None):
        super().__init__()
        self.state = state
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        # view switch + render options
        bar = QtWidgets.QHBoxLayout()
        bar.setSpacing(2)
        self.view_group = QtWidgets.QButtonGroup(self)
        self.view_group.setExclusive(True)
        for i, (label, tip) in enumerate([('Layers', 'Exploded layer stack (click a sheet to edit it)'),
                                          ('Render', 'The finished tile, flat, as it will be exported')]):
            b = QtWidgets.QToolButton()
            b.setText(label)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            b.setMinimumWidth(64)
            self.view_group.addButton(b, i)
            bar.addWidget(b)
        bar.addStretch(1)

        self.render_opts = QtWidgets.QWidget()
        ol = QtWidgets.QHBoxLayout(self.render_opts)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(2)
        bar.addWidget(self.render_opts)
        lay.addLayout(bar)

        self.views = QtWidgets.QStackedWidget()
        self.stack = StackView(doc, state, paths)
        self.render = RenderView(doc, state, paths, canvas)
        self.views.addWidget(self.stack)
        self.views.addWidget(self.render)
        lay.addWidget(self.views, 3)

        for attr, label, tip in [('show_lines', 'Lines', 'Draw the line channels'),
                                 ('show_neighbours', 'Tiles', 'Show neighbour tiles around this one'),
                                 ('show_reference', 'Ref', 'Overlay the reference image at 50%'),
                                 ('show_viewport', 'View', "Outline the editor's current view")]:
            b = QtWidgets.QToolButton()
            b.setText(label)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setChecked(getattr(self.render, attr))
            b.toggled.connect(lambda v, a=attr: self.render.set_option(a, v))
            ol.addWidget(b)
        fit = QtWidgets.QToolButton()
        fit.setText('Fit')
        fit.setToolTip('Zoom the render back out to fit the tile (or middle-click the render)')
        fit.clicked.connect(self.render.fit)
        ol.addWidget(fit)

        self.setStyleSheet('QToolButton { padding: 2px 6px; border: 1px solid transparent; border-radius: 3px; }'
                           'QToolButton:hover { border-color: #5a6270; }'
                           'QToolButton:checked { background: #2f5687; border-color: #4285d6; color: white; }')
        self.view_group.idClicked.connect(self.set_view)
        self.set_view(0)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(LayerList(doc, state), 'Geometry layers')
        self.tabs.addTab(ChannelList(doc, state), 'Line channels')
        lay.addWidget(self.tabs, 2)
        self.tabs.currentChanged.connect(lambda i: state.set_mode('geometry' if i == 0 else 'lines'))
        state.changed.connect(self._on_state)

    def set_view(self, i):
        self.views.setCurrentIndex(i)
        self.view_group.button(i).setChecked(True)
        self.render_opts.setVisible(i == 1)

    def toggle_view(self):
        self.set_view(1 - self.views.currentIndex())

    def _on_state(self, what):
        want = 0 if self.state.mode == 'geometry' else 1
        if self.tabs.currentIndex() != want:
            self.tabs.setCurrentIndex(want)


def _slider(value, tip):
    s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    s.setRange(0, 100)
    s.setValue(int(value * 100))
    s.setToolTip(tip)
    return s


class ReferencePanel(QtWidgets.QWidget):
    """Opacity controls plus the list of reference images / neighbour tiles."""

    importRequested = QtCore.Signal()

    def __init__(self, state):
        super().__init__()
        self.state = state
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)

        form = QtWidgets.QFormLayout()
        for attr, label, tip in [
            ('fill_opacity', 'Geometry fill', 'Opacity of the geometry layers'),
            ('inactive_opacity', 'Other layers', 'Opacity of layers you are not editing (geometry mode)'),
            ('background_opacity', 'Reference image', 'Opacity of the centre tile reference image'),
            ('neighbour_opacity', 'Neighbour tiles', 'Opacity of neighbouring tiles'),
        ]:
            s = _slider(getattr(state, attr), tip)
            s.valueChanged.connect(lambda v, a=attr: (setattr(state, a, v / 100), state.emit('view')))
            form.addRow(label, s)
        lay.addLayout(form)

        for attr, label in [('show_grid', 'Show snap grid'),
                            ('show_lines_in_geometry', 'Show lines in geometry mode'),
                            ('show_geometry_in_lines', 'Show geometry in lines mode')]:
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(getattr(state, attr))
            cb.toggled.connect(lambda v, a=attr: (setattr(state, a, v), state.emit('view')))
            lay.addWidget(cb)

        lay.addWidget(QtWidgets.QLabel('<b>References</b>'))
        self.list = QtWidgets.QListWidget()
        self.list.setMinimumHeight(90)
        lay.addWidget(self.list, 1)
        row = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton('Import…')
        add.clicked.connect(self.importRequested)
        self.remove = QtWidgets.QPushButton('Remove')
        self.remove.clicked.connect(self._remove)
        row.addWidget(add)
        row.addWidget(self.remove)
        lay.addLayout(row)
        state.changed.connect(lambda w: self.refresh() if w == 'refs' else None)
        self.refresh()

    def refresh(self):
        self.list.clear()
        st = self.state
        if st.background is not None:
            it = QtWidgets.QListWidgetItem(f'C · reference image · {st.background.label}')
            it.setData(QtCore.Qt.UserRole, 'C')
            self.list.addItem(it)
        for slot in ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']:
            nb = st.neighbours.get(slot)
            if nb:
                it = QtWidgets.QListWidgetItem(f'{slot} · {nb.kind} · {nb.image.label}')
                it.setToolTip(SLOT_NAMES[slot])
                it.setData(QtCore.Qt.UserRole, slot)
                self.list.addItem(it)
        if self.list.count() == 0:
            it = QtWidgets.QListWidgetItem('Nothing imported yet')
            it.setFlags(QtCore.Qt.NoItemFlags)
            self.list.addItem(it)
        self.remove.setEnabled(st.background is not None or bool(st.neighbours))

    def _remove(self):
        it = self.list.currentItem()
        if it is None:
            return
        slot = it.data(QtCore.Qt.UserRole)
        if slot == 'C':
            self.state.background = None
        elif slot in self.state.neighbours:
            del self.state.neighbours[slot]
        self.state.emit('refs')
