import logging
import time
from threading import Event, Thread
from typing import Any, List, Optional

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.config import Config
from lidske_aktivity.icon import draw_pie_chart_png, gen_random_slices
from lidske_aktivity.model import DirectoryView, Model

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    model: Model
    ui_app: Any
    status_icon: Any
    last_directory_views_list: Optional[List[DirectoryView]] = None
    tick_event_stop: Optional[Event] = None
    tick_thread: Optional[Thread] = None

    def __init__(self, ui: Any):
        self.model = Model()
        self.ui = ui
        self.ui.app.Application(self.on_init, self.on_quit).run()

    def on_init(self, ui_app: Any):
        self.ui_app = ui_app
        logger.info('On init')
        self.status_icon = self.ui.status_icon.StatusIcon(self)
        if self.model.config.show_setup:
            self.model.config.show_setup = False
            self.show_setup()
        self.tick_start()

    def set_config(self, config: Config):
        self.model.config = config
        self._update_status_icon()

    def show_setup(self):
        self.ui_app.spawn_frame(
            self.ui.setup.Setup,
            self.model.config,
            self.set_config
        )

    def show_settings(self):
        self.ui_app.spawn_frame(
            self.ui.settings.Settings,
            self.model.config,
            self.set_config
        )

    def show_about(self):
        self.ui.about.show_about(
            image=draw_pie_chart_png(148, list(gen_random_slices())),
            title=__title__,
            version=__version__,
            copyright=__copyright__,
            uri=__uri__,
            authors=__authors__
        )

    def tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self.tick)
        self.tick_thread.start()

    def tick_stop(self):
        if self.tick_event_stop is not None:
            self.tick_event_stop.set()
        if self.tick_thread is not None:
            self.tick_thread.join()
        logger.info('Tick stopped')

    def tick(self):
        while not self.tick_event_stop.is_set():
            logger.debug('Tick')
            self.ui.lib.call_tick(self._update_status_icon)
            time.sleep(1)

    def _update_status_icon(self):
        directory_views_list = list(self.model.directory_views.values())
        if directory_views_list == self.last_directory_views_list:
            return
        self.last_directory_views_list = directory_views_list
        logger.info(
            'Updating icon with slices %s',
            [f'{fract:.2f}' for fract in self.model.directory_views.fractions]
        )
        self.status_icon.update(self.model.directory_views)

    def quit(self):
        logger.info('Menu quit')
        self.ui_app.quit()
        self.status_icon.destroy()

    def on_quit(self):
        logger.info('App on_quit')
        self.tick_stop()
        self.model.scan_stop()
