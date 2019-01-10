from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple

import gi

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.gtk.lib import (
    box_add, choose_dir, create_box, create_button, create_entry, create_label,
)

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk, Gtk  # noqa:E402  # isort:skip


def add_text_heading(box: Gtk.Box, text: str):
    label = create_label(text)
    box_add(box, label, expand=False, padding=5)


def add_text_paragraph(box: Gtk.Box, text: str):
    label = create_label(text)
    box_add(box, label, expand=False)


def add_text_list(box: Gtk.Box, items: List[str]):
    for item in items:
        label = create_label(f'\N{BULLET} {item}')
        box_add(box, label, expand=False)


def create_content_intro() -> Gtk.Box:
    box = create_box(spacing=5, homogeneous=False)
    add_text_heading(box, 'Lidské aktivity setup')
    add_text_paragraph(box, 'Please adjust your OS settings like this:')
    add_text_list(
        box,
        [
            'first do this',
            'than that',
            'and finally something different',
        ]
    )
    return box


class Page(NamedTuple):
    title: str
    content: Gtk.Widget
    page_type: Gtk.AssistantPageType


def create_assistant(pages: List[Page], callback: Callable) -> Gtk.Assistant:
    assistant = Gtk.Assistant()
    assistant.set_default_size(500, 400)
    assistant.set_gravity(Gdk.Gravity.CENTER)
    assistant.set_position(Gtk.WindowPosition.CENTER)
    assistant.connect(
        'apply',
        partial(on_assistant_apply, callback=callback)
    )
    assistant.connect('cancel', on_assistant_cancel)
    for page in pages:
        assistant.append_page(page.content)
        assistant.set_page_title(page.content, page.title)
        assistant.set_page_type(page.content, page.page_type)
        assistant.set_page_complete(page.content, True)
    assistant.show_all()
    return assistant


def on_assistant_apply(assistant: Gtk.Assistant, callback: Callable):
    callback()
    assistant.hide()


def on_assistant_cancel(assistant: Gtk.Assistant):
    assistant.hide()


class Setup:
    config: Config
    assistant: Gtk.Assistant
    entries: Dict[str, Gtk.Entry]
    named_dirs_by_name: Dict[str, Path]

    def __init__(self, config: Config, on_finish: Callable, *args, **kwargs):
        self._init_config(config)
        self._on_finish = on_finish
        super().__init__()
        self.assistant = create_assistant(
            [
                Page(
                    title='Intro',
                    content=create_content_intro(),
                    page_type=Gtk.AssistantPageType.INTRO
                ),
                Page(
                    title='Setup',
                    content=self._create_content_setup(),
                    page_type=Gtk.AssistantPageType.CONFIRM
                )
            ],
            self._on_assistant_apply
        )

    def _on_assistant_apply(self):
        self._on_finish(self.config)

    def _init_config(self, config: Config):
        self.config = config
        self.config.mode = MODE_NAMED
        if not self.config.named_dirs:
            self.config.named_dirs = DEFAULT_NAMED_DIRS
        self.named_dirs_by_name = dict(zip(
            self.config.named_dirs.values(),
            self.config.named_dirs.keys(),
        ))

    def _create_content_setup(self) -> Gtk.Grid:
        box = create_box()
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        self.entries = {}
        for i, (path, name) in enumerate(self.config.named_dirs.items()):
            label = create_label(name)
            grid.attach(label, left=0, top=i, width=1, height=1)
            entry = create_entry(
                value=str(path) or '',
                callback=partial(self._on_named_dir_text, name)
            )
            entry.set_hexpand(True)
            grid.attach(entry, left=1, top=i, width=1, height=1)
            button = create_button(
                'Choose',
                partial(self._on_named_dir_button, name)
            )
            grid.attach(button, left=2, top=i, width=1, height=1)
            self.entries[name] = entry
        box_add(box, grid)
        return box

    def _update_named_dirs(self, name: str, path: Path):
        self.named_dirs_by_name[name] = path
        self.config.named_dirs = dict(zip(
            self.named_dirs_by_name.values(),
            self.named_dirs_by_name.keys()
        ))

    def _on_named_dir_text(self, name: str, entry: Gtk.Entry, value: str):
        self._update_named_dirs(name, Path(value))

    def _on_named_dir_button(self, name: str, button: Gtk.Button):
        def callback(path_str: str):
            self._update_named_dirs(name, Path(path_str))
            self.entries[name].set_text(path_str)

        choose_dir(self.assistant, callback)
