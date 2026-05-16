from typing import Generic, TypeVar
import importlib
import inspect
import pkgutil

T = TypeVar("T")


class Registry(Generic[T]):
    """Generic auto-discovering registry.

    Subclass it, set `marker` to the attribute name your decorator stamps,
    and call `autodiscover()` to scan the package.

    Example:
        class TransformationRegistry(Registry[Callable]):
            marker = "_transformation_name"
    """

    marker: str  # attribute name stamped by the decorator

    def __init__(self):
        self._entries: dict[str, T] = {}

    def register(self, name: str):
        """Decorator that registers a callable under the given name."""
        def decorator(fn: T) -> T:
            if name in self._entries:
                raise KeyError(f"'{name}' is already registered in {type(self).__name__}.")
            setattr(fn, self.marker, name)
            self._entries[name] = fn
            return fn
        return decorator

    def autodiscover(self, package: str):
        if package.startswith("."):
            caller_package = inspect.stack()[1].frame.f_globals["__name__"]
        else:
            caller_package = None
        pkg_module = importlib.import_module(package, caller_package)
        for _, module_name, _ in pkgutil.iter_modules(pkg_module.__path__):
            if module_name == "registry":
                continue
            importlib.import_module(f"{pkg_module.__name__}.{module_name}")

    def get(self, name: str) -> T:
        if name not in self._entries:
            raise KeyError(
                f"'{name}' not found in {type(self).__name__}. "
                f"Available: {self.available()}"
            )
        return self._entries[name]

    def available(self) -> list[str]:
        return list(self._entries.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._entries