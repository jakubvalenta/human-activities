import argparse
import logging
import sys

from lidske_aktivity import app, config

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--clean', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    if args.clean:
        config.clean_cache()
    else:
        app.main()
