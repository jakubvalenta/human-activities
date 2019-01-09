import logging
from typing import Callable

import gi

from lidske_aktivity import __application_id__, __title__

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    frame = None

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        self.window: Gtk.ApplicationWindow = None
        GLib.set_application_name(__title__)
        super().__init__(*args, application_id=__application_id__, **kwargs)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.on_init(self.frame)

        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self)
    def do_activate(self):
