import io
import logging
from functools import partial
from pathlib import Path
from typing import (
    Callable, Dict, Iterable, Iterator, List, NamedTuple, Optional,
)

import wx
from PIL import Image

from lidske_aktivity.config import TNamedDirs

logger = logging.getLogger(__name__)


def new_id_ref_compat():
    """A wrapper around wx.NewIdRef() compatible with wxPython < 4.0.3"""
    try:
        return wx.NewIdRef()
    except AttributeError:
        return wx.NewId()


def create_sizer(parent: wx.Window,
                 orientation: int = wx.VERTICAL,
                 *args,
                 **kwargs) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    if isinstance(parent, wx.Sizer):
        parent.Add(sizer, *args, **kwargs)
    else:
        parent.SetSizer(sizer)
    return sizer


def create_label(parent: wx.Window, text: str) -> wx.StaticText:
    return wx.StaticText(parent, label=text)


def create_button(parent: wx.Window,
                  panel: wx.Panel,
                  label: str,
                  callback: Callable) -> wx.Button:
    button = wx.Button(panel, wx.ID_ANY, label)
    parent.Bind(
        wx.EVT_BUTTON,
        partial(on_button_clicked, callback=callback),
        id=button.GetId()
    )
    return button


def on_button_clicked(event: wx.MouseEvent, callback: Callable):
    callback()


class RadioConfig(NamedTuple):
    value: str
    label: str
    tooltip: Optional[str] = None


def create_radio_group(parent: wx.Panel,
                       radio_configs: Iterable[RadioConfig],
                       active_value: str,
                       callback: Callable) -> Dict[str, wx.RadioButton]:
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
                on_radio_toggled,
                value=radio_config.value,
                callback=callback
            )
        )
        if radio_config.value == active_value:
            radio.SetValue(True)
        radio_buttons[radio_config.value] = radio
    return radio_buttons


def on_radio_toggled(event: wx.MouseEvent,
                     value: str,
                     callback: Callable):
    callback(value)


def create_text_control(parent: wx.Window,
                        value: str,
                        callback: Callable) -> wx.TextCtrl:
    text_control = wx.TextCtrl(parent, value=value)
    parent.Bind(
        wx.EVT_TEXT,
        partial(on_text_control_changed, callback=callback),
        text_control
    )
    return text_control


def on_text_control_changed(event: wx.KeyEvent, callback: Callable):
    callback(event.GetString())


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


def create_icon_from_image(image: Image) -> wx.Icon:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        wx_image = wx.Image(f)
        icon = wx.Icon(wx_image.ConvertToBitmap())
    return icon


def call_tick(func: Callable):
    wx.CallAfter(func)


class RootPathForm(wx.Panel):
    _root_path: Path
    _control: wx.TextCtrl
    _parent: wx.Panel

    def __init__(self,
                 root_path: Path,
                 on_change: Callable[[Path], None],
                 parent: wx.Panel):
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent)
        self._control = self._init_control()

    def _init_control(self) -> wx.TextCtrl:
        hbox = create_sizer(self, wx.HORIZONTAL)
        control = create_text_control(
            self,
            value=str(self._root_path) if self._root_path else '',
            callback=self._on_text
        )
        hbox.Add(
            control,
            proportion=5,
            flag=wx.EXPAND | wx.RIGHT,
            border=10
        )
        button = create_button(
            self,
            self,
            'Choose',
            self._on_button
        )
        hbox.Add(button, proportion=1, flag=wx.EXPAND)
        return control

    def _on_text(self, path_str: str):
        self._on_change(Path(path_str))

    def _on_button(self):
        def callback(path_str: str):
            self._on_change(Path(path_str))
            self._control.SetValue(path_str)

        choose_dir(self, callback)


