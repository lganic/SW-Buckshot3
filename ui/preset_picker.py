"""
Searchable, scrollable popup for picking a mesh placement preset.

Presets are named '<Building>: <tile>[ #n]'. They're shown grouped by building in a
tree (groups keep the order they appear in PRESETS), and the search box filters by
every word typed, so 'bridge 10_11' or 'hangar arid 19' narrow it down quickly.
"""
from PySide6 import QtCore, QtGui, QtWidgets

NAME_ROLE = QtCore.Qt.UserRole        # full preset name (leaves only)
SEARCH_ROLE = QtCore.Qt.UserRole + 1  # lower-cased text the search matches against

_NAV_KEYS = (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
_ENTER_KEYS = (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)


class PresetPicker(QtWidgets.QFrame):
    """Popup with a search box over a grouped list of presets. Emits `picked(name)`."""

    picked = QtCore.Signal(str)

    def __init__(self, presets, parent=None):
        super().__init__(parent, QtCore.Qt.Popup)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText('Search presets, e.g. "hangar arid 19"')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        self.search.installEventFilter(self)
        lay.addWidget(self.search)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tree.itemClicked.connect(self._choose)
        self.tree.itemActivated.connect(self._choose)
        lay.addWidget(self.tree, 1)

        self.count = QtWidgets.QLabel()
        self.count.setStyleSheet('color: palette(mid);')
        lay.addWidget(self.count)

        self.total = len(presets)
        groups = {}
        for name, ((x, y, z), yaw) in presets.items():
            group, _, rest = name.partition(': ')
            if not rest:
                group, rest = 'Other', name
            top = groups.get(group)
            if top is None:
                top = groups[group] = QtWidgets.QTreeWidgetItem(self.tree, [group])
                top.setFlags(QtCore.Qt.ItemIsEnabled)
            leaf = QtWidgets.QTreeWidgetItem(top, [rest])
            leaf.setData(0, NAME_ROLE, name)
            leaf.setData(0, SEARCH_ROLE, name.lower())
            leaf.setToolTip(0, f'{name}\nX {x:g}   Height {y:g}   Z {z:g}   Yaw {yaw:g}°')
        bold = self.tree.font()
        bold.setBold(True)
        for top in groups.values():
            top.setText(0, f'{top.text(0)}  ({top.childCount()})')
            top.setFont(0, bold)

        self._filter('')
        self.resize(440, 520)

    # ------------------------------------------------------------ showing
    def popup(self, anchor: QtWidgets.QWidget):
        """Show below `anchor` (flipped above / nudged sideways to stay on screen)."""
        screen = (anchor.screen() or QtGui.QGuiApplication.primaryScreen()).availableGeometry()
        below = anchor.mapToGlobal(QtCore.QPoint(0, anchor.height()))
        x = min(max(below.x(), screen.left()), screen.right() - self.width())
        y = below.y()
        if y + self.height() > screen.bottom():
            y = max(screen.top(), anchor.mapToGlobal(QtCore.QPoint(0, 0)).y() - self.height())
        self.move(x, y)
        self.show()
        self.search.setFocus()
        self.search.selectAll()   # keep the last search, but typing replaces it

    # ------------------------------------------------------------ filtering
    def _filter(self, text):
        tokens = text.lower().split()
        first, shown = None, 0
        self.tree.setUpdatesEnabled(False)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            any_vis = False
            for j in range(top.childCount()):
                leaf = top.child(j)
                hay = leaf.data(0, SEARCH_ROLE)
                vis = all(t in hay for t in tokens)
                leaf.setHidden(not vis)
                if vis:
                    any_vis = True
                    shown += 1
                    if first is None:
                        first = leaf
            top.setHidden(not any_vis)
            top.setExpanded(bool(tokens) and any_vis)
        self.tree.setUpdatesEnabled(True)

        if tokens:
            self.count.setText(f'{shown} of {self.total} presets' if shown else 'No presets match')
            if first is not None:
                self.tree.setCurrentItem(first)
                self.tree.scrollToItem(first)
        else:
            self.count.setText(f'{self.total} presets in {self.tree.topLevelItemCount()} groups')
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
            self.tree.scrollToTop()

    # ------------------------------------------------------------ choosing
    def _choose(self, item):
        if item is None or not self.isVisible():
            return
        name = item.data(0, NAME_ROLE)
        if name is None:  # a group header: open / close it
            item.setExpanded(not item.isExpanded())
            return
        self.hide()
        self.picked.emit(name)

    def eventFilter(self, obj, ev):
        # Arrow keys / Enter in the search box drive the list, so you never need to
        # leave the keyboard: type, arrow to the one you want, press Enter.
        if obj is self.search and ev.type() == QtCore.QEvent.KeyPress:
            if ev.key() in _NAV_KEYS:
                QtWidgets.QApplication.sendEvent(
                    self.tree, QtGui.QKeyEvent(ev.type(), ev.key(), ev.modifiers(), ev.text()))
                return True
            if ev.key() in _ENTER_KEYS:
                self._choose(self.tree.currentItem())
                return True
        return super().eventFilter(obj, ev)
