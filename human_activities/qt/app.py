import logging
import signal
import sys
from typing import Callable, TypeVar

from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Application(QApplication):
    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(sys.argv, *args, **kwargs)
        self.setQuitOnLastWindowClosed(False)
        self.on_init(self)

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, ui_app=self, **kwargs)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        super().quit()

    def run(self) -> int:
        signal.signal(signal.SIGINT, lambda *args: self.quit())
        return self.exec_()
