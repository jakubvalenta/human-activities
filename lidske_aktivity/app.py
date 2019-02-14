import logging
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial
from queue import Queue
from threading import Event, Thread, Timer
from typing import Any, Optional

from lidske_aktivity import (
    __authors__,
    __copyright__,
    __title__,
    __uri__,
    __version__,
)
from lidske_aktivity.config import Config, load_config, save_config
from lidske_aktivity.icon import DEFAULT_FRACTIONS, draw_pie_chart_png
from lidske_aktivity.model import Directories, DirectoryViews, scan_directory

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    _interval: int
    _config: Config

    _ui: Any
    _ui_app: Any
    _status_icon: Any

    _scan_event_stop: Optional[Event] = None
    _scan_timer: Optional[Timer] = None
    _redraw_event_stop: Optional[Event] = None
    _redraw_queue: Optional[Queue] = None
    _redraw_thread: Optional[Thread] = None

    def __init__(self, interval: int):
        self._interval = interval
        self._config = load_config()
        save_config(self._config)

    def run_ui(self, ui: Any):
        self._ui = ui
        self._ui.app.Application(self._on_init, self._on_quit).run()

    def _on_init(self, ui_app: Any):
        self._ui_app = ui_app
        logger.info('On init')
        self._status_icon = self._ui.status_icon.StatusIcon(self)
        self._redraw_start()
        if self._config.show_setup:
            self._config.show_setup = False
            self.show_setup()
        else:
            self.scan_start()

    def scan_start(self, interval: int = 0):
        logger.info(f'Starting scan timer in %ss', interval)
        self._scan_event_stop = Event()
        self._scan_timer = Timer(interval, self._scan)
        self._scan_timer.start()

    def _create_directory_views(self):
        logger.info('Creating directory views')
        directories = Directories()
        named_dirs = self._config.list_effective_named_dirs()
        paths = list(named_dirs.keys())
        directories.clear()
        directories.load_from_db(paths)
        directories.create_missing(paths)
        directories.save()
        directory_views = DirectoryViews()
        directory_views.config(
            self._config.unit, self._config.threshold_days_ago, named_dirs
        )
        directory_views.load(*directories)
        return directory_views

    def _scan(self):
        directory_views = self._create_directory_views()
        logger.info('Starting scan threads')
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path=path,
                    unit=self._config.unit,
                    threshold_days_ago=self._config.threshold_days_ago,
                    event_stop=self._scan_event_stop,
                    callback=partial(self._on_scan, directory_views),
                    test=self._config.test,
                )
                for path in directory_views.keys()
            ]
            wait(futures)
        logger.info('All scan threads finished')
        if not self._scan_event_stop.is_set() and self._interval:
            self.scan_start(self._interval)
        else:
            logger.info('No further scanning scheduled')

    def _on_scan(self, directory_views: DirectoryViews, directory):
        directory_views.load(directory, pending=False)
        self._redraw_trigger(directory_views.copy())

    def _scan_stop(self):
        if self._scan_event_stop is not None:
            self._scan_event_stop.set()
        if self._scan_timer is not None:
            self._scan_timer.cancel()
        logger.info('Scan thread stopped')

    def _redraw_start(self):
        logger.info('Starting redrawing thread')
        self._redraw_event_stop = Event()
        self._redraw_queue = Queue()
        self._redraw_thread = Thread(target=self._redraw)
        self._redraw_thread.start()

    def _redraw_trigger(
        self, directory_views: Optional[DirectoryViews] = None
    ):
        if self._redraw_queue is not None:
            self._redraw_queue.put(directory_views)

    def _redraw(self):
        while not self._redraw_event_stop.is_set():
            logger.info('Waiting for an item in the redrawing queue')
            directory_views = self._redraw_queue.get()
            if directory_views is None:
                logger.info('Redrawing received empty queue item')
                continue
            logger.info('Redrawing')
            self._ui.lib.call_tick(
                partial(self._status_icon.update, directory_views)
            )

    def _redraw_stop(self):
        if self._redraw_event_stop is not None:
            self._redraw_event_stop.set()
        self._redraw_trigger()
        if self._redraw_thread is not None:
            self._redraw_thread.join()
        logger.info('Redrawing thread stopped')

    def set_config(self, config: Config):
        self._config = config
        save_config(config)
        self._scan_stop()
        self.scan_start()
        self._redraw_trigger()

    def show_setup(self):
        self._ui_app.spawn_frame(
            self._ui.setup.Setup, self._config, self.set_config
        )

    def show_settings(self):
        self._ui_app.spawn_frame(
            self._ui.settings.Settings, self._config, self.set_config
        )

    def show_about(self):
        self._ui.about.show_about(
            image=draw_pie_chart_png(148, DEFAULT_FRACTIONS),
            title=__title__,
            version=__version__,
            copyright=__copyright__,
            uri=__uri__,
            authors=__authors__,
        )

    def quit(self):
        logger.info('Menu quit')
        self._ui_app.quit()
        self._status_icon.destroy()

    def _on_quit(self):
        logger.info('App on_quit')
        self._redraw_stop()
        self._scan_stop()
