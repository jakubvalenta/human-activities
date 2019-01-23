import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial
from threading import Event, Thread
from typing import Any, List, Optional

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.config import Config, load_config, save_config
from lidske_aktivity.icon import draw_pie_chart_png, gen_random_slices
from lidske_aktivity.model import (
    Directories, DirectoryView, DirectoryViews, scan_directory,
)

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class Application:
    _config: Config
    _directories: Directories
    _directory_views: DirectoryViews

    _ui: Any
    _ui_app: Any
    _status_icon: Any
    _last_directory_views_list: Optional[List[DirectoryView]] = None

    _scan_event_stop: Event
    _scan_thread: Thread
    _tick_event_stop: Optional[Event] = None
    _tick_thread: Optional[Thread] = None

    def __init__(self, ui: Any):
        self._config = load_config()
        save_config(self._config)
        self._directories = Directories()
        self._directory_views = DirectoryViews()
        self._load_directories()
        self._ui = ui
        self._ui.app.Application(self._on_init, self._on_quit).run()

    def _load_directories(self):
        named_dirs = self._config.list_effective_named_dirs()
        paths = named_dirs.keys()
        self._directories.clear()
        self._directories.load(paths)
        self._directories.save()
        self._directory_views.config(
            self._config.unit,
            self._config.threshold_days_ago,
            named_dirs
        )
        self._directory_views.load(*self._directories)
        self._scan_start()

    def _on_init(self, ui_app: Any):
        self._ui_app = ui_app
        logger.info('On init')
        self._status_icon = self._ui.status_icon.StatusIcon(self)
        if self._config.show_setup:
            self._config.show_setup = False
            self.show_setup()
        self._tick_start()

    def _scan_start(self):
        self._scan_event_stop = Event()

        def orchestrator():
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        scan_directory,
                        path=directory.path,
                        unit=self._config.unit,
                        threshold_days_ago=self._config.threshold_days_ago,
                        event_stop=self._scan_event_stop,
                        callback=partial(
                            self._directory_views.load,
                            pending=False
                        ),
                        test=self._config.test
                    )
                    for directory in self._directories
                ]
                wait(futures)

        self._scan_thread = Thread(target=orchestrator)
        self._scan_thread.start()

    def _scan_stop(self):
        self._scan_event_stop.set()
        self._scan_thread.join()
        logger.info('Scan stopped')

    def _tick_start(self):
        self._tick_event_stop = Event()
        self._tick_thread = Thread(target=self._tick)
        self._tick_thread.start()

    def _tick_stop(self):
        if self._tick_event_stop is not None:
            self._tick_event_stop.set()
        if self._tick_thread is not None:
            self._tick_thread.join()
        logger.info('Tick stopped')

    def _tick(self):
        while not self._tick_event_stop.is_set():
            logger.debug('Tick')
            self._ui.lib.call_tick(self._update_status_icon)
            time.sleep(1)

    def _update_status_icon(self):
        directory_views_list = list(self._directory_views.values())
        if directory_views_list == self._last_directory_views_list:
            return
        self._last_directory_views_list = directory_views_list
        logger.info(
            'Updating icon with slices %s',
            [f'{fract:.2f}' for fract in self._directory_views.fractions]
        )
        self._status_icon.update(self._directory_views)

    def set_config(self, config: Config):
        self._config = config
        save_config(config)
        self._load_directories()
        self._update_status_icon()

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
            image=draw_pie_chart_png(148, list(gen_random_slices())),
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
        self._tick_stop()
        self._scan_stop()
