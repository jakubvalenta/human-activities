import logging
import sys

import click

from lidske_aktivity import app

logger = logging.getLogger(__name__)


@click.command()
@click.option('-v', '--verbose', is_flag=True)
def main(verbose: bool):
    if verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    app.main()
