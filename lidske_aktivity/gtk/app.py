import logging
from typing import Callable, Optional

import gi

from lidske_aktivity import __application_id__, __title__

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    frame: Optional[Gtk.ApplicationWindow] = None

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        GLib.set_application_name(__title__)
        super().__init__(*args, application_id=__application_id__, **kwargs)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.on_init(self.frame)

    def do_activate(self):
        if not self.frame:
            self.frame = Gtk.ApplicationWindow(application=self)
