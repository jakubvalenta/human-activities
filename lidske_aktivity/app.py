import logging
import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import gi

from lidske_aktivity.lib import (Directory, FileSystem, init_file_system,
                                 scan_file_system)

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, Gtk  # noqa:E402  # isort:skip

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
        self.file_system = init_file_system(CACHE_PATH, root_path=ROOT_PATH)
        self.create_main_menu(self.file_system)
        self.create_context_menu()
        self.create_status_icon()
        scan_file_system(
            self.file_system,
            CACHE_PATH,
            self.on_directory_change)

    def do_activate(self):
        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title='Main Window')
        self.window.present()

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

    def create_main_menu(self, file_system: FileSystem) -> None:
        self.main_menu = Gtk.Menu()
        if file_system.directories:
            for directory in file_system.directories:
                progress_bar = self.create_progressbar(
                    self.main_menu,
                    text=directory.path.name,
                    pulse=True)
                self.progress_bars[directory.path] = progress_bar
        else:
            self.create_menu_item(self.main_menu, 'No directories found')
        self.main_menu.show_all()

    def on_directory_change(self, directory: Directory) -> None:
        self.file_system.size += directory.size
        if self.file_system.size:
            fraction = directory.size / self.file_system.size
        else:
            fraction = 0
        self.progress_bars[directory.path].set_fraction(fraction)

    def create_context_menu(self):
        self.context_menu = Gtk.Menu()
        self.create_menu_item(self.context_menu, 'About', self.on_about)
        self.create_menu_item(self.context_menu, 'Quit', self.on_quit)
        self.context_menu.show_all()

    def create_status_icon(self):
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
            activate_time=time)

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
