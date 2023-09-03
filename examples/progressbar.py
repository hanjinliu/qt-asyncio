from qtpy import QtWidgets as QtW
from qt_asyncio import qasync, qcallback
import time

class MyWidget(QtW.QWidget):
    def __init__(self):
        super().__init__()
        self._pbar = QtW.QProgressBar()
        self._pbar.setMaximum(100)
        self._btn = QtW.QPushButton("Click me")
        self._btn.clicked.connect(self.btn_clicked.start)
        _layout = QtW.QVBoxLayout()
        _layout.addWidget(self._pbar)
        _layout.addWidget(self._btn)
        self.setLayout(_layout)

    @qasync
    async def btn_clicked(self, v: bool = False):
        """Start updating the progress bar."""
        await self.initialize()
        for _ in range(100):
            time.sleep(0.01)
            await self.increment()
        await self.increment()

    @qcallback
    def initialize(self):
        """Initialize the progress bar."""
        self._pbar.setValue(0)

    @qcallback
    def increment(self):
        """Increment the progress bar."""
        value = self._pbar.value()
        self._pbar.setValue(value + 1)

if __name__ == "__main__":
    app = QtW.QApplication([])
    w = MyWidget()
    w.show()
    app.exec_()
