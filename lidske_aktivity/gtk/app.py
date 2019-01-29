import logging
from typing import Callable, Optional, TypeVar

import gi

from lidske_aktivity import __application_id__, __title__

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Application(Gtk.Application):
    _window: Optional[Gtk.ApplicationWindow] = None

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        GLib.set_application_name(__title__)
        super().__init__(*args, application_id=__application_id__, **kwargs)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.on_init(self)

    def do_activate(self):
        if not self._window:
            self._window = Gtk.ApplicationWindow(application=self)

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, **kwargs, parent=self._window)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        super().quit()
