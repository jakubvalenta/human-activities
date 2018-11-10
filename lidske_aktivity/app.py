import logging
import sys
from pathlib import Path

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

XML = str(Path(__file__).parent / 'ui.xml')


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
        self.create_menu()
        self.create_status_icon()

    def do_activate(self):
        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title='Main Window')
        self.window.present()

    def create_menu(self):
        menu = Gtk.Menu()

        menu_item = Gtk.MenuItem()
        menu_item.set_sensitive(False)
        progress_bar = Gtk.ProgressBar(text='Foo')
        progress_bar.set_fraction(0.2)
        progress_bar.set_show_text(True)
        menu_item.add(progress_bar)
        menu.append(menu_item)

        menu_item = Gtk.MenuItem()
        menu_item.set_label('About')
        menu_item.connect('activate', self.on_about)
        menu.append(menu_item)

        menu_item = Gtk.MenuItem()
        menu_item.set_label('Quit')
        menu_item.connect('activate', self.on_quit)
        menu.append(menu_item)

        menu.show_all()
        self.menu = menu

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
