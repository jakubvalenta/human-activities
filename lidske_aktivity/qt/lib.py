import io
import logging
from typing import Callable

from PIL import Image
from PyQt5 import QtGui, QtWidgets

logger = logging.getLogger(__name__)


def image_to_pixmap(image: Image.Image) -> QtGui.QPixmap:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(f.read())
    return pixmap


def create_icon_pixmap(
    app: QtWidgets.QApplication,
    standard_pixmap: QtWidgets.QStyle.StandardPixmap,
) -> QtGui.QPixmap:
    style = app.style()
    pixmap = style.standardPixmap(standard_pixmap)
    return pixmap


def get_icon_size(
    app: QtWidgets.QApplication, pixel_metric: QtWidgets.QStyle.PixelMetric
) -> int:
    style = app.style()
    size = style.pixelMetric(pixel_metric)
    return size


def create_icon(pixmap: QtGui.QPixmap) -> QtGui.QIcon:
    return QtGui.QIcon(pixmap)


def call_tick(func: Callable):
    func()
