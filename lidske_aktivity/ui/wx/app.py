import logging
from typing import Callable

import wx
import wx.adv

from lidske_aktivity.config import save_config
from lidske_aktivity.store import Store
from lidske_aktivity.ui.wx.about import About
from lidske_aktivity.ui.wx.menu import Menu
from lidske_aktivity.ui.wx.settings import Settings
from lidske_aktivity.ui.wx.setup import Setup

logger = logging.getLogger(__name__)


class TaskBarIcon(wx.adv.TaskBarIcon):
    id_setup = wx.NewIdRef()

    def __init__(self,
                 on_menu: Callable,
                 on_setup: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        super().__init__(wx.adv.TBI_DOCK)

        icon = wx.Icon()
        icon.LoadFile('/usr/share/icons/Adwaita/16x16/actions/go-home.png')
        self.SetIcon(icon)

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_menu)
        self.Bind(wx.EVT_MENU, on_setup, id=self.id_setup)
        self.Bind(wx.EVT_MENU, on_settings, id=wx.ID_SETUP)
        self.Bind(wx.EVT_MENU, on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, on_quit, id=wx.ID_EXIT)

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        menu.Append(self.id_setup, '&Setup')
        menu.Append(wx.ID_SETUP, 'Advanced &configuration')
        menu.Append(wx.ID_ABOUT, '&About')
        menu.Append(wx.ID_EXIT, 'E&xit')
        return menu


class Application(wx.App):
    menu: Menu
    store: Store
    on_quit: Callable
    status_icon: TaskBarIcon

    def __init__(self,
                 store: Store,
                 on_quit: Callable,
                 *args,
                 **kwargs):
        self.store = store
        self.on_quit = on_quit  # type: ignore
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title='Foo')
        self.status_icon = TaskBarIcon(
            on_menu=lambda event: self.show_menu(),
            on_setup=lambda event: self.show_setup(),
            on_settings=lambda event: self.show_settings(),
            on_about=lambda event: self.show_about(),
            on_quit=lambda event: self.quit()
        )
        self.menu = Menu(store=self.store, parent=self.frame)
        if self.store.config.show_setup:
            self.store.config.show_setup = False
            self.show_setup()
        return True

    def show_menu(self):
        self.menu.popup_at(*wx.GetMousePosition())

    def show_setup(self):
        setup = Setup(self.frame, self.store.config)
        val = setup.show()
        if val == wx.ID_OK:
            self.store.config = setup.config
            self.menu.refresh()
            save_config(self.store.config)
        setup.Destroy()

    def show_settings(self):
        settings = Settings(self.frame, self.store.config)
        val = settings.show()
        if val == wx.ID_OK:
            self.store.config = settings.config
            self.menu.refresh()
            save_config(self.store.config)
        settings.Destroy()

    def show_about(self):
        about = About(self.frame)
        about.show()
        about.Destroy()

    def quit(self):
        logger.info('Menu quit')
        self.status_icon.Destroy()
        self.menu.Destroy()
        self.frame.Destroy()

    def OnExit(self):
        logger.info('App OnExit')
        self.on_quit()
        super().OnExit()
        return True


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
