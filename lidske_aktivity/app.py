import logging
from pathlib import Path
from threading import Event

from lidske_aktivity import ui
from lidske_aktivity.config import (
    CACHE_PATH, MODE_CUSTOM, MODE_HOME, MODE_PATH, load_config,
)
from lidske_aktivity.directories import (
    init_directories_from_paths, init_directories_from_root_path,
    scan_directories,
)
from lidske_aktivity.store import Store

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


def main():
    config = load_config()
    if config.mode == MODE_HOME:
        directories = init_directories_from_root_path(
            CACHE_PATH,
            Path.home()
        )
    elif config.mode == MODE_PATH:
        directories = init_directories_from_root_path(
            CACHE_PATH,
            config.root_path
        )
    elif config.mode == MODE_CUSTOM:
        directories = init_directories_from_paths(
            CACHE_PATH,
            config.custom_dirs
        )
    else:
        raise AppError(f'Invalid mode config.mode')
    store = Store(directories=directories)
    scan_event_stop = Event()
    scan_thread = scan_directories(
        store.directories,
        cache_path=CACHE_PATH,
        callback=store.update,
        event_stop=scan_event_stop,
        test=config.test
    )

    def on_quit():
        scan_event_stop.set()
        scan_thread.join()
        logger.info('Scan stopped')

    ui.run_app(store, on_quit, config)
