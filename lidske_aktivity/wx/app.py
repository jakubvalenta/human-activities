import logging
from typing import Callable

import wx

from lidske_aktivity import __title__

logger = logging.getLogger(__name__)


class Application(wx.App):
    frame: wx.Frame

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title=__title__)
        self.on_init(self.frame)
        return True

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        self.frame.Destroy()

    def OnExit(self) -> bool:
        logger.info('App OnExit')
        self.on_quit()
        super().OnExit()
        return True

    def run(self):
        self.MainLoop()
