import logging
from typing import Callable, TypeVar

from PyQt5 import QtWidgets

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Application(QtWidgets.QApplication):
    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(*args, **kwargs)

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, **kwargs)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        super().quit()

    def run(self):
        self.exec_()
