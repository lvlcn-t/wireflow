import asyncio
import collections.abc as cabc
import inspect
import typing as t
import warnings
from functools import wraps

from wireflow.dependency import container

T = t.TypeVar("T")
P = t.ParamSpec("P")


class ProvideMeta(type):
    """Metaclass to override the behavior of Provide when it's used as a type hint."""

    def __getitem__(cls, service_cls: type[T]) -> T:
        """When `Provide[T]` is used in type hints, this method is invoked."""
        return cls(service_cls)


class Provide(t.Generic[T], metaclass=ProvideMeta):
    """A generic provider class that will be used to denote that a certain dependency should be injected."""

    def __init__(self, service_cls: type[T]):
        self.service_cls = service_cls

    async def __call__(self) -> T:
        """When an instance of `Provide` is called, it triggers the resolution process."""
        return await container.resolve(self.service_cls)

    def sync_resolve(self) -> T:
        """Resolve the dependency synchronously using the default event loop."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.run_until_complete(self())
            return asyncio.run(self())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self())
            finally:
                loop.close()


def _is_provide_instance(obj: t.Any) -> t.TypeGuard[Provide[t.Any]]:
    return isinstance(obj, Provide)


def inject(func: cabc.Callable[P, T]) -> cabc.Callable[P, T]:
    """Decorator to inject dependencies into a function or method.

    This decorator allows you to automatically inject dependencies into the
    parameters of a function or method. It works by replacing the default
    values of the parameters with instances provided by a dependency injection
    container.

    For example, if you have a class `Service` and you want to inject an
    instance of this class into a function, you can type hint the parameter with
    the `Service` class and set `Provide[Service]` as the default value.
    The `inject` decorator will then replace the default value with an instance
    of the `Service` class provided by the DI container when the function is called.

    Usage:

    - Add your dependencies to the DI container using the `provide` method.
    - Define the dependencies you want to inject using the `Provide` type annotation.
    - Decorate the function with `@inject`.
    """
    if inspect.iscoroutinefunction(func):
        return t.cast(cabc.Callable[P, T], _inject_to_async(func))

    return _inject_to_sync(func)


def _inject_to_async(func: cabc.Callable[P, cabc.Coroutine[t.Any, t.Any, T]]) -> cabc.Callable[P, cabc.Coroutine[t.Any, t.Any, T]]:
    signature = inspect.signature(func)

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        for name, param in signature.parameters.items():
            if not _is_provide_instance(param.default):
                continue
            if name in kwargs:
                raise RuntimeError(f"Injected arguments must not be redefined, {name=}")

            kwargs[name] = await param.default()
            injected = True
        if not injected:
            warnings.warn(
                "Expected injection, but nothing found. Remove @inject decorator.",
                RuntimeWarning,
                stacklevel=1,
            )
        return await func(*args, **kwargs)

    return wrapper


def _inject_to_sync(func: cabc.Callable[P, T]) -> cabc.Callable[P, T]:
    signature = inspect.signature(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        injected = False
        for name, param in signature.parameters.items():
            if not _is_provide_instance(param.default):
                continue
            if name in kwargs:
                raise RuntimeError(f"Injected arguments must not be redefined, {name=}")

            kwargs[name] = param.default.sync_resolve()
            injected = True

        if not injected:
            warnings.warn(
                "Expected injection, but nothing found. Remove @inject decorator.",
                RuntimeWarning,
                stacklevel=1,
            )

        return func(*args, **kwargs)

    return wrapper
