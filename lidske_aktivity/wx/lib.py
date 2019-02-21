import io
import logging
from functools import partial
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Union

import wx
import wx.lib.filebrowsebutton
from PIL import Image

from lidske_aktivity import texts
from lidske_aktivity.config import TNamedDirs

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


def create_label(parent: wx.Window, text: str) -> wx.StaticText:
    return wx.StaticText(parent, label=text)


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

    def __init__(self, parent: wx.Window, use_parent_panel: bool = False):
        if use_parent_panel:
            self.panel = parent
        else:
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
        *args,
        **kwargs,
    ):
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent, *args, **kwargs)
        self._init_button()

    def _init_button(self):
        vbox = create_sizer(self.panel)
        button = create_dir_browse_button(
            self.panel,
            value=self._root_path or '',
            callback=self._on_dir_changed,
        )
        vbox.Add(button, flag=wx.EXPAND)

    def _on_dir_changed(self, path: str):
        self._on_change(path)


class NamedDir(NamedTuple):
    path: str = ''
    name: str = ''


class NamedDirsForm(Form):
    _named_dirs_list: List[NamedDir]
    _vbox: wx.BoxSizer

    def __init__(
        self,
        named_dirs: TNamedDirs,
        on_change: Callable[[TNamedDirs], None],
        parent: wx.Panel,
        on_redraw: Optional[Callable[[], None]] = None,
        *args,
        **kwargs,
    ):
        self._named_dirs_list = [
            NamedDir(path, name) for path, name in named_dirs.items()
        ]
        self._on_change = on_change
        self._on_redraw = on_redraw
        self._parent = parent
        super().__init__(self._parent, *args, **kwargs)
        self._init_controls()

    def _init_controls(self):
        self._vbox = create_sizer(self.panel)
        for i, named_dir in enumerate(self._named_dirs_list):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            name_control = create_text_control(
                self.panel,
                value=named_dir.name or '',
                callback=partial(self._on_name_changed, i),
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
                callback=partial(self._on_path_changed, i),
            )
            hbox.Add(
                path_button, proportion=3, flag=wx.EXPAND | wx.RIGHT, border=10
            )
            remove_button = create_button(
                self.panel,
                texts.BUTTON_REMOVE,
                callback=partial(self._on_remove_clicked, i),
            )
            hbox.Add(remove_button, proportion=1, flag=wx.EXPAND)
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            self._vbox.Add(hbox, flag=flag, border=5)
        add_button = create_button(
            self.panel, texts.BUTTON_ADD, callback=self._on_add_clicked
        )
        self._vbox.Add(add_button, flag=wx.TOP, border=10)

    def _recreate(self):
        self.panel.DestroyChildren()
        self._init_controls()
        self._vbox.Layout()
        self.panel.Layout()
        if self._on_redraw:
            self._on_redraw()

    def _on_name_changed(self, i: int, name: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(name=name)
        self._on_change(self._named_dirs)

    def _on_path_changed(self, i: int, path: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(path=path)
        self._on_change(self._named_dirs)

    def _on_remove_clicked(self, i: int):
        del self._named_dirs_list[i]
        self._on_change(self._named_dirs)
        wx.CallAfter(self._recreate)

    def _on_add_clicked(self):
        new_named_dir = NamedDir()
        self._named_dirs_list.append(new_named_dir)
        self._on_change(self._named_dirs)
        wx.CallAfter(self._recreate)

    @property
    def _named_dirs(self) -> TNamedDirs:
        return {
            named_dir.path: named_dir.name
            for named_dir in self._named_dirs_list
            if named_dir.path and named_dir.name
        }
