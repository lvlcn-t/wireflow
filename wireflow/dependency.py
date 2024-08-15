from __future__ import annotations

import abc
import asyncio
import collections.abc as cabc
import inspect
import typing as t
from dataclasses import dataclass
from dataclasses import field


T = t.TypeVar("T")


class Injector(abc.ABC):
    """An abstract base class for a dependency injection container."""

    @abc.abstractmethod
    async def provide(
        self,
        dependency: T | None,
        singleton: bool,
        interface: type[abc.ABC] | None = None,
        factory: cabc.Callable[[], T] | None = None,
        name: str | None = None,
        scope: str | None = None,
        on_init: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None,
        on_destroy: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None,
    ) -> None:
        """Provide a dependency to the container.

        - The dependency can be provided as an instance, a factory function, or both.
        - The dependency can be registered as a singleton or a transient instance.
        - The dependency can also be associated with an interface, a name, and a scope.

        Args:
            dependency (T | None): An instance of the dependency to provide.
            singleton (bool): Whether the dependency should be a singleton or not.
            interface (type[abc.ABC] | None): The interface of the dependency.
            factory (Callable[[], T] | None): A factory function to create the dependency.
            name (str | None): The name of the dependency.
            scope (str | None): The scope of the dependency.
            on_init (Callable[[T], None] | Callable[[T], Coroutine[Any, Any, None]] | None): A function to call when the dependency is initialized.
            on_destroy (Callable[[T], None] | Callable[[T], Coroutine[Any, Any, None]] | None): A function to call when the dependency is destroyed.
        """  # noqa: E501
        ...

    @abc.abstractmethod
    async def resolve(self, dependency: type[T], name: str | None = None) -> T:
        """Resolve a dependency from the container.

        The following rules are used to resolve the dependency:
        - If no name is provided, the first dependency registered for the given type is resolved.
        - If the name is not found, it tries to resolve the dependency by the name of the type.
        - If the name is an empty string, the first dependency registered for the given type is resolved.
        - If the name is '-1', the last dependency registered for the given type is resolved.

        Args:
            dependency (type[T]): The type of the dependency to resolve.
            name (str | None): The name of the dependency.
        """
        ...

    @abc.abstractmethod
    async def resolve_all(self, dependency: type[T]) -> list[T]:
        """Resolve all dependencies of a given type from the container."""
        ...

    @abc.abstractmethod
    async def delete(self, dependency: type[T]) -> None:
        """Remove a dependency from the DI container."""
        ...

    @abc.abstractmethod
    async def destroy_scope(self, scope: str) -> None:
        """Remove all dependencies from a given scope."""
        ...


@dataclass(slots=True)
class Dependency(t.Generic[T]):
    """A class to represent a dependency in the container."""

    value: T
    """The value of the dependency."""
    factory: cabc.Callable[[], T] | None
    """A factory function to create the dependency."""
    singleton: bool
    """Whether the dependency is a singleton or not."""
    initialized: bool = False
    """Whether the dependency has been initialized or not."""
    on_init: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None
    """A function to call when the dependency is initialized."""
    on_destroy: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None
    """A function to call when the dependency is destroyed."""
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def instantiate(self) -> T:
        """Instantiate the dependency."""
        if not self.singleton:
            instance = self._new_instance()
            if self.on_init:
                self.on_init(instance)
            return instance

        async with self._lock:
            if not self.initialized:
                self.value = self._new_instance()
                if self.on_init:
                    if inspect.iscoroutinefunction(self.on_init):
                        await self.on_init(self.value)
                    else:
                        self.on_init(self.value)
                self.initialized = True
        return self.value

    def _new_instance(self) -> T:
        """Create a new instance of the dependency."""
        if self.factory:
            return self.factory()
        return self.value

    def __del__(self) -> None:
        """Destroy the dependency."""
        if self.initialized and self.on_destroy:
            if inspect.iscoroutinefunction(self.on_destroy):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.on_destroy(self.value))
                        return
                    raise RuntimeError("No running event loop")
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.on_destroy(self.value))
                    finally:
                        loop.close()

            self.on_destroy(self.value)


@dataclass(frozen=True, slots=True)
class DependencyInfo:
    """A class to represent information about a dependency in the container."""

    interface: type
    """The interface of the dependency."""
    implementation: type
    """The implementation of the dependency."""
    scope: str | None = None
    """The scope of the dependency."""


