from typing import List

import gi
from PIL import Image

from human_activities.gtk.lib import image_to_pixbuf

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip


def show_about(
    image: Image.Image,
    title: str,
    version: str,
    copyright: str,
    uri: str,
    authors: List[str],
):
    about_dialog = Gtk.AboutDialog(
        modal=True,
        logo=image_to_pixbuf(image),
        authors=authors,
        copyright=copyright,
        license_type=Gtk.License.GPL_3_0,
        version=version,
        website=uri,
    )
    about_dialog.present()
    about_dialog.connect('response', on_about_response)


def on_about_response(dialog: Gtk.Dialog, response_id: int) -> None:
    dialog.destroy()
