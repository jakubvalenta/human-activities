from functools import partial
from typing import Callable, List, NamedTuple

import gi

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.gtk.lib import box_add, create_box, create_label

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip


def add_text_heading(box: Gtk.Box, text: str):
    label = create_label(text)
    box_add(box, label)


def add_text_paragraph(box: Gtk.Box, text: str):
    label = create_label(text)
    box_add(box, label)


def add_text_list(box: Gtk.Box, items: List[str]):
    for item in items:
        label = create_label(f'\N{BULLET} {item}')
        box_add(box, label)


def create_content_intro() -> Gtk.Box:
    box = create_box()
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


def create_content_setup() -> Gtk.Label:
    return create_label('Content of the setup page.')


class Page(NamedTuple):
    title: str
    content: Gtk.Widget
    page_type: Gtk.AssistantPageType


def init_assistant(pages: List[Page], on_finish: Callable):
    assistant = Gtk.Assistant()
    assistant.use_header_bar = True
    assistant.connect(
        'apply',
        partial(on_assistant_apply, on_finish=on_finish)
    )
    assistant.connect('cancel', on_assistant_cancel)
    for page in pages:
        assistant.append_page(page.content)
        assistant.set_page_title(page.content, page.title)
        assistant.set_page_type(page.content, page.page_type)
        assistant.set_page_complete(page.content, True)
    assistant.show_all()


def on_assistant_apply(assistant: Gtk.Assistant, on_finish: Callable):
    on_finish()
    assistant.hide()


def on_assistant_cancel(assistant: Gtk.Assistant):
    assistant.hide()


class Setup:
    config: Config
    on_finish: Callable

    def __init__(self, config: Config, on_finish: Callable, *args, **kwargs):
        self._init_config(config)
        self._on_finish = on_finish
        super().__init__()
        init_assistant(
            [
                Page(
                    title='Intro',
                    content=create_content_intro(),
                    page_type=Gtk.AssistantPageType.INTRO
                ),
                Page(
                    title='Setup',
                    content=create_content_setup(),
                    page_type=Gtk.AssistantPageType.CONFIRM
                )
            ],
            self.on_finish
        )

    def on_finish(self):
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
