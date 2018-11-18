import logging
import sys

import click

from lidske_aktivity import app, config

logger = logging.getLogger(__name__)


@click.command()
@click.option('-v', '--verbose', is_flag=True)
@click.option('-c', '--clean', is_flag=True)
def main(verbose: bool, clean: bool):
    if verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    if clean:
        config.clean_cache()
    else:
        app.main()
