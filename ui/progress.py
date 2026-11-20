"""Modal progress bar popup for long jobs that run on the GUI thread."""
import time

from PySide6 import QtCore, QtWidgets


class Cancelled(Exception):
    """Raised out of a progress callback once the user has pressed Cancel."""


def subrange(progress, start, end):
    """A progress callback that reports into [start, end] of another one."""
    def report(fraction, text=None):
        progress(start + (end - start) * fraction, text)
    return report


class ProgressPopup(QtWidgets.QDialog):
    """
    Use as a context manager and pass it (or a subrange() of it) to the work as a
    progress callback: progress(fraction 0..1, text=None). Each call moves the
    bar, keeps the app painting, and raises Cancelled if the user cancelled.

    The work runs on the GUI thread (Qt's painting holds the GIL, so a worker
    thread would not keep the UI any livelier), so it must report regularly.
    The popup only appears once a job has run for delay_ms, so quick jobs
    don't flash it; until then user input is held back rather than handled.
    """

    PUMP_INTERVAL = 0.03      # seconds between event-loop pumps

    def __init__(self, parent, title, text='', cancellable=True, delay_ms=200):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        lay = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.label.setMinimumWidth(380)
        lay.addWidget(self.label)
        self.bar = QtWidgets.QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(True)
        self.bar.setFormat('%p%')
        lay.addWidget(self.bar)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.rejected.connect(self.reject)
        lay.addWidget(self.buttons)
        self.setFixedHeight(self.sizeHint().height())

        self.cancelled = False
        self._cancellable = True
        self.set_cancellable(cancellable)
        self._show_at = time.monotonic() + delay_ms / 1000
        self._last_pump = 0.0

    # ---- reporting ----
    def __call__(self, fraction, text=None):
        self.bar.setValue(int(round(max(0.0, min(1.0, fraction)) * 1000)))
        if text is not None:
            self.label.setText(text)
        now = time.monotonic()
        if not self.isVisible() and now >= self._show_at:
            self.show()
            self._pump()
            self._pump()                  # second pass lets the first paint land
        elif now - self._last_pump >= self.PUMP_INTERVAL:
            self._pump()
        if self.cancelled and self._cancellable:
            raise Cancelled()

    def set_cancellable(self, on):
        """Turn Cancel off for a step that must not be interrupted halfway."""
        self._cancellable = on
        self.buttons.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(on and not self.cancelled)

    def _pump(self):
        self._last_pump = time.monotonic()
        flags = QtCore.QEventLoop.AllEvents
        if not self.isVisible():
            flags |= QtCore.QEventLoop.ExcludeUserInputEvents
        QtWidgets.QApplication.processEvents(flags)

    # ---- dialog ----
    def reject(self):
        """Cancel button, Esc or the close box: flag it; the work stops at its next report."""
        if self._cancellable and not self.cancelled:
            self.cancelled = True
            self.label.setText('Cancelling…')
            self.buttons.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)

    def closeEvent(self, e):
        e.ignore()
        self.reject()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.hide()
        self.deleteLater()
        return False
