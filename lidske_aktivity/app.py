import logging
from pathlib import Path
from threading import Event, Thread
from typing import Optional

from PIL import Image

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import (
    CACHE_PATH, MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, load_config,
    save_config,
)
from lidske_aktivity.directories import (
    init_directories_from_paths, init_directories_from_root_path,
    scan_directories,
)
from lidske_aktivity.store import Store, TFractions
from lidske_aktivity.ui.lib import Application, StatusIcon, show_about
from lidske_aktivity.ui.settings import Settings
from lidske_aktivity.ui.setup import Setup

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application(Application):
    title = __title__

    store: Store
    scan_event_stop: Event
    scan_thread: Thread

    status_icon: StatusIcon
    last_percents: Optional[TFractions] = None
    last_fractions: Optional[TFractions] = None

    def __init__(self):
        config = load_config()
        self.store = Store(
            config=config,
            on_config_change=self.on_config_change
        )
        self.load_directories()
        self.scan_start()

    def load_directories(self):
        if self.store.config.mode == MODE_HOME:
            directories = init_directories_from_root_path(
                CACHE_PATH,
                Path.home()
            )
        elif self.store.config.mode == MODE_PATH:
            directories = init_directories_from_root_path(
                CACHE_PATH,
                self.store.config.root_path
            )
        elif self.store.config.mode == MODE_CUSTOM:
            directories = init_directories_from_paths(
                CACHE_PATH,
                self.store.config.custom_dirs
            )
        elif self.store.config.mode == MODE_NAMED:
            directories = init_directories_from_paths(
                CACHE_PATH,
                self.store.config.named_dirs.keys()
            )
        else:
            raise AppError(f'Invalid mode {self.store.config.mode}')
        self.store.directories = directories

    def on_config_change(self):
        self.scan_stop()
        self.load_directories()
        self.scan_start()

    def scan_start(self):
        self.scan_event_stop = Event()
        self.scan_thread = scan_directories(
            self.store.directories,
            cache_path=CACHE_PATH,
            callback=self.store.update,
            event_stop=self.scan_event_stop,
            test=self.store.config.test
        )

    def scan_stop(self):
        self.scan_event_stop.set()
        self.scan_thread.join()
        logger.info('Scan stopped')

    def on_init(self):
        self.status_icon = StatusIcon(
            on_setup=self.show_setup,
            on_settings=self.show_settings,
            on_about=self.show_about,
            on_quit=self.quit
        )
        if self.store.config.show_setup:
            self.store.config.show_setup = False
            self.show_setup()

    def show_setup(self):
        Setup(
            self.store.config,
            on_finish=self.on_setup_finish,
            parent=self.frame
        )

    def on_setup_finish(self, setup: Setup):
        self.store.config = setup.config
        self.status_icon.refresh_menu()
        save_config(self.store.config)

    def show_settings(self):
        Settings(
            self.store.config,
            self.on_settings_accept,
            parent=self.frame
        )

    def on_settings_accept(self, settings: Settings):
        self.store.config = settings.config
        self.status_icon.refresh_menu()
        save_config(self.store.config)

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

    def _should_update(self) -> bool:
        if self.store.fractions != self.last_fractions:
            return False
        self.last_fractions = self.store.fractions
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

    def on_tick(self, pulse: bool = True):
        if self._should_update():
            image = self._create_icon_image()
            tooltip = self._create_tooltip()
            self.update_icon(image, tooltip)
            self.update_menu(pulse=pulse)

    def update_menu(self, pulse: bool = False):
        if self.store.directories:
            for path, d in self.store.directories.items():
                if d.size is None:
                    if pulse:
                        self.menu.pulse_progress_bar()
                else:
                    self.menu.update_progress_bar(
                        self.store.fractions[path],
                        self.store.get_tooltip(path)
                    )
        if not any(self.store.pending.values()):
            self.menu.hide_spinner()

    def refresh_menu(self):
        self.menu.refresh()

    def quit(self):
        super().quit()
        self.status_icon.destroy()

    def on_exit(self):
        self.scan_stop()


def main():
    app = Application()
    app.run()
