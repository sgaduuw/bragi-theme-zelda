"""bragi-theme-zelda: a Link's-Awakening-flavoured bragi theme."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bragi-theme-zelda")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
