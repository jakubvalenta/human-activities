import logging
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial
from queue import Queue
from threading import Event, Thread, Timer
from typing import Any, Optional

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.config import Config, load_config, save_config
from lidske_aktivity.icon import draw_pie_chart_png, gen_random_slices
from lidske_aktivity.model import Directories, DirectoryViews, scan_directory

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    _interval: int
    _config: Config
    _directory_views: DirectoryViews

    _ui: Any
    _ui_app: Any
    _status_icon: Any

    _scan_event_stop: Event
    _scan_timer: Timer
    _redraw_event_stop: Optional[Event] = None
    _redraw_queue: Optional[Queue] = None
    _redraw_thread: Optional[Thread] = None

    def __init__(self, interval: int):
        self._interval = interval
        self._config = load_config()
        save_config(self._config)
        self._directory_views = DirectoryViews()

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

    def _load_directory_views(self):
        logger.info('Loading directory views')
        directories = Directories()
        named_dirs = self._config.list_effective_named_dirs()
        paths = list(named_dirs.keys())
        directories.clear()
        directories.load_from_db(paths)
        directories.create_missing(paths)
        directories.save()
        self._directory_views.config(
            self._config.unit,
            self._config.threshold_days_ago,
            named_dirs
        )
        self._directory_views.load(*directories)

    def _scan(self):
        self._load_directory_views()
        logger.info('Starting scan threads')
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path=path,
                    unit=self._config.unit,
                    threshold_days_ago=self._config.threshold_days_ago,
                    event_stop=self._scan_event_stop,
                    callback=partial(self._on_scan, pending=False),
                    test=self._config.test
                )
                for path in self._directory_views.keys()
            ]
            wait(futures)
        logger.info('All scan threads finished')
        if not self._scan_event_stop.is_set() and self._interval:
            self.scan_start(self._interval)
        else:
            logger.info('No further scanning scheduled')

    def _on_scan(self, *args, **kwargs):
        changed = self._directory_views.load(*args, **kwargs)
        if changed:
            self._redraw_trigger()

    def _scan_stop(self):
        self._scan_event_stop.set()
        self._scan_timer.cancel()
        logger.info('Scan thread stopped')

    def _redraw_start(self):
        logger.info('Starting redrawing thread')
        self._redraw_event_stop = Event()
        self._redraw_queue = Queue()
        self._redraw_thread = Thread(target=self._redraw)
        self._redraw_thread.start()

    def _redraw_trigger(self):
        if self._redraw_queue is not None:
            self._redraw_queue.put(None)

    def _redraw(self):
        while not self._redraw_event_stop.is_set():
            logger.info('Waiting for an item in the redrawing queue')
            self._redraw_queue.get()
            logger.info('Redrawing')
            self._ui.lib.call_tick(
                partial(
                    self._status_icon.update,
                    self._directory_views
                )
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
            self._ui.setup.Setup,
            self._config,
            self.set_config
        )

    def show_settings(self):
        self._ui_app.spawn_frame(
            self._ui.settings.Settings,
            self._config,
            self.set_config
        )

    def show_about(self):
        self._ui.about.show_about(
            image=draw_pie_chart_png(148, tuple(gen_random_slices())),
            title=__title__,
            version=__version__,
            copyright=__copyright__,
            uri=__uri__,
            authors=__authors__
        )

    def quit(self):
        logger.info('Menu quit')
        self._ui_app.quit()
        self._status_icon.destroy()

    def _on_quit(self):
        logger.info('App on_quit')
        self._redraw_stop()
        self._scan_stop()
