[![PyPI - Version](https://img.shields.io/pypi/v/qt-asyncio.svg)](https://pypi.org/project/qt-asyncio)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qt-asyncio.svg)](https://pypi.org/project/qt-asyncio)

# qt_asyncio

A concise solution for using async/await syntax with Qt.

-----

**Table of Contents**

- [qt\_asyncio](#qt_asyncio)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
  - [License](#license)

## Installation

```console
pip install qt-asyncio
```

## Basic Usage

`@qasync` for Qt-compatible async functions and `@qcallback` for the functions that update the GUI. Use `start` method to start the worker of the qasync function.

```python
import time
from qtpy.QtWidgets import QPushButton
from qt_asyncio import qasync, qcallback

btn = QPushButton("Start")
@qcallback
def update_btn_text(text: str):
    btn.setText(text)

@qasync
async def on_clicked(_=None):
    for i in range(10):
        time.sleep(0.1)
        await update_btn_text(f"t = {i}")
    await update_btn_text("Finished")

btn.clicked.connect(on_clicked.start)
btn.show()
```

See the /examples folder for the detailed usage.

## License

`qt-asyncio` is distributed under the terms of the [BSD 3-Clause](https://spdx.org/licenses/BSD 3-Clause.html) license.
