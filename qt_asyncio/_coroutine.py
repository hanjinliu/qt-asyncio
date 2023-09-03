from __future__ import annotations
from functools import wraps

from typing import (
    Any,
    Callable,
    Generator,
    TypeVar,
    Generic,
    Coroutine,
)
from typing_extensions import ParamSpec
import weakref

from superqt.utils import create_worker, GeneratorWorker, FunctionWorker

from ._callback import NestedCallback, unwrap_value


_P = ParamSpec("_P")
_Y = TypeVar("_Y")
_R = TypeVar("_R")


class Aborted(RuntimeError):
    """Raised when worker is aborted."""

    @classmethod
    def raise_(cls, *args):
        """A function version of "raise"."""
        if not args:
            args = ("Aborted.",)
        raise cls(*args)


class QtFuture(Generic[_R]):
    def __init__(self, cor: QtAsyncFunction[_P, _Y, _R], *args, **kwargs):
        self._async = cor
        self._args = args
        self._kwargs = kwargs

    def __await__(self) -> Generator[_Y, None, _R]:
        gen = self._async._create_generator()
        out = yield from gen(*self._args, **self._kwargs)
        return out

    def start(self):
        cor = self._async
        # create a worker object
        worker = cor._create_qt_worker(*self._args, **self._kwargs)
        cor._bind_callbacks(worker)
        if isinstance(worker, GeneratorWorker):
            worker.aborted.connect(Aborted.raise_)
        worker.start()
        return worker

    def run_blocked(self) -> _R:
        _empty = object()
        result = err = _empty
        worker = self._async._create_qt_worker(*self._args, **self._kwargs)

        @worker.returned.connect
        def _(val):
            nonlocal result
            result = val

        @worker.errored.connect
        def _(exc):
            nonlocal err
            err = exc

        if isinstance(worker, GeneratorWorker):

            @worker.aborted.connect
            def _():
                nonlocal err
                err = Aborted()

        try:
            worker.run()

        except KeyboardInterrupt as e:
            worker.quit()
            worker.finished.emit()
            Aborted.raise_()

        if result is _empty and err is not _empty:
            raise err
        return result


def _coroutine_to_generator(f: Callable[_P, Coroutine[_Y, None, _R]]):
    def new(*args: _P.args, **kwargs: _P.kwargs) -> Generator[_Y, None, _R]:
        cor = f(*args, **kwargs)
        while True:
            try:
                yielded = cor.send(None)
            except StopIteration as e:
                return e.value
            else:
                yield yielded

    return new


class QtAsyncFunction(Generic[_P, _Y, _R]):
    """Create a worker in a superqt/napari style."""

    def __init__(
        self,
        f: Callable[_P, Coroutine[_Y, None, _R]],
        *,
        ignore_errors: bool = False,
    ) -> None:
        self._func = _coroutine_to_generator(f)
        self._ignore_errors = ignore_errors
        self._objects: dict[int, Any] = {}
        self._worker = lambda: None
        wraps(f)(self)

    @property
    def func(self) -> Callable[_P, _R]:
        """The original function."""
        return self._func

    def __call__(self, *args, **kwargs):
        return QtFuture(self, *args, **kwargs)

    def start(self, *args, **kwargs):
        """Create a future object and start the worker."""
        return self(*args, **kwargs).start()

    def __get__(self, obj, objtype=None) -> QtAsyncFunction[_P, _R]:
        if obj is None:
            return self

        gui_id = id(obj)
        if gui_id in self._objects:
            return self._objects[gui_id]

        new = self._objects[gui_id] = self.__class__(
            self._func.__get__(obj),
            ignore_errors=self._ignore_errors,
        )
        return new

    def _create_qt_worker(self, *args, **kwargs) -> FunctionWorker | GeneratorWorker:
        """Create a worker object."""
        worker = create_worker(
            self._func,
            _ignore_errors=self._ignore_errors,
            _start_thread=False,
            *args,
            **kwargs,
        )
        self._worker = weakref.ref(worker)
        return worker

    def _create_generator(self):
        def _gen(*args, **kwargs):
            # run
            gen = self._func(*args, **kwargs)
            _empty = object()
            out: _R = _empty
            while True:
                try:
                    _val = next(gen)
                except StopIteration as exc:
                    out = exc.value
                    break
                else:
                    # yielded
                    ncb = NestedCallback.from_arg(_val)
                    yield ncb
                    ncb.await_call()

            assert out is not _empty
            # returned
            ncb = NestedCallback.from_arg(out)
            yield ncb
            return ncb.await_call()

        return _gen

    def _bind_callbacks(
        self,
        worker: FunctionWorker | GeneratorWorker,
    ):
        # bind callbacks
        is_generator = isinstance(worker, GeneratorWorker)
        worker.returned.connect(unwrap_value)
        if is_generator:
            worker.yielded.connect(unwrap_value)
