import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Callable, Dict, Iterable, Iterator, List, Optional

import wx
import wx.adv

from lidske_aktivity import __version__
from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_PATH, MODES, Config, save_config,
)
from lidske_aktivity.store import SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store

logger = logging.getLogger(__name__)


@dataclass
class RadioButtonConfig:
    name: str
    label: str
    tooltip: str


def create_sizer(parent: wx.Window,
                 orientation: int = wx.VERTICAL,
                 *args,
                 **kwargs) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    if isinstance(parent, wx.Sizer):
        parent.Add(sizer, *args, **kwargs)
    else:
        parent.SetSizer(sizer)
        parent.SetAutoLayout(1)
        sizer.Fit(parent)
    return sizer


def on_radio_update_ui(event):
    button = event.GetEventObject()
    value = button.GetValue()
    event.Enable(not value)


def create_label(parent: wx.Window, text: str) -> wx.StaticText:
    return wx.StaticText(parent, label=text)


def create_button(parent: wx.Window,
                  panel: wx.Panel,
                  label: str,
                  callback: Callable) -> wx.Button:
    button = wx.Button(panel, wx.ID_ANY, label)
    parent.Bind(wx.EVT_BUTTON, callback, id=button.GetId())
    return button


def create_text_control(parent: wx.Window,
                        value: str,
                        callback: Callable) -> wx.TextCtrl:
    text_control = wx.TextCtrl(parent, value=value)
    parent.Bind(wx.EVT_TEXT, callback, text_control)
    return text_control


def choose_dir(parent: wx.Window, callback: Callable[[str], None]):
    dialog = wx.DirDialog(
        parent,
        'Choose a directory:',
        style=wx.DD_DIR_MUST_EXIST
        # TODO: Fill in current dir
    )
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
        callback(path)


class Gauge(wx.Window):
    fraction: float = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, size=(-1, 5), **kwargs)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def set_fraction(self, fraction: float):
        self.fraction = fraction
        self.Refresh()

    def pulse(self):
        pass  # TODO: Add pulse support

    def on_paint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen('#ffffff', 1, wx.TRANSPARENT))
        w_fg = round(w * self.fraction)
        w_bg = w - w_fg
        dc.SetBrush(wx.Brush('#268bd2'))
        dc.DrawRectangle(0, 0, w_fg, h)
        dc.SetBrush(wx.Brush('#93a1a1'))
        dc.DrawRectangle(w_fg, 0, w_bg, h)


def create_progress_bar(parent: wx.Window,
                        fraction: Optional[float] = None) -> Gauge:
    progress_bar = Gauge(parent=parent)
    if fraction is not None:
        progress_bar.set_fraction(fraction)
    return progress_bar


def create_radio_buttons(window: wx.Window,
                         parent: wx.Window,
                         configs: Iterable[RadioButtonConfig],
                         active_name: str,
                         on_toggled: Callable) -> Iterator[wx.ToggleButton]:
    grid = wx.GridSizer(cols=2)
    for config in configs:
        button = wx.ToggleButton(
            parent=window,
            label=config.label,
        )
        button.SetValue(config.name == active_name)
        button.Bind(
            wx.EVT_TOGGLEBUTTON,
            partial(on_toggled, button=button, mode=config.name)
        )
        button.Bind(
            wx.EVT_UPDATE_UI,
            on_radio_update_ui,
        )
        grid.Add(button)
        yield button
    parent.Add(grid)


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self,
                 on_main_menu: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        super().__init__(wx.adv.TBI_DOCK)

        icon = wx.Icon()
        icon.LoadFile('/usr/share/icons/Adwaita/16x16/actions/go-home.png')
        self.SetIcon(icon)

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_main_menu)
        self.Bind(wx.EVT_MENU, on_settings, id=wx.ID_SETUP)
        self.Bind(wx.EVT_MENU, on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, on_quit, id=wx.ID_EXIT)

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        menu.Append(wx.ID_SETUP, '&Settings', ' Configure this program')
        menu.Append(wx.ID_ABOUT, '&About', ' Information about this program')
        menu.Append(wx.ID_EXIT, 'E&xit', ' Terminate the program')
        return menu


class AboutBox(wx.Dialog):
    def __init__(self, parent: wx.Frame):
        super().__init__()
        self.Create(parent, id=-1, title='About Lidské aktivity')
        # TODO: Add about icon

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = create_label(self, text='Lidské aktivity')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, '\u00a9 2018 Jakub Valena, Jiří Skála')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, 'License: GNU General Public License')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, __version__)
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        # TODO: Fill website
        label = create_label(self, 'https://www.example.com')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)


