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
        '-w',
        '--wxwidgets',
        action='store_true',
        help=(
            'Force the use of the WxWidget backend; by default, GTK is '
            'always used when AppIndicator is available'
        ),
    )
    parser.add_argument(
        '-q',
        '--qt',
        action='store_true',
        help=(
            'Force the use of the Qt5 backend; by default, GTK is '
            'always used when AppIndicator is available'
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
    if args.wxwidgets:
        logger.info('Using UI toolkit WxWidgets (reason: cli option)')
        import human_activities.wx as ui
    elif args.qt:
        logger.info('Using UI toolkit Qt5 (reason: cli option)')
        import human_activities.qt as ui
    elif is_appindicator_available():
        logger.info('Using UI toolkit Gtk+3 (reason: AppIndicator available)')
        import human_activities.gtk as ui
    elif is_pyqt5_available():
        logger.info('Using UI toolkit Qt5 (reason: PyQt5 available)')
        import human_activities.qt as ui
    else:
        logger.info('Using UI toolkit WxWidgets (reason: PyQt5 not available)')
        import human_activities.wx as ui
    return_code = app.run_ui(ui)
    sys.exit(return_code)
