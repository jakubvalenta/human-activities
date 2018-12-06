from typing import Callable

import wx
import wx.adv

from lidske_aktivity.config import save_config
from lidske_aktivity.store import Store
from lidske_aktivity.ui.wx.about import About
from lidske_aktivity.ui.wx.menu import Menu
from lidske_aktivity.ui.wx.settings import Settings
from lidske_aktivity.ui.wx.setup import Setup


class TaskBarIcon(wx.adv.TaskBarIcon):
    id_setup = wx.NewIdRef()

    def __init__(self,
                 on_main_menu: Callable,
                 on_setup: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        super().__init__(wx.adv.TBI_DOCK)

        icon = wx.Icon()
        icon.LoadFile('/usr/share/icons/Adwaita/16x16/actions/go-home.png')
        self.SetIcon(icon)

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_main_menu)
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
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title='Foo')
        self.init_menu()
        self.status_icon = TaskBarIcon(
            on_main_menu=self.on_main_menu,
            on_setup=self.on_menu_setup,
            on_settings=self.on_menu_settings,
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        return True

    def init_menu(self):
        self.menu = Menu(store=self.store, parent=self.frame)

    def destroy_menu(self):
        self.menu.Destroy()
        self.menu.tick_stop()

    def on_main_menu(self, event):
        mouse_x, mouse_y = wx.GetMousePosition()
        display_id = wx.Display.GetFromWindow(self.menu)
        display = wx.Display(display_id)
        _, _, screen_w, screen_h = display.GetClientArea()
        window_w, window_h = self.menu.GetSize()
        SCREEN_MARGIN = 10
        window_x = min(
            mouse_x,
            max(screen_w - window_w - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        window_y = min(
            mouse_y,
            max(screen_h - window_h - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        self.menu.SetPosition((window_x, window_y))
        self.menu.Popup()

    def on_menu_setup(self, event):
        setup = Setup(self.frame, self.store.config)
        val = setup.ShowModal()
        if val == wx.ID_OK:
            self.store.config = setup.config
            self.destroy_menu()
            self.init_menu()
            save_config(self.store.config)
        setup.Destroy()

    def on_menu_settings(self, event):
        settings = Settings(self.frame, self.store.config)
        val = settings.ShowModal()
        if val == wx.ID_OK:
            self.store.config = settings.config
            self.destroy_menu()
            self.init_menu()
            save_config(self.store.config)
        settings.Destroy()

    def on_menu_about(self, event):
        about = About(self.frame)
        about.ShowModal()
        about.Destroy()

    def on_menu_quit(self, event):
        self.status_icon.Destroy()
        self.menu.Destroy()
        self.frame.Destroy()

    def OnExit(self):
        self.on_quit()
        self.menu.tick_stop()
        super().OnExit()
        return True


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
