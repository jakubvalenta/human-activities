import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Tuple

import gi

from lidske_aktivity import __title__
from lidske_aktivity.gtk.lib import (
    RadioConfig, box_add, create_box, create_button, create_label,
    create_radio_group,
)
from lidske_aktivity.model import SIZE_MODES, TExtDirectories

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gdk, Gtk  # noqa:E402  # isort:skip

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def create_spinner(tooltip: str) -> Gtk.Spinner:
    spinner = Gtk.Spinner()
    spinner.set_tooltip_text(tooltip)
    spinner.start()
    spinner.show()
    return spinner


def create_window_box(window: Gtk.ApplicationWindow) -> Gtk.Box:
    window.set_border_width(10)
    box = create_box(spacing=6)
    window.add(box)
    return box


class ProgressBar(Gtk.ProgressBar):
    fraction: float = 0
    is_pulse: bool = True

    def __init__(self, i: int, text: str):
        super().__init__(text=text)
        self.set_show_text(True)
        self.set_pulse_step(1)
        self.get_style_context().add_class(f'bg-{i}')

    def set_fraction(self, fraction: float, tooltip: str):
        self.fraction = fraction
        super().set_fraction(fraction)
        self.set_tooltip_text(tooltip)

    def pulse(self):
        self.is_pulse = True
        self.set_tooltip_text('calculating...')
        super().pulse()


class Menu(Gtk.ApplicationWindow):
    title = __title__

    app: 'Application'
    active_mode: str
    box: Gtk.Box
    radio_buttons: Dict[str, Gtk.RadioButton]
    progress_bars: Dict[Path, ProgressBar]
    spinner: Gtk.MenuItem
    last_closed: float = 0
    _size: Tuple[int, int]

    def __init__(self, app: 'Application', parent: Gtk.Window):
        super().__init__(
            application=app.ui_app,
            modal=True,
            transient_for=parent,
            gravity=Gdk.Gravity.CENTER,
            resizable=False,
            decorated=False,
            skip_taskbar_hint=True,
            skip_pager_hint=True,
        )
        self.app = app

    def init(self, active_mode: str, ext_directories: TExtDirectories):
        self._init_window()
        if ext_directories:
            self._init_radio_buttons(active_mode)
            self._init_progress_bars(ext_directories)
        else:
            self._init_empty()
        self._init_spinner()
        self.connect('focus-out-event', self._on_focus_out)

    def _init_window(self):
        self.box = create_window_box(self)

    def _init_radio_buttons(self, active_mode: str):
        radio_configs = [
            RadioConfig(mode.name, mode.label, mode.tooltip)
            for mode in SIZE_MODES
        ]
        hbox = create_box(Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(hbox.get_style_context(), 'linked')
        self.radio_buttons = create_radio_group(
            radio_configs,
            active_value=active_mode,
            callback=self._on_radio_toggled,
            use_toggle_buttons=True
        )
        for radio_button in self.radio_buttons.values():
            box_add(hbox, radio_button)
        box_add(self.box, hbox)

    def _init_empty(self):
        label = create_label('No directories found')
        box_add(self.box, label)
        button = create_button('Open app setup', self._on_setup_button)
        box_add(self.box, button)

    def _init_progress_bars(self, ext_directories: TExtDirectories):
        self.progress_bars = {}
        for i, (path, ext_directory) in enumerate(ext_directories.items()):
            progress_bar = ProgressBar(text=ext_directory.label, i=i)
            box_add(self.box, progress_bar)
            self.progress_bars[path] = progress_bar

    def _init_spinner(self):
        self._size_remember()
        self.spinner = create_spinner('calculating...')
        box_add(self.box, self.spinner)

    def _empty(self):
        self.box.destroy()

    def pulse_progress_bar(self, path: Path):
        self.progress_bars[path].pulse()

    def update_progress_bar(self, path: Path, fraction: float, tooltip: str):
        self.progress_bars[path].set_fraction(fraction, tooltip)

    def hide_spinner(self):
        self.spinner.hide()
        self._size_restore()

    def reset(self, active_mode: str, ext_directories: TExtDirectories):
        self._empty()
        self.init(active_mode, ext_directories)

    def popup_at(self, mouse_x: int, mouse_y: int):
        self.set_position(Gtk.WindowPosition.CENTER)
        self.present()

    def _on_radio_toggled(self, mode: str):
        logger.info('Radio toggled: new mode = "%s"', mode)
        self.app.set_active_mode(mode)

    def update_radio_buttons(self, active_mode: str):
        pass

    def _on_setup_button(self):
        self.hide()
        self.app.show_setup()

    def _on_focus_out(self, widget: Gtk.Window, event: Gdk.EventFocus):
        self.hide()

    def _size_remember(self):
        self._size = self.get_size()

    def _size_restore(self):
        self.resize(*self._size)

    def destroy(self):
        pass
