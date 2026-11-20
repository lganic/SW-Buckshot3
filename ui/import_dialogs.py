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

    def __init__(self, parent=None, show_blank=False):
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
             'Open a map geometry tile to edit, or place it above / below / beside your tile '
             'so you can line things up across tiles.'),
            ('image', 'Reference image',
             'Use any picture as the reference for the centre tile or a neighbour slot.'),
        ]
        if show_blank:
            options.append(('blank', 'Start from scratch', 'An empty tile. You can import references later (Ctrl+I).'))
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
        self.lines = QtWidgets.QCheckBox('Import its lines as editable lines')
        self.lines.setChecked(True)
        form.addRow('', self.lines)
        lay.addLayout(form)
        lay.addWidget(QtWidgets.QLabel('Where should it go?'))
        self.picker = PlacementPicker(state, 'C')
        lay.addWidget(self.picker, 0, QtCore.Qt.AlignHCenter)
        self.note = QtWidgets.QLabel()
        self.note.setWordWrap(True)
        lay.addWidget(self.note)
        self.doc_empty = doc_empty
        self.picker.changed.connect(self._update)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.button(QtWidgets.QDialogButtonBox.Ok).setText('Import')
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self._update(self.picker.slot())

    def _update(self, slot):
        centre = slot == 'C'
        self.res.setEnabled(not centre)
        self.lines.setEnabled(centre)
        if centre:
            msg = 'Loads the tile into the editor.'
            if not self.doc_empty:
                msg += ' <b>This replaces the tile you are editing</b> (save first if needed).'
        else:
            msg = 'Shown as a read-only neighbour. Its border vertices become snap points (yellow diamonds).'
        self.note.setText(msg)


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
