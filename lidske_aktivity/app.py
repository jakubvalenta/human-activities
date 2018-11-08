import gi  # isort:skip

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402


def main():
    window = Gtk.Window(title='Hello World')
    window.show()
    window.connect('destroy', Gtk.main_quit)
    Gtk.main()
