import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict

import gi

from lidske_aktivity.bitmap import TColor
from lidske_aktivity.gtk.lib import create_menu_item
from lidske_aktivity.model import TExtDirectories

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def create_spinner_menu_item(tooltip: str) -> Gtk.MenuItem:
    menu_item = Gtk.MenuItem()
    menu_item.set_sensitive(False)
    spinner = Gtk.Spinner()
    spinner.start()
    spinner.set_tooltip_text(tooltip)
    menu_item.add(spinner)
    menu_item.show_all()
    return menu_item


def create_main_menu() -> Gtk.Menu:
    return Gtk.Menu()


class ProgressBar(Gtk.MenuItem):
    bar: Gtk.ProgressBar
    color: TColor
    fraction: float = 0
    is_pulse: bool = True
    default_color: TColor = (147, 161, 161, 255)

    def __init__(self, text: str, color: TColor):
        super().__init__()
        self.set_sensitive(False)
        self.bar = Gtk.ProgressBar(text=text)
        self.bar.set_show_text(True)
        self.bar.set_pulse_step(1)
        self.add(self.bar)

    def set_fraction(self, fraction: float, tooltip: str):
        self.bar.set_fraction(fraction)
        self.bar.set_tooltip_text(tooltip)

    def pulse(self):
        self.is_pulse = True
        self.bar.set_tooltip_text('Calculating...')
        self.bar.pulse()


class Menu(Gtk.Menu):
    app: 'Application'
    active_mode: str
    radio_buttons: Dict[Path, Gtk.RadioButton]
    progress_bars: Dict[Path, ProgressBar]
    spinner: Gtk.MenuItem
    last_closed: float = 0

    def __init__(self, app: 'Application', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app

    def init(self, active_mode: str, ext_directories: TExtDirectories):
        if ext_directories:
            self._init_radio_buttons()
            self.update_radio_buttons(active_mode)
            self._init_progress_bars(ext_directories)
        else:
            self._init_empty()
        self._init_spinner()

    def _init_radio_buttons(self):
        self.radio_buttons = {}

    def _init_empty(self):
        create_menu_item(self, 'No directories found')

    def _init_progress_bars(self, ext_directories: TExtDirectories):
        self.progress_bars = {}
        for i, (path, ext_directory) in enumerate(ext_directories.items()):
            progress_bar = ProgressBar(
                text=ext_directory.label,
                color=ext_directory.color
            )
            self.progress_bars[path] = progress_bar
            self.append(progress_bar)
        self.show_all()

    def _init_spinner(self):
        self.spinner = create_spinner_menu_item('calculating...')
        self.append(self.spinner)

    def _empty(self):
        pass  # TODO: self.DestroyChildren()

    def pulse_progress_bar(self, path: Path):
        self.progress_bars[path].pulse()

    def update_progress_bar(self, path: Path, fraction: float, tooltip: str):
        self.progress_bars[path].set_fraction(fraction, tooltip)

    def hide_spinner(self):
        self.spinner.hide()

    def reset(self, active_mode: str, ext_directories: TExtDirectories):
        self._empty()
        self.init(active_mode, ext_directories)

    def popup_at(self, mouse_x: int, mouse_y: int):
        raise NotImplementedError

    def _on_radio_toggled(self, mode: str):
        logger.info('Radio toggled: new mode = "%s"', mode)
        self.app.set_active_mode(mode)

    def update_radio_buttons(self, active_mode: str):
        for mode, radio_button in self.radio_buttons.items():
            if mode == active_mode:
                radio_button.SetValue(True)
            else:
                radio_button.SetValue(False)

    def _on_setup_button(self, event):
        self.app.show_setup()

    def destroy(self):
        pass
