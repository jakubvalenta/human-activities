import argparse
import logging
import sys

from lidske_aktivity import __title__
from lidske_aktivity.app import Application
from lidske_aktivity.model import clean_cache

logger = logging.getLogger(__name__)


def is_appindicator_available() -> bool:
    try:
        import gi

        gi.require_version('AppIndicator3', '0.1')
        logger.info('AppIndicator is available')
        return True
    except (ModuleNotFoundError, ValueError):
        logger.info('AppIndicator is not available')
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
        '-s',
        '--scan',
        action='store_true',
        help='Scan all directories, write the results to cache, and exit',
    )
    parser.add_argument(
        '-i',
        '--interval',
        type=int,
        default=21600,
        help=(
            'Number of seconds between periodic directory scans '
            '(default 21600 = 6h). If set to 0, periodic scanning will be '
            'disabled.'
        ),
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
    if args.scan:
        interval = 0
    else:
        interval = args.interval
    app = Application(interval)
    if args.scan:
        app.scan_start()
        return
    if args.wxwidgets:
        import lidske_aktivity.wx as ui
    elif args.qt:
        import lidske_aktivity.qt as ui
    elif is_appindicator_available():
        import lidske_aktivity.gtk as ui
    else:
        import lidske_aktivity.wx as ui
    app.run_ui(ui)
