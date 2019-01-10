from typing import Callable, List, NamedTuple

import gi

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.gtk.lib import box_add, create_label, create_vbox

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip


def add_text_heading(vbox: Gtk.VBox, text: str):
    label = create_label(text)
    box_add(vbox, label)


def add_text_paragraph(vbox: Gtk.VBox, text: str):
    label = create_label(text)
    box_add(vbox, label)


def add_text_list(vbox: Gtk.VBox, items: List[str]):
    for item in items:
        label = create_label(f'\N{BULLET} {item}')
        box_add(vbox, label)


def create_content_intro() -> Gtk.VBox:
    vbox = create_vbox()
    add_text_heading(vbox, 'Lidské aktivity setup')
    add_text_paragraph(vbox, 'Please adjust your OS settings like this:')
    add_text_list(
        vbox,
        [
            'first do this',
            'than that',
            'and finally something different',
        ]
    )
    return vbox


def create_content_setup() -> Gtk.Label:
    return create_label('Content of the setup page.')


class Page(NamedTuple):
    title: str
    content: Gtk.Widget
    page_type: Gtk.AssistantPageType


def init_assistant(pages: List[Page]):
    assistant = Gtk.Assistant()
    for page in pages:
        assistant.append_page(page.content)
        assistant.set_page_title(page.content, page.title)
        assistant.set_page_type(page.content, page.page_type)
        assistant.set_page_complete(page.content, True)
    assistant.show_all()


class Setup:
    config: Config

    def __init__(self, config: Config, on_finish: Callable, *args, **kwargs):
        self._init_config(config)
        super().__init__()
        init_assistant([
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
        ])

    def _init_config(self, config: Config):
        self.config = config
        self.config.mode = MODE_NAMED
        if not self.config.named_dirs:
            self.config.named_dirs = DEFAULT_NAMED_DIRS
        self.named_dirs_by_name = dict(zip(
            self.config.named_dirs.values(),
            self.config.named_dirs.keys(),
        ))
