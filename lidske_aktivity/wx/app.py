import logging
from typing import Callable, TypeVar

import wx

from lidske_aktivity import __title__

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Application(wx.App):
    _frame: wx.Frame

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self._frame = wx.Frame(parent=None, title=__title__)
        self.on_init(self)
        return True

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, **kwargs, parent=self._frame)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        self._frame.Destroy()

    def OnExit(self) -> bool:
        logger.info('App OnExit')
        self.on_quit()
        super().OnExit()
        return True

    def run(self):
        self.MainLoop()
