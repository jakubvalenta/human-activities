import argparse
import logging
import sys

from lidske_aktivity import __title__
from lidske_aktivity.app import Application
from lidske_aktivity.config import clean_cache

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
        '-v',
        '--verbose',
        action='store_true',
        help='Enable debugging output'
    )
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help='Clean cache and exit'
    )
    parser.add_argument(
        '-w',
        '--wx',
        action='store_true',
        help=('Force the use of the WxWidget backend; by default, GTK is '
              'always used when AppIndicator is available')
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='[%(threadName)s] %(message)s')
    if args.clean:
        clean_cache()
    else:
        if not args.wx and is_appindicator_available():
            import lidske_aktivity.gtk as ui
        else:
            import lidske_aktivity.wx as ui
        Application(ui)
