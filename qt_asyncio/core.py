from __future__ import annotations

from typing import Coroutine, Callable, TypeVar
from typing_extensions import ParamSpec
from inspect import iscoroutinefunction
from qt_asyncio._coroutine import QtAsyncFunction
from qt_asyncio._callback import Callback

_P = ParamSpec("_P")
_R = TypeVar("_R")
_Y = TypeVar("_Y")


def qasync(f: Callable[_P, Coroutine[_Y, _R, _P]]) -> QtAsyncFunction[_P, _R, _Y]:
    """
    Convert an async function into a qasync function.

    A superqt worker will be created inside the qasync function and the function

    Examples
    --------
    >>> @qasync
    >>> async def main():
    ...     await other_qasync_func()
    ...     await some_qcallback()  # see @qcallback
    """
    if not iscoroutinefunction(f):
        raise TypeError(f"{f} is not a async function.")
    return QtAsyncFunction(f)


def qcallback(f: Callable[_P, _R]) -> Callback[_P, _R]:
    """
    Convert a sync function into a callback.

    All the functions that updates the GUI should be wrapped with this and called
    with ``await`` inside a qasync function.

    Examples
    --------
    >>> label = QtW.QLabel()
    >>> @qcallback
    >>> def set_label(text: str):
    ...     label.setText(text)

    >>> @qasync
    >>> async def update_label():
    ...      for i in range(10):
    ...          await set_label(f"t = {i}")
    """
    if not callable(f):
        raise TypeError(f"{f} is not callable.")
    elif iscoroutinefunction(f):
        raise TypeError(f"Cannot convert an async function {f!r} into a Qt callback.")
    return Callback(f)
