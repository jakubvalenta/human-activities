import logging
from threading import Event, Thread
from time import sleep
from typing import Callable, Optional

import wx
import wx.adv

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import save_config
from lidske_aktivity.store import Store, TFractions
from lidske_aktivity.ui.lib import create_icon_from_image
from lidske_aktivity.ui.menu import Menu
from lidske_aktivity.ui.settings import Settings
from lidske_aktivity.ui.setup import Setup

logger = logging.getLogger(__name__)


class TaskBarIcon(wx.adv.TaskBarIcon):
    store: Store
    last_fractions: Optional[TFractions] = None
    id_setup = wx.NewIdRef()

    def __init__(self,
                 store: Store,
                 on_menu: Callable,
                 on_setup: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        self.store = store
        # TODO: Check TaskBarIcon.isAvailable()
        super().__init__(wx.adv.TBI_DOCK)
        self.update()
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

    def update(self):
        if self.store.fractions == self.last_fractions:
            return
        self.last_fractions = self.store.fractions
        slices_frac = list(self.store.fractions.values())
        logger.info('Updating icon with slices %s', slices_frac)
        image = draw_pie_chart(self.calc_icon_size(), slices_frac)
        icon = create_icon_from_image(image)
        tooltip = '\n'.join(
            '{text}: {fraction:.2%}'.format(
                text=self.store.get_text(path),
                fraction=self.store.fractions[path]
            )
            for path in self.store.fractions
        )
        self.SetIcon(icon, tooltip)

    @staticmethod
    def calc_icon_size() -> int:
        if 'wxMSW' in wx.PlatformInfo:
            return 16
        if 'wxGTK' in wx.PlatformInfo:
            return 22
        return 128


class Application(wx.App):
    menu: Menu
    store: Store
    on_quit: Callable
    status_icon: TaskBarIcon
    tick_event_stop: Optional[Event] = None
    tick_thread: Optional[Thread] = None

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
            store=self.store,
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
        self._tick_start()
        return True

    def show_menu(self):
        self.menu.popup_at(*wx.GetMousePosition())

    def show_setup(self):
        setup = Setup(self.frame, self.store.config)
        if setup.run():
            self.store.config = setup.config
            self.menu.refresh()
            save_config(self.store.config)

    def show_settings(self):
        settings = Settings(self.frame, self.store.config)
        val = settings.show()
        if val == wx.ID_OK:
            self.store.config = settings.config
            self.menu.refresh()
            save_config(self.store.config)
        settings.Destroy()

    def show_about(self):
        info = wx.adv.AboutDialogInfo()
        image = draw_pie_chart(148, list(gen_random_slices(3, 8)))
        info.Icon = create_icon_from_image(image)
        info.Name = __title__
        info.Version = __version__
        info.Copyright = __copyright__
        info.WebSite = __uri__
        info.Developers = __authors__
        wx.adv.AboutBox(info)

    def _tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self._tick)
        self.tick_thread.start()

    def _tick_stop(self):
        if self.tick_event_stop is not None:
            self.tick_event_stop.set()
        if self.tick_thread is not None:
            self.tick_thread.join()
        logger.info('Tick stopped')

    def _tick(self):
        while not self.tick_event_stop.is_set():
            wx.CallAfter(self._on_tick)
            sleep(1)

    def _on_tick(self, pulse: bool = True):
        logger.info('Updating UI')
        self.status_icon.update()
        self.menu.update()

    def quit(self):
        logger.info('Menu quit')
        self._tick_stop()
        self.status_icon.Destroy()
        self.menu.Destroy()
        self.frame.Destroy()

    def OnExit(self):
        logger.info('App OnExit')
        self._tick_stop()
        self.on_quit()
        super().OnExit()
        return True


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
