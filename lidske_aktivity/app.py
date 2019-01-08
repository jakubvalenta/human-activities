import logging
import textwrap
import time
from pathlib import Path
from threading import Event, Thread
from typing import NamedTuple, Optional

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
from lidske_aktivity.store import (
    SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store, TFractions,
)
from lidske_aktivity.ui.about import show_about
from lidske_aktivity.ui.app import Application as UIApplication
from lidske_aktivity.ui.lib import call_tick
from lidske_aktivity.ui.menu import Menu
from lidske_aktivity.ui.settings import Settings
from lidske_aktivity.ui.setup import Setup
from lidske_aktivity.ui.status_icon import StatusIcon

logger = logging.getLogger(__name__)


class Mode(NamedTuple):
    name: str
    label: str
    tooltip: str


class AppError(Exception):
    pass


class Application(UIApplication):
    title = __title__

    store: Store
    scan_event_stop: Event
    scan_thread: Thread

    status_icon: StatusIcon
    last_percents: Optional[TFractions] = None
    last_fractions: Optional[TFractions] = None

    modes = (
        Mode(
            name=SIZE_MODE_SIZE,
            label='by size',
            tooltip='Compares data size of the directories.'
        ),
        Mode(
            name=SIZE_MODE_SIZE_NEW,
            label='by activity',
            tooltip=('Shows how many percent of the files in each directory '
                     'was modified in the past 30 days.')
        ),
    )

    def __init__(self):
        config = load_config()
        self.store = Store(
            config=config,
            on_config_change=self.on_config_change
        )
        self.load_directories()
        self.scan_start()
        super().__init__()

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
        logger.info('On init')
        self.menu = Menu(
            self,
            self.modes,
            parent=self.frame
        )
        self.menu.init(self.store.active_mode, self.store.directories)
        self.status_icon = StatusIcon(self)
        if self.store.config.show_setup:
            self.store.config.show_setup = False
            self.show_setup()
        self.tick_start()

    def set_active_mode(self, active_mode: str):
        self.store.active_mode = active_mode
        self.menu.update_radio_buttons(active_mode)
        self.update_icon()
        self.update_menu(pulse=False)

    def get_text(self, path: Path) -> str:
        if (self.store.config.mode == MODE_NAMED and
                path in self.store.config.named_dirs):
            return self.store.config.named_dirs[path]
        return path.name

    def get_tooltip(self, path: Path) -> str:
        fraction = self.store.fractions[path]
        if self.store.active_mode == SIZE_MODE_SIZE:
            s = f'{fraction:.2%} of the size of all configured directories'
        else:
            s = (f'{fraction:.2%} of the files in this directory was modified '
                 'in the past 30 days')
        return textwrap.fill(s)

    def show_menu(self, mouse_x: int, mouse_y: int):
        self.menu.popup_at(mouse_x, mouse_y)

    def show_setup(self):
        Setup(
            self.store.config,
            on_finish=self.on_setup_finish,
            parent=self.frame
        )

    def on_setup_finish(self, setup: Setup):
        self.store.config = setup.config
        save_config(self.store.config)
        self.reset_menu()
        self.update_icon()
        self.update_menu(pulse=True)

    def show_settings(self):
        Settings(
            self.store.config,
            self.on_settings_accept,
            parent=self.frame
        )

    def on_settings_accept(self, settings: Settings):
        self.store.config = settings.config
        save_config(self.store.config)
        self.reset_menu()
        self.update_icon()
        self.update_menu(pulse=True)

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
        if self._should_update():
            self.update_icon()
            self.update_menu(pulse=True)

    def _should_update(self) -> bool:
        if self.store.fractions == self.last_fractions:
            return False
        self.last_fractions = self.store.fractions
        return True

    def _create_icon_image(self) -> Image:
        slices_frac = list(self.store.percents.values())
        logger.info('Updating icon with slices %s', slices_frac)
        return draw_pie_chart(self.status_icon.icon_size, slices_frac)

    def _create_tooltip(self) -> str:
        return '\n'.join(
            '{text}: {fraction:.2%}'.format(
                text=self.get_text(path),
                fraction=fraction
            )
            for path, fraction in self.store.percents.items()
        )

    def update_icon(self):
        logger.info('Update icon')
        image = self._create_icon_image()
        tooltip = self._create_tooltip()
        self.status_icon.update(image, tooltip)

    def update_menu(self, pulse: bool):
        logger.info('Update icon (pulse = %s)', pulse)
        if self.store.directories:
            for path, d in self.store.directories.items():
                if d.size is None:
                    if pulse:
                        self.menu.pulse_progress_bar(path)
                else:
                    self.menu.update_progress_bar(
                        path,
                        self.store.fractions[path],
                        self.get_tooltip(path)
                    )
        if not any(self.store.pending.values()):
            self.menu.hide_spinner()

    def reset_menu(self):
        self.menu.reset(self.store.active_mode, self.store.directories)

    def quit(self):
        logger.info('Menu quit')
        super().quit()
        self.status_icon.destroy()
        self.menu.destroy()

    def on_quit(self):
        logger.info('App on_quit')
        self.tick_stop()
        self.scan_stop()


def main():
    app = Application()
    app.run()
