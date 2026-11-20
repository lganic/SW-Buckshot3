"""Buckshot 3 entry point."""
import sys

from PySide6 import QtCore, QtGui, QtWidgets


def dark_palette(app):
    app.setStyle('Fusion')
    p = QtGui.QPalette()
    c = QtGui.QColor
    p.setColor(QtGui.QPalette.Window, c(37, 40, 46))
    p.setColor(QtGui.QPalette.WindowText, c(225, 228, 234))
    p.setColor(QtGui.QPalette.Base, c(28, 31, 36))
    p.setColor(QtGui.QPalette.AlternateBase, c(42, 46, 53))
    p.setColor(QtGui.QPalette.ToolTipBase, c(50, 54, 62))
    p.setColor(QtGui.QPalette.ToolTipText, c(230, 230, 230))
    p.setColor(QtGui.QPalette.Text, c(225, 228, 234))
    p.setColor(QtGui.QPalette.PlaceholderText, c(120, 126, 136))
    p.setColor(QtGui.QPalette.Button, c(48, 52, 60))
    p.setColor(QtGui.QPalette.ButtonText, c(225, 228, 234))
    p.setColor(QtGui.QPalette.Highlight, c(66, 133, 214))
    p.setColor(QtGui.QPalette.HighlightedText, c(255, 255, 255))
    p.setColor(QtGui.QPalette.Link, c(110, 170, 255))
    for role in (QtGui.QPalette.Text, QtGui.QPalette.ButtonText, QtGui.QPalette.WindowText):
        p.setColor(QtGui.QPalette.Disabled, role, c(115, 120, 130))
    app.setPalette(p)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QtWidgets.QApplication(argv)
    app.setApplicationName('Buckshot 3')
    dark_palette(app)

    from .ui.main_window import MainWindow
    w = MainWindow()
    w.resize(1500, 920)
    w.show()

    path = next((a for a in argv[1:] if not a.startswith('-')), None)
    if path and path.lower().endswith('.bs3'):
        QtCore.QTimer.singleShot(0, lambda: w.open_project(path))
    elif path and path.lower().endswith('.bin'):
        QtCore.QTimer.singleShot(0, lambda: w.import_bin(path))
    return app.exec()
