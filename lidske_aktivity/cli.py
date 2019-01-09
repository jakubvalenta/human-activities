import argparse
import logging
import sys

from lidske_aktivity.app import Application
from lidske_aktivity.config import clean_cache

logger = logging.getLogger(__name__)


def is_wx_available() -> bool:
    try:
        import wx
        import wx.adv
        logger.info('WxWidgets library is available')
        wx.App()
        is_tray_available = wx.adv.TaskBarIcon.IsAvailable()
        logger.info('TaskBarIcon availability = %s', is_tray_available)
        return is_tray_available
    except ModuleNotFoundError:
        logger.info('WxWidgets library is not available')
        return False


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--clean', action='store_true')
    parser.add_argument('-g', '--gtk', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    if args.clean:
        clean_cache()
    else:
        if not args.gtk and is_wx_available():
            import lidske_aktivity.wx as ui
        else:
            import lidske_aktivity.gtk as ui
        Application(ui)
