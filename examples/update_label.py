from qtpy import QtWidgets as QtW
from qt_asyncio import qasync, qcallback
import time

class MyWidget(QtW.QWidget):
    def __init__(self):
        super().__init__()
        self._label = QtW.QLabel("Not started")
        self._btn = QtW.QPushButton("Click me")
        self._btn.clicked.connect(self.btn_clicked.start)
        _layout = QtW.QVBoxLayout()
        _layout.addWidget(self._label)
        _layout.addWidget(self._btn)
        self.setLayout(_layout)

    @qasync
    async def btn_clicked(self, v: bool = False):
        for i in range(10):
            time.sleep(0.1)
            await self.set_label(f"t = {i}")
        await self.set_label("Done!")

    @qcallback
    def set_label(self, text: str):
        self._label.setText(text)

if __name__ == "__main__":
    app = QtW.QApplication([])
    w = MyWidget()
    w.show()
    app.exec_()
