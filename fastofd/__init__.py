from .ofd import OFD
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fastofd")
except PackageNotFoundError:
    __version__ = "0.0.6"
__author__ = "ihadyou"
__email__ = "wohen@nivbi.com"
__description__ = "一个用于OFD文档处理的Python库"
__all__ = ["OFD"]