import logging
from typing import Callable

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    title: str
    frame = None

    def __init__(self,
                 title: str,
                 on_init: Callable,
                 on_quit: Callable,
                 *args,
                 **kwargs):
        self.title = title
        self.on_init = on_init
        self.on_quit = on_quit
        GLib.set_application_name(self.title)
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.window: Gtk.ApplicationWindow = None

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        self.on_init(self.frame)

    def do_activate(self) -> None:
        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self)
