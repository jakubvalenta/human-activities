import logging
import os
import stat
from pathlib import Path
from threading import Event
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


def calc_dir_size(path: Path, event_stop: Event) -> int:
    """See https://stackoverflow.com/a/37367965"""
    logger.info('Calculating size %s', path)
    total = 0
    try:
        entries = os.scandir(path)
    except PermissionError:
        entries = []
    for entry in entries:
        if event_stop.is_set():
            logger.warn('Stopping calculation')
            return None
        if not entry.is_symlink():
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += calc_dir_size(entry.path, event_stop)
    logger.info('Calculated size %s = %d', path, total)
    return total
