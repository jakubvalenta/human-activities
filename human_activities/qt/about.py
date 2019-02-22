from typing import List

from PIL import Image
from PyQt5.QtWidgets import QMessageBox, QWidget

from human_activities import __license__
from human_activities.qt.lib import create_icon, image_to_pixmap


def show_about(
    image: Image.Image,
    title: str,
    version: str,
    copyright: str,
    uri: str,
    authors: List[str],
):
    pixmap = image_to_pixmap(image)
    icon = create_icon(pixmap)
    parent = QWidget()
    parent.setWindowIcon(icon)
    authors_str = ', '.join(authors)
    text = f'''
{title}

{version}

{uri}

{copyright}

Authors: {authors_str}
License: {__license__}'''
    QMessageBox.about(parent, title, text)
