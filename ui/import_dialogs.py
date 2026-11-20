"""Import screen, placement picker, and the .bin / image import dialogs."""
import os

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import SLOT_GRID, SLOT_NAMES


class PlacementPicker(QtWidgets.QWidget):
    """3 x 3 grid: the centre is the editable tile, the rest are neighbour slots."""

    changed = QtCore.Signal(str)

    def __init__(self, state, default='C', allow_center=True):
        super().__init__()
        grid = QtWidgets.QGridLayout(self)
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        self.group = QtWidgets.QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for r, row in enumerate(SLOT_GRID):
            for c, slot in enumerate(row):
                b = QtWidgets.QToolButton()
                b.setCheckable(True)
                b.setFixedSize(78, 54)
                occupant = None
                if slot == 'C':
                    occupant = 'your tile'
                elif slot in state.neighbours:
                    occupant = state.neighbours[slot].image.label
                text = 'EDIT\ntile' if slot == 'C' else slot
                if occupant and slot != 'C':
                    text += '\n(replace)'
                b.setText(text)
                b.setToolTip(SLOT_NAMES[slot] + (f'\nCurrently: {occupant}' if occupant else ''))
                if slot == 'C':
                    b.setStyleSheet('QToolButton { font-weight: bold; }')
                    b.setEnabled(allow_center)
                self.group.addButton(b)
                self.buttons[slot] = b
                grid.addWidget(b, r, c)
                b.toggled.connect(lambda on, s=slot: on and self.changed.emit(s))
        if not allow_center and default == 'C':
            default = 'N'
        self.buttons[default].setChecked(True)

    def slot(self):
        for s, b in self.buttons.items():
            if b.isChecked():
                return s
        return 'C'


