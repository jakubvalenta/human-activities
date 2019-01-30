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
    _directories: Directories
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
        self._directories = Directories()
        self._directory_views = DirectoryViews()

    def _load_directories(self):
        paths = self._config.effective_named_dirs.keys()
        self._directories.clear()
        self._directories.load(paths)
        self._directories.save()

    def _load_directory_views(self):
        self._directory_views.config(
            self._config.unit,
            self._config.threshold_days_ago,
            self._config.effective_named_dirs
        )
        self._directory_views.load(*self._directories)

    def run_ui(self, ui: Any):
        self._load_directories()
        self._load_directory_views()
        self._ui = ui
        self._ui.app.Application(self._on_init, self._on_quit).run()

    def scan(self):
        self._load_directories()
        self._scan_start()

    def _on_init(self, ui_app: Any):
        self._ui_app = ui_app
        logger.info('On init')
        self._status_icon = self._ui.status_icon.StatusIcon(self)
        if self._config.show_setup:
            self._config.show_setup = False
            self.show_setup()
        self._redraw_start()
        self._redraw_trigger()
        self._scan_start()

    def _scan_start(self):
        self._scan_event_stop = Event()

        def orchestrator():
            logger.info(f'Starting scan ochestrator')
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        scan_directory,
                        path=directory.path,
                        unit=self._config.unit,
                        threshold_days_ago=self._config.threshold_days_ago,
                        event_stop=self._scan_event_stop,
                        callback=partial(self._on_scan, pending=False),
                        test=self._config.test
                    )
                    for directory in self._directories
                ]
                wait(futures)
                logger.info('All scan threads finished')

                if not self._scan_event_stop.is_set() and self._interval:
                    logger.info(f'Setting new scan timer to {self._interval}s')
                    self._scan_timer = Timer(self._interval, orchestrator)
                    self._scan_timer.start()

        self._scan_timer = Timer(0, orchestrator)
        self._scan_timer.start()

    def _on_scan(self, *args, **kwargs):
        if self._directory_views:
            changed = self._directory_views.load(*args, **kwargs)
            if changed:
                self._redraw_trigger()

    def _scan_stop(self):
        self._scan_event_stop.set()
        self._scan_timer.cancel()
        logger.info('Scan orchestrator stopped')

    def _redraw_start(self):
        logger.info('Starting redrawing thread')
        self._redraw_event_stop = Event()
        self._redraw_queue = Queue()
        self._redraw_thread = Thread(target=self._redraw)
        self._redraw_thread.start()

    def _redraw_trigger(self):
        if self._redraw_queue:
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
        self._load_directories()
        self._load_directory_views()
        self._scan_start()
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
