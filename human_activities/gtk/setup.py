from functools import partial
from typing import Callable, List, NamedTuple

import gi

from human_activities import texts
from human_activities.config import Config, NamedDirs
from human_activities.gtk.lib import (
    NamedDirsForm,
    box_add,
    create_box,
    create_label,
)

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk, Gtk  # noqa:E402  # isort:skip


class Page(NamedTuple):
    title: str
    content_func: Gtk.Widget
    page_type: Gtk.AssistantPageType


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
        assistant.connect('apply', self._on_assistant_apply)
        assistant.connect('cancel', self._on_assistant_cancel)
        page = create_box(spacing=10, homogeneous=False)
        heading = create_label(texts.SETUP_HEADING)
        box_add(page, heading, expand=False)
        TEXT = create_label(texts.SETUP_TEXT)
        box_add(page, TEXT, expand=False)
        named_dirs_form = NamedDirsForm(
            self._config.named_dirs,
            self._on_named_dirs_change,
            parent=assistant,
            custom_names_enabled=False,
        )
        box_add(page, named_dirs_form, expand=False)
        assistant.append_page(page)
        assistant.set_page_title(page, texts.SETUP_HEADING)
        assistant.set_page_type(page, Gtk.AssistantPageType.CONFIRM)
        assistant.set_page_complete(page, True)
        assistant.show_all()

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _on_assistant_apply(self, assistant: Gtk.Assistant):
        assistant.hide()
        self._on_finish(self._config)

    def _on_assistant_cancel(self, assistant: Gtk.Assistant):
        assistant.hide()
