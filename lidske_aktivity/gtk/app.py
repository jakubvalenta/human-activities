import logging
from typing import Callable, Iterator, Optional

import gi

from lidske_aktivity import __application_id__, __title__
from lidske_aktivity.bitmap import MAX_COLORS, TColor, color_from_index

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk, GLib, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

T = TypeVar('T')


def gen_bg_color_rule(selector: str, color: TColor) -> str:
    r, g, b, _ = color
    return f'{selector} {{ background-color: rgb({r}, {g}, {b}) }}'


def gen_color_rules() -> Iterator[str]:
    for i in range(MAX_COLORS):
        yield gen_bg_color_rule(f'.bg-{i} progress', color_from_index(i))
    yield gen_bg_color_rule('progress.pulse', color_from_index(-1))


def gen_stylesheet() -> bytes:
    rules = gen_color_rules()
    s = ''.join(rules)
    return s.encode()


def load_css():
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    stylesheet = gen_stylesheet()
    provider.load_from_data(stylesheet)
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class Application(Gtk.Application):
    _frame: Optional[Gtk.ApplicationWindow] = None

    def __init__(self, on_init: Callable, on_quit: Callable, *args, **kwargs):
        self.on_init = on_init
        self.on_quit = on_quit
        GLib.set_application_name(__title__)
        super().__init__(*args, application_id=__application_id__, **kwargs)
        load_css()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.on_init(self)

    def do_activate(self):
        if not self._frame:
            self._frame = Gtk.ApplicationWindow(application=self)

    def spawn_frame(self, func: Callable[..., T], *args, **kwargs) -> T:
        return func(*args, **kwargs)

    def quit(self):
        logger.info('App quit')
        self.on_quit()
        super().quit()