class DIContainer(Injector):
    """A dependency injection container."""

    def __init__(self) -> None:
        self._dependencies: dict[type, list[Dependency[t.Any]]] = {}
        self._registry: dict[str, DependencyInfo] = {}
        self._scopes: dict[str, list[Dependency[t.Any]]] = {}
        self._lock = asyncio.Lock()

    async def provide(
        self,
        dependency: T | None,
        singleton: bool,
        interface: type[abc.ABC] | None = None,
        factory: cabc.Callable[[], T] | None = None,
        name: str | None = None,
        scope: str | None = None,
        on_init: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None,
        on_destroy: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None = None,
    ) -> None:
        """Provide a dependency to the container."""
        if name == "-1":
            raise ValueError("name cannot be a reserved keyword: '-1'")

        await self._provide(dependency, interface, factory, singleton, name, scope, on_init, on_destroy)

    async def resolve(self, dependency: type[T], name: str | None = None) -> T:
        """Resolve a dependency from the container."""
        if not name:
            return await self._resolve(dependency, dependency.__name__)

        return await self._resolve(dependency, name)

    async def resolve_all(self, dependency: type[T]) -> list[T]:
        """Resolve all dependencies of a given type from the container."""
        async with self._lock:
            deps = self._dependencies.get(dependency, [])
            if not deps:
                raise DependencyNotFoundError(f"No dependencies found for {dependency}")
            return [await dep.instantiate() for dep in deps]

    async def delete(self, dependency: type[T]) -> None:
        """Delete a dependency from the container."""
        async with self._lock:
            if dependency in self._dependencies:
                for dep in self._dependencies[dependency]:
                    del dep
                del self._dependencies[dependency]
            for name, info in list(self._registry.items()):
                if info.interface is dependency:
                    del self._registry[name]

    async def destroy_scope(self, scope: str) -> None:
        """Destroy a scope from the container."""
        async with self._lock:
            if scope in self._scopes:
                for dep in self._scopes[scope]:
                    del dep
                del self._scopes[scope]

    async def _provide(
        self,
        dependency: T | None,
        interface: type[abc.ABC | t.Any] | None,
        factory: cabc.Callable[[], T] | None,
        singleton: bool,
        name: str | None,
        scope: str | None,
        on_init: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None,
        on_destroy: cabc.Callable[[T], None] | cabc.Callable[[T], cabc.Coroutine[t.Any, t.Any, None]] | None,
    ) -> None:
        if dependency is None and factory is None:
            raise ValueError("both dependency and factory cannot be None")

        if dependency is None:
            dependency = factory()  # type: ignore # The factory can never be None here
            if dependency is None:
                raise ValueError("factory must return an instance of the dependency")

        if not interface:
            interface = type(dependency)
            if isinstance(interface, type) and interface.__name__ == "type":
                interface = interface.__bases__[0]

        dep = Dependency(
            value=dependency,
            factory=factory,
            singleton=singleton,
            on_init=on_init,
            on_destroy=on_destroy,
        )

        async with self._lock:
            self._dependencies.setdefault(interface, []).append(dep)
            if scope:
                self._scopes.setdefault(scope, []).append(dep)
            if not name:
                name = type(dependency).__name__
            self._registry[name] = DependencyInfo(interface, type(dependency), scope)

    async def _resolve(self, dependency: type[T], name: str) -> T:
        async with self._lock:
            deps = self._dependencies.get(dependency)
            if not deps or len(deps) == 0:
                raise DependencyNotFoundError(f"No dependency found for {dependency}")

            match name:
                case "":
                    return await deps[0].instantiate()
                case "-1":
                    return await deps[-1].instantiate()
                case _:
                    pass

            info = self._registry.get(name)
            if not info:
                raise DependencyNotFoundError(f"No dependency found for {name}")
            if info.interface != dependency:
                raise DependencyMismatchError(f"Dependency {name} is not of type {dependency}")

            for dep in deps:
                if dep.value.__class__ == info.implementation:
                    return await dep.instantiate()

            raise DependencyNotFoundError(f"Dependency {name} not found in the registered instances")


class DIContainerError(Exception):
    """A base exception class for all exceptions raised by the DIContainer."""

    pass


class DependencyNotFoundError(DIContainerError):
    """Raised when a dependency is not found in the container."""

    pass


class DependencyMismatchError(DIContainerError):
    """Raised when a dependency is found but it doesn't match the expected type."""

    pass


container: Injector = DIContainer()
"""The default dependency injection container."""
