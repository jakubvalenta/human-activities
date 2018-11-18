import logging
from typing import Callable, List, Optional

import gi

from lidske_aktivity.scan import TDirectories, TPending, sum_size

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_progressbar(menu: Gtk.Menu,
                       text: str,
                       fraction: Optional[float] = None) -> Gtk.ProgressBar:
    menu_item = Gtk.MenuItem()
    menu_item.set_sensitive(False)
    progress_bar = Gtk.ProgressBar(text=text)
    if fraction is not None:
        progress_bar.set_fraction(fraction)
    progress_bar.set_show_text(True)
    progress_bar.set_pulse_step(1)
    menu_item.add(progress_bar)
    menu.append(menu_item)
    return progress_bar


def create_menu_item(menu: Gtk.Menu,
                     label: str,
                     callback: Callable = None) -> None:
    menu_item = Gtk.MenuItem()
    menu_item.set_label(label)
    if callback:
        menu_item.connect('activate', callback)
    else:
        menu_item.set_sensitive(False)
    menu.append(menu_item)


def create_main_menu() -> Gtk.Menu:
    return Gtk.Menu()


def create_progress_bars(main_menu: Gtk.Menu,
                         directories: TDirectories) -> List[Gtk.ProgressBar]:
    if directories:
        progress_bars = {
            path: create_progressbar(main_menu, text=path.name, fraction=size)
            for path, size in directories.items()
        }
    else:
        progress_bars = {}
        create_menu_item(main_menu, 'No directories found')
    main_menu.show_all()
    return progress_bars


def update_progress_bars(progress_bars: List[Gtk.ProgressBar],
                         directories: TDirectories,
                         pending: TPending) -> None:
    logger.info('Updating progress bars')
    total_size = sum_size(directories)
    if total_size:
        for path, size in directories.items():
            if pending[path]:
                progress_bars[path].pulse()
            elif size is not None:
                progress_bars[path].set_fraction(size / total_size)


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
