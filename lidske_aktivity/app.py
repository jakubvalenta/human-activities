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


class StatusIcon(Gtk.StatusIcon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Window(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.status_icon = None
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_file(XML)
        menu_model = builder.get_object('popup-menu')
        self.popup_menu = Gtk.Menu.new_from_model(menu_model)

    def do_activate(self):
        self.status_icon = Gtk.StatusIcon.new_from_stock(Gtk.STOCK_HOME)
        self.status_icon.set_tooltip_text('Lidské aktivity')
        # if not self.status_icon.is_embedded():
        #    raise AppError('Tray icon is not supported on this platform')
        self.status_icon.connect('popup-menu', self.on_popup_menu)

        # TODO: Remove this window
        if not self.window:
            self.window = Window(application=self, title="Main Window")
        self.window.present()

    def on_popup_menu(self, icon, button, time):
        self.popup_menu.popup(
            parent_menu_shell=None,
            parent_menu_item=None,
            func=None,
            data=None,
            button=button,
            activate_time=time)

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.present()

    def on_quit(self, action, param):
        self.quit()


def main():
    try:
        app = Application()
        app.run(sys.argv)
    except AppError:
        sys.exit(1)