class Settings(wx.Dialog):
    grid_: None = Optional[wx.GridSizer]
    panel: wx.Panel
    sizer: wx.Sizer
    border_sizer: wx.Sizer
    mode_radios: Dict[str, wx.RadioButton]
    root_path_panel: wx.Sizer
    root_path_control: wx.TextCtrl
    list_box: wx.ListBox
    button_panel: wx.Panel

    def __init__(self, parent: wx.Frame, config: Config):
        super().__init__()
        self.Create(parent, id=-1, title='Settings of Lidské aktivity')
        self.config = config
        self.init_window()
        self.create_mode_radios()
        self.add_mode_radio(MODE_HOME)
        self.add_mode_radio(MODE_PATH)
        self.init_root_path_control()
        self.add_mode_radio(MODE_CUSTOM)
        self.init_custom_dirs()
        self.init_dialog_buttons()
        self.toggle_controls()
        self.fit()

    def init_window(self):
        self.panel = wx.Panel(self)
        self.border_sizer = create_sizer(self.panel)
        self.sizer = create_sizer(
            self.border_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

    def create_mode_radios(self):
        label = create_label(self, 'Scan mode')
        self.sizer.Add(label, flag=wx.ALL, border=5)
        self.mode_radios = {}
        for i, (mode, label) in enumerate(MODES.items()):
            if i == 0:
                kwargs = {'style': wx.RB_GROUP}
            else:
                kwargs = {}
            radio = wx.RadioButton(self.panel, label=label, **kwargs)
            radio.Bind(wx.EVT_RADIOBUTTON, self.on_radio_toggle)
            if mode == self.config.mode:
                radio.SetValue(True)
            self.mode_radios[mode] = radio

    def add_mode_radio(self, mode: str):
        self.sizer.Add(self.mode_radios[mode], flag=wx.ALL, border=5)

    def init_root_path_control(self):
        self.root_path_panel = wx.Panel(self.panel)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.root_path_control = create_text_control(
            self.root_path_panel,
            value=str(self.config.root_path),
            callback=self.on_root_path_text
        )
        hbox.Add(self.root_path_control, flag=wx.EXPAND | wx.RIGHT, border=10)
        button = create_button(
            self,
            self.root_path_panel,
            'Choose',
            self.on_root_path_button
        )
        hbox.Add(button, proportion=0.6, flag=wx.EXPAND)
        self.root_path_panel.SetSizer(hbox)
        self.sizer.Add(self.root_path_panel, flag=wx.EXPAND)

    def init_custom_dirs(self):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.init_custom_dirs_listbox()
        hbox.Add(self.listbox, wx.ID_ANY, flag=wx.EXPAND | wx.RIGHT, border=10)
        self.init_custom_dirs_buttons()
        hbox.Add(self.button_panel, proportion=0.6, flag=wx.EXPAND)
        self.sizer.Add(hbox, flag=wx.EXPAND)

    def toggle_controls(self):
        if self.config.mode == MODE_PATH:
            self.root_path_panel.Enable()
        else:
            self.root_path_panel.Disable()
        if self.config.mode == MODE_CUSTOM:
            self.listbox.Enable()
            self.button_panel.Enable()
        else:
            self.listbox.Disable()
            self.button_panel.Disable()

    def init_custom_dirs_listbox(self):
        self.listbox = wx.ListBox(self.panel)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_custom_dir_change)
        for custom_dir in self.config.custom_dirs:
            self.listbox.Append(str(custom_dir))

    def init_custom_dirs_buttons(self):
        self.button_panel = wx.Panel(self.panel)
        vbox = wx.BoxSizer(wx.VERTICAL)
        for i, (label, callback) in enumerate([
                ('New', self.on_custom_dir_new),
                ('Change', self.on_custom_dir_change),
                ('Delete', self.on_custom_dir_delete),
                ('Clear', self.on_custom_dirs_clear),
        ]):
            button = create_button(self, self.button_panel, label, callback)
            if i == 0:
                vbox.Add(button)
            else:
                vbox.Add(button, 0, flag=wx.TOP, border=5)
        self.button_panel.SetSizer(vbox)

    def init_dialog_buttons(self):
        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        self.sizer.Add(button_sizer, flag=wx.TOP, border=10)

    def fit(self):
        self.border_sizer.Fit(self.panel)
        self.border_sizer.Fit(self)
        self.Layout()
        self.Centre()

    def on_radio_toggle(self, event):
        for mode, radio in self.mode_radios.items():
            if radio.GetValue():
                self.config.mode = mode
        self.toggle_controls()

    def on_root_path_text(self, event):
        self.config.root_path = Path(event.GetString())

    def on_root_path_button(self, event):
        def callback(path_str: str):
            self.config.root_path = Path(path_str)
            self.root_path_control.SetValue(path_str)

        choose_dir(self, callback)

    def on_custom_dir_change(self, event):
        def callback(path_str: str):
            sel = self.listbox.GetSelection()
            self.listbox.Delete(sel)
            item_id = self.listbox.Insert(path_str, sel)
            self.config.custom_dirs[sel] = Path(path_str)
            self.listbox.SetSelection(item_id)

        choose_dir(self, callback)

    def on_custom_dir_new(self, event):
        def callback(path_str: str):
            self.config.custom_dirs.append(Path(path_str))
            self.listbox.Append(path_str)

        choose_dir(self, callback)

    def on_custom_dir_delete(self, event):
        sel = self.listbox.GetSelection()
        if sel != -1:
            del self.config.custom_dirs[sel]
            self.listbox.Delete(sel)

    def on_custom_dirs_clear(self, event):
        self.config.custom_dirs[:] = []
        self.listbox.Clear()


