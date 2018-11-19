import logging
from pathlib import Path
from typing import Callable, Dict, Optional

import gi

from lidske_aktivity import __version__
from lidske_aktivity.scan import TDirectories, TFractions, TPending, TSizeModes

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)

TProgressBars = Dict[Path, Gtk.ProgressBar]


def create_progress_bar(text: str,
                        fraction: Optional[float] = None) -> Gtk.ProgressBar:
    progress_bar = Gtk.ProgressBar(text=text)
    if fraction is not None:
        progress_bar.set_fraction(fraction)
    progress_bar.set_show_text(True)
    progress_bar.set_pulse_step(1)
    return progress_bar


def box_add(vbox: Gtk.Box, widget: Gtk.Widget):
    vbox.pack_start(widget, True, True, 0)
    vbox.show_all()


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


def create_spinner() -> Gtk.Spinner:
    spinner = Gtk.Spinner()
    spinner.start()
    spinner.show()
    return spinner


def create_vbox() -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)


def create_radio_buttons(size_modes: TSizeModes,
                         active_name: str,
                         on_toggled: Callable) -> Gtk.Box:
    hbox = Gtk.Box()
    Gtk.StyleContext.add_class(hbox.get_style_context(), 'linked')
    group = None
    for name, size_mode in size_modes.items():
        button = Gtk.RadioButton.new_with_label_from_widget(
            group,
            size_mode.label
        )
        button.set_tooltip_text(size_mode.tooltip)
        button.set_mode(False)
        if not group:
            group = button
        button.set_active(name == active_name)
        button.connect('toggled', on_toggled, name)
        box_add(hbox, button)
    return hbox


def create_progress_bars(directories: TDirectories,
                         fractions: TFractions) -> TProgressBars:
    if not directories:
        return {}
    return {
        path: create_progress_bar(text=path.name, fraction=fractions[path])
        for path, d in directories.items()
    }


def add_progress_bars(vbox: Gtk.Box, progress_bars: TProgressBars):
    if progress_bars:
        for progress_bar in progress_bars.values():
            box_add(vbox, progress_bar)
    else:
        label = Gtk.Labe('No directories found')
        box_add(vbox, label)


def update_progress_bars(progress_bars: TProgressBars,
                         directories: TDirectories,
                         pending: TPending,
                         fractions: TFractions,
                         on_finished: Callable[[], None]):
    logger.info('Updating progress bars')
    some_pending = False
    if directories:
        for path, d in directories.items():
            if d.size is None:
                progress_bars[path].pulse()
            else:
                progress_bars[path].set_fraction(fractions[path])
            if pending[path]:
                some_pending = True
    if not some_pending:
        on_finished()


def create_context_menu(on_about: Callable, on_quit: Callable) -> Gtk.Menu:
    context_menu = Gtk.Menu()
    create_menu_item(context_menu, 'About', on_about)
    create_menu_item(context_menu, 'Quit', on_quit)
    context_menu.show_all()
    return context_menu


def create_status_icon(on_main_menu: Callable,
                       on_context_menu: Callable) -> Gtk.StatusIcon:
    status_icon = Gtk.StatusIcon.new_from_stock(Gtk.STOCK_HOME)
    status_icon.set_tooltip_text('Lidské aktivity')
    # if not self.status_icon.is_embedded():
    #    raise AppError('Tray icon is not supported on this platform')
    status_icon.connect('activate', on_main_menu)
    status_icon.connect('popup-menu', on_context_menu)
    return status_icon


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