class CustomDirsForm(wx.Panel):
    _custom_dirs: List[Path]
    _list_box: wx.ListBox
    _parent: wx.Panel

    def __init__(self,
                 custom_dirs: List[Path],
                 on_change: Callable[[List[Path]], None],
                 parent: wx.Panel):
        self._custom_dirs = custom_dirs
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent)
        self._list_box = self._init_list_box()

    def _init_list_box(self):
        hbox = create_sizer(self, wx.HORIZONTAL)

        list_box = wx.ListBox(self)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self._on_list_box_double_click)
        for custom_dir in self._custom_dirs:
            list_box.Append(str(custom_dir))
        hbox.Add(
            list_box,
            proportion=5,
            flag=wx.EXPAND | wx.RIGHT,
            border=10
        )

        vbox = wx.BoxSizer(wx.VERTICAL)
        for i, (label, callback) in enumerate([
                ('New', self._on_button_new),
                ('Change', self._on_button_change),
                ('Delete', self._on_button_delete),
                ('Clear', self._on_button_clear),
        ]):
            button = create_button(
                self,
                self,
                label,
                callback
            )
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            vbox.Add(button, flag=flag, border=5)
        hbox.Add(vbox, proportion=1, flag=wx.EXPAND)

        return list_box

    def _on_list_box_double_click(self, event: wx.MouseEvent):
        self._on_button_change()

    def _on_button_change(self):
        def callback(path_str: str):
            sel = self._list_box.GetSelection()
            self._list_box.Delete(sel)
            item_id = self._list_box.Insert(path_str, sel)
            self._custom_dirs[sel] = Path(path_str)
            self._on_change(self._custom_dirs)
            self._list_box.SetSelection(item_id)

        choose_dir(self, callback)

    def _on_button_new(self):
        def callback(path_str: str):
            self._custom_dirs.append(Path(path_str))
            self._on_change(self._custom_dirs)
            self._list_box.Append(path_str)

        choose_dir(self, callback)

    def _on_button_delete(self):
        sel = self._list_box.GetSelection()
        if sel != -1:
            del self._custom_dirs[sel]
            self._on_change(self._custom_dirs)
            self._list_box.Delete(sel)

    def _on_button_clear(self):
        self._custom_dirs[:] = []
        self._on_change(self._custom_dirs)
        self._list_box.Clear()


class NamedDir(NamedTuple):
    path: Path
    name: str


class NamedDirsForm(wx.Panel):
    _named_dirs_list: List[NamedDir]
    _path_controls: List[wx.TextCtrl]

    def __init__(self,
                 named_dirs: TNamedDirs,
                 on_change: Callable[[TNamedDirs], None],
                 parent: wx.Panel):
        self._named_dirs_list = [
            NamedDir(path, name)
            for path, name in named_dirs.items()
        ]
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent)
        self._path_controls = list(self._init_controls())

    def _init_controls(self) -> Iterator[wx.TextCtrl]:
        vbox = create_sizer(self)
        for i, named_dir in enumerate(self._named_dirs_list):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            text_control_name = create_text_control(
                self,
                value=named_dir.name or '',
                callback=partial(self._on_name_text, i)
            )
            hbox.Add(
                text_control_name,
                proportion=2,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            control_path = create_text_control(
                self,
                value=str(named_dir.path) or '',
                callback=partial(self._on_path_text, i)
            )
            hbox.Add(
                control_path,
                proportion=3,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            button = create_button(
                self,
                self,
                'Choose',
                partial(self._on_path_button, i)
            )
            hbox.Add(button, proportion=1, flag=wx.EXPAND)
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            vbox.Add(hbox, flag=flag, border=5)
            yield control_path

    def _on_name_text(self, i: int, name: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(name=name)
        self._on_change(self._named_dirs)

    def _on_path_text(self, i: int, path_str: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(path=Path(path_str))
        self._on_change(self._named_dirs)

    def _on_path_button(self, i: int):
        def callback(path_str: str):
            named_dir = self._named_dirs_list[i]
            self._named_dirs_list[i] = named_dir._replace(path=Path(path_str))
            self._on_change(self._named_dirs)
            self._path_controls[i].SetValue(path_str)

        choose_dir(self, callback)

    @property
    def _named_dirs(self) -> TNamedDirs:
        return {
            named_dir.path: named_dir.name
            for named_dir in self._named_dirs_list
        }
