import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any, Callable, Dict, Iterable, Optional

import gi

from lidske_aktivity import __version__
from lidske_aktivity.store import SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import GLib, Gdk, Gio, Gtk  # noqa:E402  # isort:skip

GLib.set_application_name('Lidské aktivity')

logger = logging.getLogger(__name__)


@dataclass
class RadioButtonConfig:
    name: str
    label: str
    tooltip: str


def create_vbox() -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)


def box_add(vbox: Gtk.Box, widget: Gtk.Widget):
    vbox.pack_start(widget, True, True, 0)
    vbox.show_all()


def create_progress_bar(text: str,
                        fraction: Optional[float] = None) -> Gtk.ProgressBar:
    progress_bar = Gtk.ProgressBar(text=text)
    if fraction is not None:
        progress_bar.set_fraction(fraction)
    progress_bar.set_show_text(True)
    progress_bar.set_pulse_step(1)
    return progress_bar


def create_radio_buttons(configs: Iterable[RadioButtonConfig],
                         active_name: str,
                         on_toggled: Callable) -> Gtk.Box:
    hbox = Gtk.Box()
    Gtk.StyleContext.add_class(hbox.get_style_context(), 'linked')
    group = None
    for config in configs:
        button = Gtk.RadioButton.new_with_label_from_widget(
            group,
            config.label
        )
        button.set_tooltip_text(config.tooltip)
        button.set_mode(False)
        if not group:
            group = button
        button.set_active(config.name == active_name)
        button.connect('toggled', on_toggled, config.name)
        box_add(hbox, button)
    return hbox


def create_spinner() -> Gtk.Spinner:
    spinner = Gtk.Spinner()
    spinner.start()
    spinner.show()
    return spinner


def create_window_box(window: Gtk.ApplicationWindow) -> Gtk.Box:
    window.set_border_width(10)
    vbox = create_vbox()
    window.add(vbox)
    return vbox


def create_menu_item(menu: Gtk.Menu,
                     label: str,
                     callback: Callable = None):
    menu_item = Gtk.MenuItem()
    menu_item.set_label(label)
    if callback:
        menu_item.connect('activate', callback)
    else:
        menu_item.set_sensitive(False)
    menu.append(menu_item)


def create_context_menu(on_about: Callable, on_quit: Callable) -> Gtk.Menu:
    context_menu = Gtk.Menu()
    create_menu_item(context_menu, 'About', on_about)
    create_menu_item(context_menu, 'Quit', on_quit)
    context_menu.show_all()
    return context_menu


def popup_menu(menu: Gtk.Menu,
               button: int = 1,
               time: Optional[int] = None):
    if time is None:
        time = Gtk.get_current_event_time()
    menu.popup(
        parent_menu_shell=None,
        parent_menu_item=None,
        func=None,
        data=None,
        button=button,
        activate_time=time
    )


def create_status_icon(on_main_menu: Callable,
                       on_context_menu: Callable) -> Gtk.StatusIcon:
    status_icon = Gtk.StatusIcon.new_from_stock(Gtk.STOCK_HOME)
    status_icon.set_tooltip_text('Lidské aktivity')
    # if not self.status_icon.is_embedded():
    #    raise AppError('Tray icon is not supported on this platform')
    status_icon.connect('activate', on_main_menu)
    status_icon.connect('popup-menu', on_context_menu)
    return status_icon


def show_about_dialog():
    about_dialog = Gtk.AboutDialog(
        modal=True,
        logo_icon_name='go-home',
        # logo_icon_name='application-exit',
        authors=['Jakub Valenta', 'Jiří Skála'],
        copyright='\u00a9 2018 Jakub Valena, Jiří Skála',
        license_type=Gtk.License.GPL_3_0,
        version=__version__,
        website='https://www.example.com'  # TODO
    )
    about_dialog.present()
    about_dialog.connect('response', on_about_response)


def on_about_response(dialog: Gtk.Dialog, response_id: int):
    dialog.destroy()


