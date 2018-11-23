import logging
from threading import Event

from lidske_aktivity import ui
from lidske_aktivity.config import CACHE_PATH, load_config
from lidske_aktivity.directories import init_directories, scan_directories
from lidske_aktivity.store import Store

logger = logging.getLogger(__name__)


def main():
    config = load_config()
    directories = init_directories(CACHE_PATH, config.root_path)
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

    ui.run_app(store, on_quit)
