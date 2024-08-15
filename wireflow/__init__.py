import importlib
from importlib import metadata
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wireflow.dependency import Injector
    from wireflow.dependency import DIContainer
    from wireflow.dependency import container
    from wireflow.provider import Provide
    from wireflow.provider import inject

__all__ = [
    "Injector",
    "DIContainer",
    "container",
    "Provide",
    "inject",
]

_module_lookup = {
    "Injector": "wireflow.dependency",
    "DIContainer": "wireflow.dependency",
    "container": "wireflow.dependency",
    "Provide": "wireflow.provider",
    "inject": "wireflow.provider",
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
