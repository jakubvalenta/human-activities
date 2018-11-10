import logging
import sys
from collections import namedtuple
from pathlib import Path
from typing import Callable

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
        self.create_menu()
        self.create_status_icon()

    def do_activate(self):
        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title='Main Window')
        self.window.present()

    def load_settings(self):
        self.settings = Settings(directories=list(list_home_dirs()))

    def create_progressbar(self, text: str):
        menu_item = Gtk.MenuItem()
        menu_item.set_sensitive(False)
        progress_bar = Gtk.ProgressBar(text=text)
        progress_bar.set_fraction(0.2)
        progress_bar.set_show_text(True)
        menu_item.add(progress_bar)
        self.menu.append(menu_item)

    def create_menu_item(self, label: str, callback: Callable = None):
        menu_item = Gtk.MenuItem()
        menu_item.set_label(label)
        if callback:
            menu_item.connect('activate', callback)
        else:
            menu_item.set_sensitive(False)
        self.menu.append(menu_item)

    def create_menu(self):
        self.menu = Gtk.Menu()

        if self.settings.directories:
            for directory in self.settings.directories:
                self.create_progressbar(directory.name)
        else:
            self.create_menu_item('No directories found')

        self.create_menu_item('About', self.on_about)
        self.create_menu_item('Quit', self.on_quit)

        self.menu.show_all()

    def create_status_icon(self):
        status_icon = Gtk.StatusIcon.new_from_stock(Gtk.STOCK_HOME)
        status_icon.set_tooltip_text('Lidské aktivity')
        # if not self.status_icon.is_embedded():
        #    raise AppError('Tray icon is not supported on this platform')
        status_icon.connect('popup-menu', self.on_menu)
        self.status_icon = status_icon

    def on_menu(self, icon, button, time):
        self.menu.popup(
            parent_menu_shell=None,
            parent_menu_item=None,
            func=None,
            data=None,
            button=button,
            activate_time=time)

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
