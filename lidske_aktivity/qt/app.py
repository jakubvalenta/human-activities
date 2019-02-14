import logging
import signal
import sys
from typing import Callable, TypeVar

from PyQt5 import QtWidgets

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Application(QtWidgets.QApplication):
    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(sys.argv, *args, **kwargs)
        self.on_init(self)

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, **kwargs)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        super().quit()

    def run(self):
        signal.signal(signal.SIGINT, lambda *args: self.quit())
        self.exec_()
