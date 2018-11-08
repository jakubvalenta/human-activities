import gi  # isort:skip

gi.require_version('Gtk', '3.0')

import logging  # noqa:E402
import sys  # noqa:E402

from gi.repository import Gtk  # noqa:E402

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


class App:
    def __init__(self):
        self.status_icon = Gtk.StatusIcon()
        self.status_icon.set_from_stock(Gtk.STOCK_HOME)
        self.status_icon.connect('popup-menu', self.right_click_event)
        self.status_icon.set_tooltip_text('Lidské aktivity')
        #if not self.status_icon.is_embedded():
        #    raise AppError('Tray icon is not supported on this platform')

    def right_click_event(self, icon, button, time):
        self.menu = Gtk.Menu()

        about = Gtk.MenuItem()
        about.set_label('About')
        quit = Gtk.MenuItem()
        quit.set_label('Quit')

        about.connect('activate', self.show_about_dialog)
        quit.connect('activate', Gtk.main_quit)

        self.menu.append(about)
        self.menu.append(quit)

        self.menu.show_all()

        def pos(menu, icon):
            return (Gtk.Status_Icon.position_menu(menu, icon))

        self.menu.popup(None, None, pos, self.status_icon, button, time)

    def show_about_dialog(self, widget):
        about_dialog = Gtk.AboutDialog()

        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name('Status_Icon Example')
        about_dialog.set_version('1.0')
        about_dialog.set_authors(['Andrew Steele'])

        about_dialog.run()
        about_dialog.destroy()


def main():
    try:
        App()
        Gtk.main()
    except AppError:
        sys.exit(1)
