import logging
import time
from threading import Event, Thread
from typing import Optional

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import Config
from lidske_aktivity.model import Model, TExtDirectories

if False:
    from lidske_aktivity.ui.about import show_about
    from lidske_aktivity.ui.app import Application as UIApplication
    from lidske_aktivity.ui.lib import call_tick
    from lidske_aktivity.ui.menu import Menu
    from lidske_aktivity.ui.settings import Settings
    from lidske_aktivity.ui.setup import Setup
    from lidske_aktivity.ui.status_icon import StatusIcon
else:
    from lidske_aktivity.gtk.about import show_about
    from lidske_aktivity.gtk.app import Application as UIApplication
    from lidske_aktivity.gtk.lib import call_tick
    from lidske_aktivity.gtk.menu import Menu
    from lidske_aktivity.gtk.settings import Settings
    from lidske_aktivity.gtk.setup import Setup
    from lidske_aktivity.gtk.status_icon import StatusIcon

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application(UIApplication):
    title = __title__
    model: Model
    status_icon: StatusIcon
    last_ext_directories: Optional[TExtDirectories] = None

    def __init__(self):
        self.model = Model()
        super().__init__()

    def on_init(self):
        logger.info('On init')
        self.menu = Menu(self, parent=self.frame)
        self.menu.init(self.model.active_mode, self.model.ext_directories)
        self.status_icon = StatusIcon(self)
        if self.model.config.show_setup:
            self.model.config.show_setup = False
            self.show_setup()
        self.tick_start()

    def set_active_mode(self, active_mode: str):
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
        Setup(
            self.model.config,
            on_finish=lambda setup: self.set_config(setup.config),
            parent=self.frame
        )

    def show_settings(self):
        Settings(
            self.model.config,
            lambda settings: self.set_config(settings.config),
            parent=self.frame
        )

    def show_about(self):
        image = draw_pie_chart(148, list(gen_random_slices(3, 8)))
        show_about(
            image=image,
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
            call_tick(self.on_tick)
            time.sleep(1)

    def on_tick(self):
        if self.model.ext_directories != self.last_ext_directories:
            self.last_ext_directories = self.model.ext_directories
            self.update_icon()
            self.update_menu()

    def update_icon(self):
        logger.info('Updating icon with slices %s', self.model.percents)
        image = draw_pie_chart(self.status_icon.icon_size, self.model.percents)
        self.status_icon.update(image, self.model.tooltip)

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
        super().quit()
        self.status_icon.destroy()
        self.menu.destroy()

    def on_quit(self):
        logger.info('App on_quit')
        self.tick_stop()
        self.model.scan_stop()


def main():
    app = Application()
    app.run()
