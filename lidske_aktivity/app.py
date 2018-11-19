import logging
import sys
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any, Dict

import gi

from lidske_aktivity import ui
from lidske_aktivity.config import CACHE_PATH, load_config
from lidske_aktivity.scan import (
    SIZE_MODES, Directory, init_directories, scan_directories,
)

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gdk, Gio, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

GLib.set_application_name('Lidské aktivity')


class AppError(Exception):
    pass


class Window(Gtk.ApplicationWindow):

    def __init__(self, application, *args, **kwargs):
        super().__init__(
            *args,
            application=application,
            gravity=Gdk.Gravity.NORTH_EAST,
            resizable=False,
            decorated=False,
            skip_taskbar_hint=True,
            skip_pager_hint=True,
            **kwargs
        )
        self.application = application

        self.set_border_width(10)
        self.vbox = ui.create_vbox()
        self.add(self.vbox)

        radio_buttons = ui.create_radio_buttons(
            SIZE_MODES,
            self.application.active_size_field,
            self.on_mode_toggled
        )
        ui.box_add(self.vbox, radio_buttons)

        self.progress_bars = ui.create_progress_bars(
            self.application.directories,
            self.application.calc_fractions(),
        )
        ui.add_progress_bars(self.vbox, self.progress_bars)

        self.size_remember()
        self.spinner = ui.create_spinner()
        ui.box_add(self.vbox, self.spinner)

        self.connect('focus-out-event', self.on_focus_out)

        self.tick_start()

    def on_mode_toggled(self, button: Gtk.Button, size_field: str):
        self.application.active_size_field = size_field
        self.on_tick()

    def tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self.tick)
        self.tick_thread.start()

    def tick_stop(self):
        self.tick_event_stop.set()
        self.tick_thread.join()
        logger.info('Tick stopped')

    def tick(self):
        while not self.tick_event_stop.is_set():
            logger.info('Tick')
            GLib.idle_add(self.on_tick)
            sleep(1)

    def on_tick(self):
        ui.update_progress_bars(
            self.progress_bars,
            self.application.directories,
            self.application.pending,
            self.application.calc_fractions(),
            self.on_scan_finished
        )

    def on_scan_finished(self):
        self.spinner.hide()
        self.size_restore()

    def on_focus_out(self, widget: Gtk.Window, event: Gdk.EventFocus):
        self.hide()

    def size_remember(self):
        self.size = self.get_size()

    def size_restore(self):
        self.resize(*self.size)


class Application(Gtk.Application):

    active_size_field = 'size'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.window: Gtk.ApplicationWindow = None
        self.progress_bars: Dict[Path, Gtk.ProgressBar] = {}

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.init_directories()
        self.context_menu = ui.create_context_menu(
            on_about=self.on_about,
            on_quit=self.on_quit
        )
        self.status_icon = ui.create_status_icon(
            on_main_menu=self.on_main_menu,
            on_context_menu=self.on_context_menu
        )
        self.scan_start()

    def do_activate(self):
        if not self.window:
            self.window = Window(application=self)

    def init_directories(self):
        self.config = load_config()
        self.directories = init_directories(
            CACHE_PATH,
            root_path=self.config.root_path
        )
        self.pending = {path: True for path in self.directories.keys()}

    def calc_fractions(self):
        return SIZE_MODES[self.active_size_field].calc_fractions(
            self.directories
        )

    def scan_start(self):
        self.scan_event_stop = Event()
        self.scan_thread = scan_directories(
            self.directories,
            CACHE_PATH,
            self.on_scan,
            self.scan_event_stop,
            test=self.config.test
        )

    def scan_stop(self):
        self.scan_event_stop.set()
        self.scan_thread.join()
        logger.info('Scan stopped')

    def on_scan(self, path: Path, directory: Directory):
        self.directories[path] = directory
        self.pending[path] = False

    def on_main_menu(self, status_icon: Gtk.StatusIcon):
        self.window.hide()
        geometry = status_icon.get_geometry()
        self.window.present()
        self.window.move(
            x=geometry.area.x - self.window.get_size().width,
            y=geometry.area.y + geometry.area.height
        )
        # TODO: What is the taskbar is at the bottom of the screen?

    def on_context_menu(self, icon: Any, button: int, time: int):
        self.window.hide()
        ui.popup_menu(self.context_menu, button=button, time=time)

    def on_about(self, param: Any):
        ui.show_about_dialog()

    def on_quit(self, param: Any):
        self.scan_stop()
        if self.window:
            self.window.tick_stop()
        self.quit()


def main():
    try:
        app = Application()
        app.run()
    except AppError:
        sys.exit(1)