class Window(Gtk.ApplicationWindow):
    store: Store
    vbox: Gtk.Box
    progress_bars: Dict[Path, Gtk.ProgressBar]

    def __init__(self,
                 application: Gtk.Application,
                 store: Store,
                 *args,
                 **kwargs):
        super().__init__(
            *args,
            application=application,
            gravity=Gdk.Gravity.NORTH_EAST,
            resizable=False,
            decorated=False,
            skip_taskbar_hint=True,
            skip_pager_hint=True,
            **kwargs
        )
        self.store = store
        self.init_window()
        self.init_radio()
        self.init_progress_bars()
        self.init_spinner()
        self.connect('focus-out-event', self.on_focus_out)
        self.tick_start()

    def init_window(self):
        self.vbox = create_window_box(self)

    def init_radio(self):
        radio_button_configs = [
            RadioButtonConfig(
                name=SIZE_MODE_SIZE,
                label='by size',
                tooltip=(
                    'Each bar shows the fraction of the total root directory '
                    'size that the given directory occupies.'
                )
            ),
            RadioButtonConfig(
                name=SIZE_MODE_SIZE_NEW,
                label='by activity',
                tooltip=(
                    'Each bar shows the fraction of the size of the given '
                    'directory that was modified in the last 30 days.'
                )
            ),
        ]
        radio_buttons = create_radio_buttons(
            radio_button_configs,
            self.store.active_mode,
            self.on_radio_toggled
        )
        box_add(self.vbox, radio_buttons)

    def init_progress_bars(self):
        self.progress_bars = {}
        if not self.store.directories:
            label = Gtk.Label('No directories found')
            box_add(self.vbox, label)
            return
        for path, d in self.store.directories.items():
            progress_bar = create_progress_bar(
                text=path.name,
                fraction=self.store.fractions[path]
            )
            box_add(self.vbox, progress_bar)
            self.progress_bars[path] = progress_bar

    def init_spinner(self):
        self.size_remember()
        self.spinner = create_spinner()
        box_add(self.vbox, self.spinner)

    def on_radio_toggled(self, button: Gtk.Button, mode: str):
        self.store.set_active_mode(mode)
        self.on_tick(pulse=False)

    def tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self.tick)
        self.tick_thread.start()

    def tick_stop(self):
        self.tick_event_stop.set()
        self.tick_thread.join()
        logger.info('Tick stopped')

    def tick(self):
        while not self.tick_event_stop.is_set():
            logger.info('Tick')
            GLib.idle_add(self.on_tick)
            sleep(1)

    def on_tick(self, pulse: bool = True):
        logger.info('Updating progress bars')
        if self.store.directories:
            for path, d in self.store.directories.items():
                if d.size is None:
                    if pulse:
                        self.progress_bars[path].pulse()
                else:
                    self.progress_bars[path].set_fraction(
                        self.store.fractions[path]
                    )
        if not any(self.store.pending.values()):
            self.spinner.hide()
            self.size_restore()

    def on_focus_out(self, widget: Gtk.Window, event: Gdk.EventFocus):
        self.hide()

    def size_remember(self):
        self.size = self.get_size()

    def size_restore(self):
        self.resize(*self.size)


class Application(Gtk.Application):
    window: Gtk.ApplicationWindow = None
    store: Store
    on_quit: Callable
    context_menu: Gtk.Menu
    status_icon: Gtk.StatusIcon

    def __init__(self, store: Store, on_quit: Callable, *args, **kwargs):
        super().__init__(*args, application_id='org.example.myapp', **kwargs)
        self.store = store
        self.on_quit = on_quit  # type: ignore

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.context_menu = create_context_menu(
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        self.status_icon = create_status_icon(
            on_main_menu=self.on_main_menu,
            on_context_menu=self.on_context_menu
        )

    def do_activate(self):
        if not self.window:
            self.window = Window(application=self, store=self.store)

    def on_main_menu(self, status_icon: Gtk.StatusIcon):
        self.window.hide()
        geometry = status_icon.get_geometry()
        self.window.present()
        self.window.move(
            x=geometry.area.x - self.window.get_size().width,
            y=geometry.area.y + geometry.area.height
        )
        # TODO: What is the taskbar is at the bottom of the screen?

    def on_context_menu(self, icon: Any, button: int, time: int):
        self.window.hide()
        popup_menu(self.context_menu, button=button, time=time)

    def on_menu_about(self, param: Any):
        show_about_dialog()

    def on_menu_quit(self, param: Any):
        self.on_quit()
        if self.window:
            self.window.tick_stop()
        self.quit()


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.run()
