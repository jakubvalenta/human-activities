import logging
from pathlib import Path
from threading import Event, Thread

from lidske_aktivity import ui
from lidske_aktivity.config import (
    CACHE_PATH, MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, load_config,
)
from lidske_aktivity.directories import (
    init_directories_from_paths, init_directories_from_root_path,
    scan_directories,
)
from lidske_aktivity.store import Store

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    store: Store
    scan_event_stop: Event
    scan_thread: Thread

    def __init__(self):
        config = load_config()
        self.store = Store(
            config=config,
            on_config_change=self.on_config_change
        )
        self.load_directories()
        self.scan_start()
        ui.run_app(self.store, self.scan_stop)

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
                self.store.config.named_dirs.values()
            )
        else:
            raise AppError(f'Invalid mode config.mode')
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


def main():
    Application()
