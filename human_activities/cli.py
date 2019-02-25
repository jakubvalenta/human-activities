import argparse
import logging
import sys

from human_activities import __title__
from human_activities.app import Application
from human_activities.model import clean_cache

logger = logging.getLogger(__name__)


def is_appindicator_available() -> bool:
    try:
        import gi

        gi.require_version('AppIndicator3', '0.1')
        return True
    except (ModuleNotFoundError, ValueError):
        return False


def is_pyqt5_available() -> bool:
    try:
        from PyQt5.QtWidgets import QApplication  # noqa: F401

        return True
    except ModuleNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__title__)
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable debugging output'
    )
    parser.add_argument(
        '-c', '--clean', action='store_true', help='Clean cache and exit'
    )
    parser.add_argument(
        '-b',
        '--backend',
        choices=('gtk', 'qt', 'wx', 'auto'),
        default='auto',
        help=(
            'UI toolkit to use. When set to "auto", the first installed '
            'toolkit in the list GTK+, Qt, WxWidgets will be chosen.'
        ),
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='[%(threadName)s] %(message)s',
        )
    if args.clean:
        clean_cache()
        return
    app = Application()
    if (
        args.backend == 'gtk'
        or args.backend == 'auto'
        and is_appindicator_available()
    ):
        logger.info('Using UI toolkit GTK+3')
        import human_activities.gtk as ui
    elif (
        args.backend == 'qt' or args.backend == 'auto' and is_pyqt5_available()
    ):
        logger.info('Using UI toolkit Qt5')
        import human_activities.qt as ui
    else:
        logger.info('Using UI toolkit WxWidgets')
        import human_activities.wx as ui
    return_code = app.run_ui(ui)
    sys.exit(return_code)
