import logging
import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import gi

from lidske_aktivity.lib import (TDirectories, init_directories,
                                 scan_directories, sum_size)

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

CACHE_PATH = Path(__file__).parent / 'cache.csv'
ROOT_PATH = Path.home() / 'desktop'


class AppError(Exception):
    pass


class Window(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label = Gtk.Label('Hello world')
        label.show()
        self.add(label)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.window = None
        self.progress_bars: Dict[str, Gtk.ProgressBar] = {}

    def do_startup(self):
        Gtk.Application.do_startup(self)
        directories = init_directories(CACHE_PATH, root_path=ROOT_PATH)
        self.create_main_menu(directories)
        self.create_context_menu()
        self.create_status_icon()
        scan_directories(
            directories,
            CACHE_PATH,
            self.on_directories_change,
            test=True
        )

    def do_activate(self):
        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title='Main Window')
        self.window.present()

    def on_directories_change(self, directories: TDirectories) -> None:
        GLib.idle_add(self.update_progress_bars, directories)

    @staticmethod
    def create_progressbar(menu: Gtk.Menu,
                           text: str,
                           fraction: Optional[float] = None,
                           pulse: bool = False) -> Gtk.ProgressBar:
        menu_item = Gtk.MenuItem()
        menu_item.set_sensitive(False)
        progress_bar = Gtk.ProgressBar(text=text)
        if fraction is not None:
            progress_bar.set_fraction(fraction)
        if pulse:
            progress_bar.pulse()
        progress_bar.set_show_text(True)
        menu_item.add(progress_bar)
        menu.append(menu_item)
        return progress_bar

    @staticmethod
    def create_menu_item(menu: Gtk.Menu,
                         label: str,
                         callback: Callable = None) -> None:
        menu_item = Gtk.MenuItem()
        menu_item.set_label(label)
        if callback:
            menu_item.connect('activate', callback)
        else:
            menu_item.set_sensitive(False)
        menu.append(menu_item)

    def create_main_menu(self, directories: TDirectories) -> None:
        self.main_menu = Gtk.Menu()
        if directories:
            self.progress_bars = {
                path: self.create_progressbar(
                    self.main_menu,
                    text=path.name,
                    fraction=size,
                    pulse=True
                )
                for path, size in directories.items()
            }
        else:
            self.create_menu_item(self.main_menu, 'No directories found')
        self.main_menu.show_all()

    def update_progress_bars(self, directories: TDirectories) -> None:
        logger.warn(f'Updating progress bars')
        total_size = sum_size(directories)
        if total_size:
            for path, size in directories.items():
                if size is not None:
                    self.progress_bars[path].set_fraction(size / total_size)

    def create_context_menu(self) -> None:
        self.context_menu = Gtk.Menu()
        self.create_menu_item(self.context_menu, 'About', self.on_about)
        self.create_menu_item(self.context_menu, 'Quit', self.on_quit)
        self.context_menu.show_all()

    def create_status_icon(self) -> None:
        status_icon = Gtk.StatusIcon.new_from_stock(Gtk.STOCK_HOME)
        status_icon.set_tooltip_text('Lidské aktivity')
        # if not self.status_icon.is_embedded():
        #    raise AppError('Tray icon is not supported on this platform')
        status_icon.connect('activate', self.on_main_menu)
        status_icon.connect('popup-menu', self.on_context_menu)
        self.status_icon = status_icon

    @staticmethod
    def popup_menu(menu: Gtk.Menu,
                   button: int = 1,
                   time: Optional[int] = None):
        if time is None:
            time = Gtk.get_current_event_time()
        menu.popup(
            parent_menu_shell=None,
            parent_menu_item=None,
            func=None,
            data=None,
            button=button,
            activate_time=time
        )

    def on_main_menu(self, widget: Gtk.StatusIcon):
        self.popup_menu(self.main_menu)

    def on_context_menu(self, icon: any, button: int, time: int):
        self.popup_menu(self.context_menu, button=button, time=time)

    def on_about(self, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.present()

    def on_quit(self, param):
        self.quit()


def main():
    try:
        app = Application()
        app.run(sys.argv)
    except AppError:
        sys.exit(1)