class ImportScreen(QtWidgets.QDialog):
    """Pick what to bring in. Returns choice() in {'mesh', 'bin', 'image', 'blank'}."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Buckshot 3 - Import')
        self._choice = None
        lay = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel('<h2>Import</h2>What do you want to bring into Buckshot?')
        lay.addWidget(title)
        options = [
            ('mesh', 'Render .mesh files',
             'Render one or more Stormworks meshes (with offsets / rotation) into a reference '
             'image, and generate shoreline, height and undersea lines from them.'),
            ('bin', 'Map tile (.bin)',
             'Open a map geometry tile to edit, import just its lines into your tile, or place it '
             'above / below / beside your tile so you can line things up across tiles.'),
            ('image', 'Reference image',
             'Use any picture as the reference for the centre tile or a neighbour slot.'),
        ]
        for key, head, desc in options:
            b = QtWidgets.QPushButton()
            b.setMinimumHeight(66)
            b.setStyleSheet('QPushButton { text-align: left; padding: 8px 14px; }')
            lab = QtWidgets.QLabel(f'<b style="font-size:13pt">{head}</b><br>{desc}')
            lab.setWordWrap(True)
            lab.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            inner = QtWidgets.QHBoxLayout(b)
            inner.setContentsMargins(12, 6, 12, 6)
            inner.addWidget(lab)
            b.clicked.connect(lambda _=False, k=key: self._pick(k))
            lay.addWidget(b)
        cancel = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        cancel.rejected.connect(self.reject)
        lay.addWidget(cancel)
        self.resize(560, 100)

    def _pick(self, k):
        self._choice = k
        self.accept()

    def choice(self):
        return self._choice


class BinImportDialog(QtWidgets.QDialog):

    def __init__(self, parent, state, path, tiledata, doc_empty):
        super().__init__(parent)
        self.setWindowTitle(f'Import {os.path.basename(path)}')
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(QtWidgets.QLabel(
            f'<b>{os.path.basename(path)}</b><br>{tiledata.tri_count()} triangles, '
            f'{tiledata.line_count()} line quads'))
        form = QtWidgets.QFormLayout()
        self.res = QtWidgets.QSpinBox()
        self.res.setRange(256, 16384)
        self.res.setSingleStep(256)
        self.res.setValue(2048)
        self.res.setSuffix(' px')
        self.res.setToolTip('Resolution the tile is rendered at when shown as a neighbour')
        form.addRow('Render resolution', self.res)
        lay.addLayout(form)
        lay.addWidget(QtWidgets.QLabel('Where should it go?'))
        self.picker = PlacementPicker(state, 'C')
        lay.addWidget(self.picker, 0, QtCore.Qt.AlignHCenter)

        self.centre_box = QtWidgets.QGroupBox('Into your tile')
        cb = QtWidgets.QVBoxLayout(self.centre_box)
        self.mode_replace = QtWidgets.QRadioButton('Replace the tile (geometry and lines)')
        self.mode_lines = QtWidgets.QRadioButton('Lines only (keep the current map geometry)')
        self.mode_replace.setChecked(True)
        self.mode_group = QtWidgets.QButtonGroup(self)
        self.mode_group.addButton(self.mode_replace)
        self.mode_group.addButton(self.mode_lines)
        self.lines = QtWidgets.QCheckBox('Import its lines as editable lines')
        self.lines.setChecked(True)
        self.clear_lines = QtWidgets.QCheckBox('Clear existing lines first')
        self.clear_lines.setToolTip('Remove every line in all channels before adding the imported ones')
        cb.addWidget(self.mode_replace)
        cb.addWidget(_indented(self.lines))
        cb.addWidget(self.mode_lines)
        cb.addWidget(_indented(self.clear_lines))
        lay.addWidget(self.centre_box)

        self.note = QtWidgets.QLabel()
        self.note.setWordWrap(True)
        lay.addWidget(self.note)
        self.doc_empty = doc_empty
        self.picker.changed.connect(self._update)
        self.mode_lines.toggled.connect(lambda _on: self._update(self.picker.slot()))
        self.clear_lines.toggled.connect(lambda _on: self._update(self.picker.slot()))
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.button(QtWidgets.QDialogButtonBox.Ok).setText('Import')
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self._update(self.picker.slot())

    def _update(self, slot):
        centre = slot == 'C'
        lines_only = self.mode_lines.isChecked()
        self.res.setEnabled(not centre)
        self.centre_box.setEnabled(centre)
        self.lines.setEnabled(not lines_only)
        self.clear_lines.setEnabled(lines_only)
        if centre and lines_only:
            msg = 'Adds its lines to your tile. Your map geometry is left as it is.'
            if self.clear_lines.isChecked():
                msg += ' Existing lines are removed first.'
            msg += ' (Ctrl+Z undoes this.)'
        elif centre:
            msg = 'Loads the tile into the editor.'
            if not self.doc_empty:
                msg += ' <b>This replaces the tile you are editing</b> (save first if needed).'
        else:
            msg = 'Shown as a read-only neighbour. Its border vertices become snap points (yellow diamonds).'
        self.note.setText(msg)

    def lines_only(self):
        return self.picker.slot() == 'C' and self.mode_lines.isChecked()


def _indented(widget, px=22):
    w = QtWidgets.QWidget()
    h = QtWidgets.QHBoxLayout(w)
    h.setContentsMargins(px, 0, 0, 0)
    h.addWidget(widget)
    return w


class ImageImportDialog(QtWidgets.QDialog):

    def __init__(self, parent, state, path):
        super().__init__(parent)
        self.setWindowTitle(f'Import {os.path.basename(path)}')
        lay = QtWidgets.QVBoxLayout(self)
        pm = QtGui.QPixmap(path)
        prev = QtWidgets.QLabel()
        prev.setPixmap(pm.scaled(220, 220, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        prev.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(prev)
        lay.addWidget(QtWidgets.QLabel('The image is stretched over the whole 1000 m tile. Where should it go?'))
        self.picker = PlacementPicker(state, 'C')
        lay.addWidget(self.picker, 0, QtCore.Qt.AlignHCenter)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
