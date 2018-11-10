import logging
import sys
from collections import namedtuple
from pathlib import Path
from typing import Callable, Optional

import gi

from lidske_aktivity.lib import list_home_dirs

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

XML = str(Path(__file__).parent / 'ui.xml')


Directory = namedtuple('Directory', ['path'])
Settings = namedtuple('Settings', ['directories'])


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

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.load_settings()
        self.create_main_menu()
        self.create_context_menu()
        self.create_status_icon()

    def do_activate(self):
        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title='Main Window')
        self.window.present()

    def load_settings(self):
        self.settings = Settings(directories=list(list_home_dirs()))

    @staticmethod
    def create_progressbar(menu: Gtk.Menu, text: str):
        menu_item = Gtk.MenuItem()
        menu_item.set_sensitive(False)
        progress_bar = Gtk.ProgressBar(text=text)
        progress_bar.set_fraction(0.2)
        progress_bar.set_show_text(True)
        menu_item.add(progress_bar)
        menu.append(menu_item)

    @staticmethod
    def create_menu_item(menu: Gtk.Menu,
                         label: str,
                         callback: Callable = None):
        menu_item = Gtk.MenuItem()
        menu_item.set_label(label)
        if callback:
            menu_item.connect('activate', callback)
        else:
            menu_item.set_sensitive(False)
        menu.append(menu_item)

    def create_main_menu(self):
        self.main_menu = Gtk.Menu()
        if self.settings.directories:
            for directory in self.settings.directories:
                self.create_progressbar(self.main_menu, directory.name)
        else:
            self.create_menu_item(self.main_menu, 'No directories found')
        self.main_menu.show_all()

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
