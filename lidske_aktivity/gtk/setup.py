from functools import partial
from typing import Callable, List, NamedTuple

import gi

from lidske_aktivity import texts
from lidske_aktivity.config import Config, TNamedDirs
from lidske_aktivity.gtk.lib import (
    NamedDirsForm,
    box_add,
    create_box,
    create_label,
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
        label = create_label(texts.LIST_BULLET.format(item=item))
        box_add(box, label, expand=False)


def create_content_intro(parent: Gtk.Window) -> Gtk.Box:
    box = create_box(spacing=5, homogeneous=False)
    add_text_heading(box, texts.SETUP_TITLE)
    add_text_paragraph(box, texts.SETUP_HEADING)
    add_text_list(box, texts.SETUP_LIST.splitlines())
    return box


class Page(NamedTuple):
    title: str
    content_func: Gtk.Widget
    page_type: Gtk.AssistantPageType


def create_assistant(
    parent: Gtk.Window, pages: List[Page], callback: Callable
) -> Gtk.Assistant:
    assistant = Gtk.Assistant(
        modal=True,
        transient_for=parent,
        gravity=Gdk.Gravity.CENTER,
        resizable=False,
        skip_taskbar_hint=True,
        skip_pager_hint=True,
    )
    assistant.set_default_size(500, 400)
    assistant.set_position(Gtk.WindowPosition.CENTER)
    assistant.connect('apply', partial(on_assistant_apply, callback=callback))
    assistant.connect('cancel', on_assistant_cancel)
    for page in pages:
        content = page.content_func(parent=assistant)
        assistant.append_page(content)
        assistant.set_page_title(content, page.title)
        assistant.set_page_type(content, page.page_type)
        assistant.set_page_complete(content, True)
    assistant.show_all()
    return assistant


def on_assistant_apply(assistant: Gtk.Assistant, callback: Callable):
    callback()
    assistant.hide()


def on_assistant_cancel(assistant: Gtk.Assistant):
    assistant.hide()


class Setup:
    _config: Config
    assistant: Gtk.Assistant

    def __init__(
        self, config: Config, on_finish: Callable, parent: Gtk.Window
    ):
        self._config = config
        self._config.reset_named_dirs()
        self._on_finish = on_finish
        super().__init__()
        self.assistant = create_assistant(
            parent,
            [
                Page(
                    title=texts.SETUP_STEP_INTRO_TITLE,
                    content_func=create_content_intro,
                    page_type=Gtk.AssistantPageType.INTRO,
                ),
                Page(
                    title=texts.SETUP_STEP_SETUP_TITLE,
                    content_func=partial(
                        NamedDirsForm,
                        self._config.named_dirs,
                        self._on_named_dirs_change,
                    ),
                    page_type=Gtk.AssistantPageType.CONFIRM,
                ),
            ],
            self._on_assistant_apply,
        )

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _on_assistant_apply(self):
        self._on_finish(self._config)
