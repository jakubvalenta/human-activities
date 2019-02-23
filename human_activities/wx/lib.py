import io
import logging
from functools import partial
from typing import Callable, Dict, Iterable, NamedTuple, Optional, Union

import wx
import wx.lib.filebrowsebutton
from PIL import Image

from human_activities import texts
from human_activities.config import NamedDirs
from human_activities.utils.func import after

logger = logging.getLogger(__name__)


def new_id_ref_compat():
    """A wrapper around wx.NewIdRef() compatible with wxPython < 4.0.3"""
    try:
        return wx.NewIdRef()
    except AttributeError:
        return wx.NewId()


def create_sizer(
    parent: Union[wx.Sizer, wx.Panel],
    orientation: int = wx.VERTICAL,
    *args,
    **kwargs,
) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    if isinstance(parent, wx.Sizer):
        parent.Add(sizer, *args, **kwargs)
    else:
        parent.SetSizer(sizer)
    return sizer


def create_label(
    parent: wx.Window, text: str = '', markup: str = ''
) -> wx.StaticText:
    label = wx.StaticText(parent, label=text)
    if markup:
        label.SetLabelMarkup(markup)
    return label


def create_button(
    parent: wx.Panel, label: str, callback: Callable
) -> wx.Button:
    button = wx.Button(parent, wx.ID_ANY, label)
    button.Bind(
        wx.EVT_BUTTON,
        partial(on_button_clicked, callback=callback),
        id=button.GetId(),
    )
    return button


def on_button_clicked(event: wx.MouseEvent, callback: Callable):
    callback()


class RadioConfig(NamedTuple):
    value: str
    label: str
    tooltip: Optional[str] = None


def create_radio_group(
    parent: wx.Panel,
    radio_configs: Iterable[RadioConfig],
    active_value: str,
    callback: Callable,
) -> Dict[str, wx.RadioButton]:
    radio_buttons = {}
    for i, radio_config in enumerate(radio_configs):
        if i == 0:
            kwargs = {'style': wx.RB_GROUP}
        else:
            kwargs = {}
        radio = wx.RadioButton(parent, label=radio_config.label, **kwargs)
        radio.Bind(
            wx.EVT_RADIOBUTTON,
            partial(
                on_radio_toggled, value=radio_config.value, callback=callback
            ),
        )
        if radio_config.value == active_value:
            radio.SetValue(True)
        radio_buttons[radio_config.value] = radio
    return radio_buttons


def on_radio_toggled(event: wx.MouseEvent, value: str, callback: Callable):
    callback(value)


def create_text_control(
    parent: wx.Panel, value: str, callback: Callable
) -> wx.TextCtrl:
    text_control = wx.TextCtrl(parent, value=value)
    text_control.Bind(
        wx.EVT_TEXT,
        partial(on_text_control_changed, callback=callback),
        text_control,
    )
    return text_control


def on_text_control_changed(event: wx.KeyEvent, callback: Callable):
    callback(event.GetString())


def create_spin_control(
    parent: wx.Window,
    value: int,
    callback: Callable,
    min_val: int = 0,
    max_val: int = 9999,
) -> wx.SpinCtrl:
    spin_control = wx.SpinCtrl(
        parent, value=str(value), min=min_val, max=max_val
    )
    spin_control.Bind(
        wx.EVT_TEXT,
        partial(
            on_spin_control_changed,
            spin_control=spin_control,
            callback=callback,
        ),
        spin_control,
    )
    return spin_control


def on_spin_control_changed(
    event: wx.KeyEvent, spin_control: wx.SpinCtrl, callback: Callable
):
    callback(spin_control.GetValue())


class DirBrowserButtonWithoutLabel(wx.lib.filebrowsebutton.DirBrowseButton):
    def createLabel(self):
        return wx.Window(self)


def create_dir_browse_button(
    parent: wx.Window, value: Optional[str], callback: Callable[[str], None]
):
    button = DirBrowserButtonWithoutLabel(
        parent, changeCallback=partial(on_dir_change, callback=callback)
    )
    button.SetValue(value)
    return button


