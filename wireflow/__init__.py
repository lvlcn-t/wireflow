import importlib
from importlib import metadata
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wireflow.dependency import container
    from wireflow.dependency import DependencyMismatchError
    from wireflow.dependency import DependencyNotFoundError
    from wireflow.dependency import DIContainer
    from wireflow.dependency import DIContainerError
    from wireflow.dependency import Injector
    from wireflow.provider import inject
    from wireflow.provider import Provide


__all__ = [
    "container",
    "DependencyMismatchError",
    "DependencyNotFoundError",
    "DIContainer",
    "DIContainerError",
    "Injector",
    "inject",
    "Provide",
]

_module_lookup = {
    "container": "wireflow.dependency",
    "DependencyMismatchError": "wireflow.dependency",
    "DependencyNotFoundError": "wireflow.dependency",
    "DIContainer": "wireflow.dependency",
    "DIContainerError": "wireflow.dependency",
    "Injector": "wireflow.dependency",
    "inject": "wireflow.provider",
    "Provide": "wireflow.provider",
}

try:
    __version__ = metadata.version(__package__)  # type: ignore
except metadata.PackageNotFoundError:
    __version__ = ""
except ValueError:
    __version__ = ""

del metadata  # Avoid polluting the namespace (results of dir(__package__) would include metadata)


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
