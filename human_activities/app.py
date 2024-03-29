import logging
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial
from queue import Queue
from threading import Event, Thread, Timer
from typing import Any, Optional

from human_activities import (
    __authors__,
    __copyright__,
    __title__,
    __uri__,
    __version__,
)
from human_activities.config import Config, load_config, save_config
from human_activities.icon import DEFAULT_FRACTIONS, draw_pie_chart_png
from human_activities.model import (
    Directories,
    Directory,
    DirectoryViews,
    scan_directory,
)

logger = logging.getLogger(__name__)


class Application:
    _config: Config

    _ui: Any
    _ui_app: Any
    _status_icon: Any

    _scan_event_stop: Optional[Event] = None
    _scan_timer: Optional[Timer] = None
    _redraw_event_stop: Optional[Event] = None
    _redraw_queue: Optional[Queue] = None
    _redraw_thread: Optional[Thread] = None

    def __init__(self):
        self._config = load_config()
        save_config(self._config)

    def run_ui(self, ui: Any) -> int:
        self._ui = ui
        ui_app = self._ui.app.Application(self._on_init, self._on_quit)
        return ui_app.run()

    def _on_init(self, ui_app: Any):
        self._ui_app = ui_app
        logger.info('On init')
        self._status_icon = self._ui.status_icon.StatusIcon(self)
        self._redraw_start()
        if self._config.show_setup:
            self._config.show_setup = False
            self.show_setup()
        else:
            self._scan_start(0)

    def _scan_start(self, interval_sec: int):
        logger.info('Starting scan timer in %ss', interval_sec)
        self._scan_event_stop = Event()
        self._scan_timer = Timer(interval_sec, self._scan)
        self._scan_timer.start()

    def _scan(self):
        logger.info('Creating directory views')
        configured_dirs = self._config.list_configured_dirs()
        directories = Directories(configured_dirs.paths)
        directory_views = DirectoryViews(
            self._config.unit, self._config.threshold_days_ago, configured_dirs
        )
        directory_views.load(*directories)
        logger.info('Drawing initial directory views')
        self._on_scan(directory_views, None)
        logger.info('Starting scan threads')
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path=path,
                    unit=self._config.unit,
                    threshold_days_ago=self._config.threshold_days_ago,
                    event_stop=self._scan_event_stop,
                    fd_command=self._config.fd_command,
                    fdignore_path=self._config.fdignore_path,
                    callback=partial(self._on_scan, directory_views),
                    test=self._config.test,
                )
                for path in directory_views.keys()
            ]
            wait(futures)
        logger.info('All scan threads finished')
        if not self._scan_event_stop.is_set() and self._config.interval_sec:
            self._scan_start(self._config.interval_sec)
        else:
            logger.info('No further scanning scheduled')

    def _on_scan(
        self,
        directory_views: DirectoryViews,
        directory: Optional[Directory] = None,
    ):
        if directory is not None:
            directory_views.load(directory, pending=False)
        if self._redraw_queue is not None:
            self._redraw_queue.put(directory_views.copy())

    def _scan_stop(self):
        if self._scan_event_stop is not None:
            self._scan_event_stop.set()
        if self._scan_timer is not None:
            self._scan_timer.cancel()
            self._scan_timer.join()
        logger.info('Scan thread stopped')

    def _redraw_start(self):
        logger.info('Starting redrawing thread')
        self._redraw_event_stop = Event()
        self._redraw_queue = Queue()
        self._redraw_thread = Thread(target=self._redraw)
        self._redraw_thread.start()

    def _redraw(self):
        while not self._redraw_event_stop.is_set():
            logger.info('Waiting for an item in the redrawing queue')
            directory_views = self._redraw_queue.get()
            if directory_views is None:
                logger.info('Redrawing received empty queue item')
                continue
            logger.info('Redrawing')
            self._status_icon.update(directory_views)

    def _redraw_stop(self):
        if self._redraw_event_stop is not None:
            self._redraw_event_stop.set()
        if self._redraw_queue is not None:
            self._redraw_queue.put(None)
        if self._redraw_thread is not None:
            self._redraw_thread.join()
        logger.info('Redrawing thread stopped')

    def set_config(self, config: Config):
        self._config = config
        save_config(config)
        self._scan_stop()
        self._scan_start(0)

    def show_setup(self):
        self._ui_app.spawn_frame(
            self._ui.setup.Setup, self._config.copy(), self.set_config
        )

    def show_settings(self):
        self._ui_app.spawn_frame(
            self._ui.settings.Settings, self._config.copy(), self.set_config
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
        self._scan_stop()
        self._redraw_stop()
        logger.info('Alive threads: %s', threading.enumerate())
