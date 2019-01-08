import logging

import wx

logger = logging.getLogger(__name__)


class Application(wx.App):
    title: str
    frame: wx.Frame

    def __init__(self, *args, **kwargs):
        super().__init__(False, *args, **kwargs)

    def on_init(self):
        raise NotImplementedError

    def on_quit(self):
        raise NotImplementedError

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title=self.title)
        self.on_init()
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
