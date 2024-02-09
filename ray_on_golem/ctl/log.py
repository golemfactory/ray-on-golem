from abc import ABC, abstractmethod

import colorful


class RayOnGolemCtlError(Exception):
    ...


class RayOnGolemCtlLogger(ABC):
    @abstractmethod
    def info(self, msg: str):
        """Handle a regular info-level message."""

    @abstractmethod
    def warning(self, msg: str):
        """Handle a warning-level message."""

    @abstractmethod
    def verbose(self, msg: str):
        """Handle a verbose-level message."""

    @abstractmethod
    def error(self, msg: str):
        """Handle an error"""


class RayOnGolemCtlConsoleLogger(RayOnGolemCtlLogger):
    def __init__(self, verbose=False):
        self._output_verbose = verbose

    def info(self, msg: str):
        print(msg)

    def warning(self, msg: str):
        print(colorful.yellow(msg))

    def verbose(self, msg: str):
        if self._output_verbose:
            print(msg)

    def error(self, msg: str):
        raise RayOnGolemCtlError(msg)
