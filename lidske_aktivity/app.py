import logging
import time
from threading import Event, Thread
from typing import Any, Optional

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import Config
from lidske_aktivity.model import Model, TExtDirectories

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    model: Model
    frame: Any
    ui_app: Any
    status_icon: Any
    last_ext_directories: Optional[TExtDirectories] = None

    def __init__(self, ui: Any):
        self.model = Model()
        self.ui = ui
        self.ui_app = self.ui.app.Application(self.on_init, self.on_quit)
        self.ui_app.run()

    def on_init(self, frame: Any):
        logger.info('On init')
        self.menu = self.ui.menu.Menu(self, parent=frame)
        self.menu.init(self.model.active_mode, self.model.ext_directories)
        self.status_icon = self.ui.status_icon.StatusIcon(self)
        if self.model.config.show_setup:
            self.model.config.show_setup = False
            self.show_setup()
        self.tick_start()

    def set_active_mode(self, active_mode: str):
        if self.model.active_mode == active_mode:
            return
        self.model.active_mode = active_mode
        self.menu.update_radio_buttons(active_mode)
        self.update_icon()
        self.update_menu()

    def set_config(self, config: Config):
        self.model.config = config
        self.reset_menu()
        self.update_icon()
        self.update_menu()

    def show_menu(self, mouse_x: int, mouse_y: int):
        self.menu.popup_at(mouse_x, mouse_y)

    def show_setup(self):
        self.ui.setup.Setup(
            self.model.config,
            on_finish=lambda setup: self.set_config(setup.config),
            parent=self.ui_app.frame
        )

    def show_settings(self):
        self.ui.settings.Settings(
            self.model.config,
            lambda settings: self.set_config(settings.config),
            parent=self.ui_app.frame
        )

    def show_about(self):
        self.ui.about.show_about(
            image=draw_pie_chart(148, list(gen_random_slices())),
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
            logger.info('Tick')
            self.ui.lib.call_tick(self.on_tick)
            time.sleep(1)

    def on_tick(self):
        if self.model.ext_directories != self.last_ext_directories:
            self.last_ext_directories = self.model.ext_directories
            self.update_icon()
            self.update_menu()

    def update_icon(self):
        logger.info('Updating icon with slices %s', self.model.percents)
        self.status_icon.update(self.model.percents, self.model.tooltip)

    def update_menu(self):
        logger.info('Update menu')
        pending = False
        if self.model.ext_directories:
            for path, ext_directory in self.model.ext_directories.items():
                if ext_directory.pending:
                    pending = True
                    self.menu.pulse_progress_bar(path)
                else:
                    self.menu.update_progress_bar(
                        path,
                        ext_directory.fraction,
                        ext_directory.tooltip
                    )
        if not pending:
            self.menu.hide_spinner()

    def reset_menu(self):
        self.menu.reset(self.model.active_mode, self.model.ext_directories)

    def quit(self):
        logger.info('Menu quit')
        self.ui_app.quit()
        self.status_icon.destroy()
        self.menu.destroy()

    def on_quit(self):
        logger.info('App on_quit')
        self.tick_stop()
        self.model.scan_stop()
