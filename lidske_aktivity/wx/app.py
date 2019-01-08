import logging
from typing import Callable

import wx

logger = logging.getLogger(__name__)


class Application(wx.App):
    title: str
    frame: wx.Frame

    def __init__(self,
                 title: str,
                 on_init: Callable,
                 on_quit: Callable,
                 *args,
                 **kwargs):
        self.title = title
        self.on_init = on_init
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title=self.title)
        self.on_init(self.frame)
        return True

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        self.frame.Destroy()

    def OnExit(self):
        logger.info('App OnExit')
        self.on_quit()
        super().OnExit()
        return True

    def run(self):
        self.MainLoop()
