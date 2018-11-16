import logging
import os
import random
import stat
import time
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


def has_hidden_attribute(path: Path) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(getattr(path.stat(), 'st_file_attributes', 0) &
                stat.FILE_ATTRIBUTE_HIDDEN)


def is_hidden(path: Path) -> bool:
    return path.name.startswith('.') or has_hidden_attribute(path)


def list_dirs(path: Path) -> Iterator[Path]:
    return sorted(
        p for p in path.iterdir()
        if p.is_dir() and not is_hidden(p)
    )


def random_wait():
    time.sleep(random.randint(1, 20))


def calc_dir_size(path: Path, test: bool = False) -> int:
    """See https://stackoverflow.com/a/37367965"""
    logger.warn('Calculating size %s', path)
    total = 0
    try:
        entries = os.scandir(path)
    except PermissionError:
        entries = []
    for entry in entries:
        if not entry.is_symlink():
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += calc_dir_size(entry.path)
    logger.warn('Calculated size %s = %d', path, total)
    if test:
        random_wait()
    return total