class Window(wx.PopupTransientWindow):
    store: Store
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[Path, wx.Gauge]

    def __init__(self,
                 store: Store,
                 parent: wx.Window,
                 *args, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)
        self.store = store
        self.init_window()
        self.init_radio()
        self.init_progress_bars()
        self.init_spinner()
        self.tick_start()
        self.fit()

    def init_window(self):
        self.panel = wx.Panel(self)
        self.border_sizer = create_sizer(self.panel)
        self.sizer = create_sizer(
            self.border_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

    def fit(self):
        self.border_sizer.Fit(self.panel)
        self.border_sizer.Fit(self)
        self.Layout()

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
        self.radio_buttons = list(create_radio_buttons(
            window=self,
            parent=self.sizer,
            configs=radio_button_configs,
            active_name=self.store.active_mode,
            on_toggled=self.on_radio_toggled
        ))

    def init_progress_bars(self):
        self.progress_bars = {}
        if not self.store.directories:
            label = create_label(self, 'No directories found')
            self.sizer.Add(label)
            return
        self.sizer.AddSpacer(5)
        paths = self.store.directories.keys()
        for i, path in enumerate(paths):
            label = create_label(self, path.name)
            progress_bar = create_progress_bar(
                parent=self,
                fraction=self.store.fractions[path]
            )
            self.sizer.Add(label, flag=wx.EXPAND | wx.BOTTOM, border=3)
            self.sizer.Add(progress_bar, flag=wx.EXPAND | wx.BOTTOM, border=5)
            self.progress_bars[path] = progress_bar

    def init_spinner(self):
        self.spinner = create_label(self, 'Processing...')
        self.sizer.Add(self.spinner, flag=wx.TOP, border=5)

    def on_radio_toggled(self, event, button: wx.ToggleButton, mode: str):
        self.store.set_active_mode(mode)
        for other_button in self.radio_buttons:
            if other_button != button:
                other_button.SetValue(False)
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
            wx.CallAfter(self.on_tick)
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
            self.spinner.Hide()
            self.fit()

    def ProcessLeftDown(self, evt):
        logger.info('ProcessLeftDown: %s' % evt.GetPosition())
        return wx.PopupTransientWindow.ProcessLeftDown(self, evt)


class Application(wx.App):
    window: Window
    store: Store
    on_quit: Callable
    status_icon: wx.adv.TaskBarIcon

    def __init__(self,
                 store: Store,
                 on_quit: Callable,
                 *args,
                 **kwargs):
        self.store = store
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title='Foo')
        self.init_window()
        self.status_icon = TaskBarIcon(
            on_main_menu=self.on_main_menu,
            on_settings=self.on_menu_settings,
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        return True

    def init_window(self):
        self.window = Window(store=self.store, parent=self.frame)

    def destroy_window(self):
        self.window.Destroy()
        self.window.tick_stop()

    def on_main_menu(self, event):
        mouse_x, mouse_y = wx.GetMousePosition()
        display_id = wx.Display.GetFromWindow(self.window)
        display = wx.Display(display_id)
        _, _, screen_w, screen_h = display.GetClientArea()
        window_w, window_h = self.window.GetSize()
        SCREEN_MARGIN = 10
        window_x = min(
            mouse_x,
            max(screen_w - window_w - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        window_y = min(
            mouse_y,
            max(screen_h - window_h - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        self.window.SetPosition((window_x, window_y))
        self.window.Popup()

    def on_menu_settings(self, event):
        settings = Settings(self.frame, self.store.config)
        val = settings.ShowModal()
        if val == wx.ID_OK:
            self.store.config = settings.config
            self.destroy_window()
            self.init_window()
            save_config(self.store.config)
        settings.Destroy()

    def on_menu_about(self, event):
        about = AboutBox(self.frame)
        about.ShowModal()
        about.Destroy()

    def on_menu_quit(self, event):
        self.status_icon.Destroy()
        self.window.Destroy()
        self.frame.Destroy()

    def OnExit(self):
        self.on_quit()
        self.window.tick_stop()
        super().OnExit()
        return True


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