def on_dir_change(event: wx.Event, callback: Callable):
    callback(event.GetString())


def image_to_bitmap(image: Image.Image) -> wx.Bitmap:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        wx_image = wx.Image(f)
        bitmap = wx_image.ConvertToBitmap()
    return bitmap


def image_to_icon(image: Image.Image) -> wx.Icon:
    return wx.Icon(image_to_bitmap(image))


class Form:
    panel: wx.Panel

    def __init__(self, parent: wx.Window):
        self.panel = wx.Panel(parent)

    def toggle(self, enabled: bool):
        if enabled:
            self.panel.Enable()
        else:
            self.panel.Disable()


class RootPathForm(Form):
    _root_path: Optional[str]
    _parent: wx.Panel

    def __init__(
        self,
        root_path: Optional[str],
        on_change: Callable[[str], None],
        parent: wx.Panel,
    ):
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent)
        self._create_widgets()

    def _create_widgets(self):
        vbox = create_sizer(self.panel)
        button = create_dir_browse_button(
            self.panel,
            value=self._root_path or '',
            callback=self._on_dir_changed,
        )
        vbox.Add(button, flag=wx.EXPAND)

    def _on_dir_changed(self, path: str):
        self._on_change(path)


class NamedDirsForm(Form):
    _named_dirs: NamedDirs
    _vbox: wx.BoxSizer
    _custom_names_enabled: bool

    def __init__(
        self,
        named_dirs: NamedDirs,
        on_change: Callable[[NamedDirs], None],
        parent: wx.Panel,
        on_redraw: Optional[Callable[[], None]] = None,
        custom_names_enabled: bool = True,
    ):
        self._named_dirs = named_dirs
        self._on_change = on_change
        self._on_redraw = on_redraw
        self._parent = parent
        self._custom_names_enabled = custom_names_enabled
        super().__init__(self._parent)
        self._create_widgets()

    def _create_widgets(self):
        self._vbox = create_sizer(self.panel)
        for i, named_dir in enumerate(self._named_dirs):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            if self._custom_names_enabled:
                name_control = create_text_control(
                    self.panel,
                    value=named_dir.name or '',
                    callback=after(
                        partial(self._named_dirs.set_name, i), self._changed
                    ),
                )
                hbox.Add(
                    name_control,
                    proportion=2,
                    flag=wx.EXPAND | wx.RIGHT,
                    border=10,
                )
            path_button = create_dir_browse_button(
                self.panel,
                value=named_dir.path or '',
                callback=after(
                    partial(self._named_dirs.set_path, i), self._changed
                ),
            )
            hbox.Add(
                path_button, proportion=3, flag=wx.EXPAND | wx.RIGHT, border=10
            )
            remove_button = create_button(
                self.panel,
                texts.BUTTON_REMOVE,
                callback=after(
                    partial(self._named_dirs.remove, i),
                    self._recreate,
                    self._changed,
                ),
            )
            hbox.Add(remove_button, proportion=1, flag=wx.EXPAND)
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            self._vbox.Add(hbox, flag=flag, border=5)
        if not self._named_dirs.max_reached:
            add_button = create_button(
                self.panel,
                texts.BUTTON_ADD,
                callback=after(
                    self._named_dirs.new, self._recreate, self._changed
                ),
            )
            self._vbox.Add(add_button, flag=wx.TOP, border=10)
        else:
            label = create_label(
                self.panel,
                texts.SETTINGS_MAX_DIRS_REACHED.format(
                    max_len=self._named_dirs.max_len
                ),
            )
            self._vbox.Add(label, flag=wx.TOP, border=10)

    def _changed(self):
        self._on_change(self._named_dirs)

    def _recreate(self):
        def wrapper():
            self.panel.DestroyChildren()
            self._create_widgets()
            self._vbox.Layout()
            self.panel.Layout()
            if self._on_redraw:
                self._on_redraw()

        wx.CallAfter(wrapper)
