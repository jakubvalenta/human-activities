import logging
from threading import Event, Thread
from time import sleep
from typing import Callable, Optional

from PIL import Image

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import save_config
from lidske_aktivity.store import Store, TFractions
from lidske_aktivity.ui.lib import App, StatusIcon
from lidske_aktivity.ui.menu import Menu
from lidske_aktivity.ui.settings import Settings

logger = logging.getLogger(__name__)


class StatusIcon(StatusIcon):
    store: Store
    last_percents: Optional[TFractions] = None

    def __init__(self, store: Store, *args, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def _should_update(self) -> bool:
        if self.store.percents == self.last_percents:
            return False
        self.last_percents = self.store.percents
        return True

    def _create_icon_image(self) -> Image:
        slices_frac = list(self.store.percents.values())
        logger.info('Updating icon with slices %s', slices_frac)
        return draw_pie_chart(self.calc_icon_size(), slices_frac)

    def _create_tooltip(self) -> str:
        return '\n'.join(
            '{text}: {fraction:.2%}'.format(
                text=self.store.get_text(path),
                fraction=fraction
            )
            for path, fraction in self.store.percents.items()
        )

    def update(self):
        if self._should_update():
            image = self._create_icon_image()
            tooltip = self._create_tooltip()
            self.update_icon(image, tooltip)


class Application(App):
    menu: Menu
    store: Store
    on_quit: Callable
    status_icon: StatusIcon
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
        self.status_icon = StatusIcon(
            store=self.store,
            on_menu=lambda event: self.show_menu(),
            on_setup=lambda event: self.show_setup(),
            on_settings=lambda event: self.show_settings(),
            on_about=lambda event: self.show_about(),
            on_quit=lambda event: self.quit()
        )
        self.frame = wx.Frame(parent=None, title=__title__)
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
