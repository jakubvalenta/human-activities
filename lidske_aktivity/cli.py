import argparse
import logging
import sys

from lidske_aktivity.app import Application
from lidske_aktivity.config import clean_cache

logger = logging.getLogger(__name__)


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
        if args.gtk:
            import lidske_aktivity.gtk as ui
        else:
            import lidske_aktivity.wx as ui
        Application(ui)
