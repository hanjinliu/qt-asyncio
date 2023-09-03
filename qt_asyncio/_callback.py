from __future__ import annotations

import time
from functools import partial, wraps
from typing import (
    Any,
    Callable,
    Literal,
    TypeVar,
    Generic,
    overload,
)
from typing_extensions import ParamSpec


_P = ParamSpec("_P")
_R = TypeVar("_R")

_NULL = object()


class AwaitableCallback(Generic[_P, _R]):
    def __init__(self, f: Callable[_P, _R]):
        self._func = f
        wraps(f)(self)
        self._result = _NULL

    def __repr__(self):
        if isinstance(self._func, partial):
            a = ", ".join(map(repr, self._func.args))
            k = ", ".join(f"{k}={v!r}" for k, v in self._func.keywords.items())
            return f"{self.__class__.__name__}<{self._func.func!r}({a}, {k})>"
        return f"{self.__class__.__name__}<{self._func!r}()>"

    def run(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        assert self._result is _NULL
        out = self._func(*args, **kwargs)
        self._result = out
        return out

    def with_args(self, *args: _P.args, **kwargs: _P.kwargs) -> AwaitableCallback[[], _R]:
        """Return a partial callback."""
        return self.__class__(partial(self._func, *args, **kwargs))

    def __call__(self, *args, **kwargs) -> CallbackTask[_R]:
        return CallbackTask(self.with_args(*args, **kwargs))

    def copy(self) -> AwaitableCallback[_P, _R]:
        """Return a copy of the callback."""
        return self.__class__(self._func)

    def await_call(self, timeout: float = -1) -> _R:
        """
        Await the callback to be called.

        Usage
        -----
        >>> cb = thread_worker.callback(func)
        >>> yield cb
        >>> cb.await_call()  # stop here until callback is called
        """
        if timeout <= 0:
            while self._result is _NULL:
                time.sleep(0.01)
            return self.unwrap()
        t0 = time.time()
        while self._result is _NULL:
            time.sleep(0.01)
            if time.time() - t0 > timeout:
                raise TimeoutError(f"Callback {self} did not finish within {timeout} seconds.")
        return self.unwrap()

    def unwrap(self) -> _R:
        """Unwrap the callback."""
        if self._result is _NULL:
            raise RuntimeError("Callback has not been called.")
        return self._result


class Callback(AwaitableCallback[_P, _R]):
    """Callback object that can be recognized by thread_worker."""

    @overload
    def __get__(self, obj: Any, type=None) -> Callback[..., _R]:
        ...

    @overload
    def __get__(self, obj: Literal[None], type=None) -> Callback[_P, _R]:
        ...

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return self.__class__(partial(self._func, obj))

    def with_args(self, *args: _P.args, **kwargs: _P.kwargs) -> Callback[[], _R]:
        """Return a partial callback."""
        return self.__class__(partial(self._func, *args, **kwargs))

    @classmethod
    def empty(cls) -> Callback[[], None]:
        """An empty callback."""
        return cls(lambda: None)


class NestedCallback(AwaitableCallback[_P, _R]):
    def with_args(self, *args: _P.args, **kwargs: _P.kwargs) -> NestedCallback[_P, _R]:
        """Return a partial callback."""
        return self.__class__(partial(self._func, *args, **kwargs))

    @classmethod
    def from_arg(cls, arg: _R) -> NestedCallback[[], _R]:
        return cls(unwrap_value).with_args(arg)


class CallbackTask(Generic[_R]):
    """A class to make the syntax of thread_worker and Callback similar."""

    def __init__(self, callback: Callback[[], _R]):
        self._callback = callback

    def __await__(self):
        yield self._callback
        return self._callback.await_call()


def unwrap_value(out: Any | None):
    if isinstance(out, AwaitableCallback):
        out.run()
        return out._result
    else:
        return out
