import logging
import os
import stat
from pathlib import Path
from threading import Event
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def has_hidden_attribute(path: Path) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(getattr(path.stat(), 'st_file_attributes', 0) &
                stat.FILE_ATTRIBUTE_HIDDEN)  # type: ignore


def is_hidden(path: Path) -> bool:
    return path.name.startswith('.') or has_hidden_attribute(path)


def list_dirs(path: Path) -> List[Path]:
    return sorted(
        p for p in path.iterdir()
        if p.is_dir() and not is_hidden(p)
    )


def calc_dir_size(path: str,
                  threshold: float,
                  event_stop: Event) -> Tuple[Optional[int], Optional[int]]:
    try:
        entries = os.scandir(path)
    except PermissionError:
        logger.info('Permission error %s', path)
        return 0, 0
    total_size = 0
    total_size_new = 0
    for entry in entries:
        if event_stop.is_set():
            logger.warn('Stopping calculation')
            return None, None
        if not entry.is_symlink():
            if entry.is_file():
                stat_result = entry.stat()
                total_size += stat_result.st_size
                if stat_result.st_mtime > threshold:
                    total_size_new += stat_result.st_size
            elif entry.is_dir():
                sub_size, sub_size_new = calc_dir_size(
                    entry.path,
                    threshold,
                    event_stop
                )
                if sub_size is not None:
                    total_size += sub_size
                if sub_size_new is not None:
                    total_size_new += sub_size_new
    return total_size, total_size_new
