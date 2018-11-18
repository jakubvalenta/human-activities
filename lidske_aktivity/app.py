import logging
import sys
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any, Dict, Optional

import gi

from lidske_aktivity import ui
from lidske_aktivity.config import CACHE_PATH, load_config
from lidske_aktivity.scan import init_directories, scan_directories

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

GLib.set_application_name('Lidské aktivity')


class AppError(Exception):
    pass


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.window: Gtk.ApplicationWindow = None
        self.progress_bars: Dict[Path, Gtk.ProgressBar] = {}

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        self.init_directories()
        self.main_menu = ui.create_main_menu()
        self.progress_bars = ui.create_progress_bars(
            self.main_menu,
            self.directories
        )
        self.spinner_menu_item = ui.create_spinner_menu_item(self.main_menu)
        self.context_menu = ui.create_context_menu(
            on_about=self.on_about,
            on_quit=self.on_quit
        )
        self.status_icon = ui.create_status_icon(
            on_main_menu=self.on_main_menu,
            on_context_menu=self.on_context_menu
        )
        self.scan_start()
        self.tick_start()

    def do_activate(self) -> None:
        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self)

    def init_directories(self) -> None:
        self.config = load_config()
        self.directories = init_directories(
            CACHE_PATH,
            root_path=self.config.root_path
        )
        self.pending = {path: True for path in self.directories.keys()}

    def scan_start(self) -> None:
        self.scan_event_stop = Event()
        self.scan_thread = scan_directories(
            self.directories,
            CACHE_PATH,
            self.on_scan,
            self.scan_event_stop,
            test=self.config.test
        )

    def scan_stop(self) -> None:
        self.scan_event_stop.set()
        self.scan_thread.join()
        logger.info('Scan stopped')

    def on_scan(self, path: Path, size: Optional[int]) -> None:
        self.directories[path] = size
        self.pending[path] = False

    def tick_start(self) -> None:
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self.tick)
        self.tick_thread.start()

    def tick_stop(self) -> None:
        self.tick_event_stop.set()
        self.tick_thread.join()
        logger.info('Tick stopped')

    def tick(self) -> None:
        while not self.tick_event_stop.is_set():
            logger.info('Tick')
            GLib.idle_add(self.on_tick)
            sleep(1)

    def on_tick(self) -> None:
        ui.update_progress_bars(
            self.progress_bars,
            self.directories,
            self.pending,
            self.spinner_menu_item
        )

    def on_main_menu(self, widget: Gtk.StatusIcon) -> None:
        ui.popup_menu(self.main_menu)

    def on_context_menu(self, icon: Any, button: int, time: int) -> None:
        ui.popup_menu(self.context_menu, button=button, time=time)

    def on_about(self, param: Any) -> None:
        ui.show_about_dialog()

    def on_quit(self, param: Any) -> None:
        self.scan_stop()
        self.tick_stop()
        self.quit()


def main():
    try:
        app = Application()
        app.run()
    except AppError:
        sys.exit(1)
