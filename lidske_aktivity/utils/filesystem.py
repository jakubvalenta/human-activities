import logging
import os
import os.path
import stat
from threading import Event
from typing import List, NamedTuple, Optional

logger = logging.getLogger(__name__)


def has_hidden_attribute(entry: os.DirEntry) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(
        getattr(entry.stat(), 'st_file_attributes', 0)
        & stat.FILE_ATTRIBUTE_HIDDEN  # type: ignore
    )


def is_hidden(entry: os.DirEntry) -> bool:
    return entry.name.startswith('.') or has_hidden_attribute(entry)


def list_dirs(path: str) -> List[str]:
    return sorted(
        entry.path
        for entry in os.scandir(path)
        if entry.is_dir() and not is_hidden(entry)
    )


suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def humansize(nbytes: int) -> str:
    """https://stackoverflow.com/a/14996816"""
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = f'{nbytes:.2f}'.rstrip('0').rstrip('.')
    return f'{f} {suffixes[i]}'


class DirSize(NamedTuple):
    size_bytes_all: Optional[int] = None
    size_bytes_new: Optional[int] = None
    num_files_all: Optional[int] = None
    num_files_new: Optional[int] = None


def calc_dir_size(
    path: str, threshold_seconds: float, event_stop: Event
) -> DirSize:
    try:
        entries = os.scandir(path)
    except FileNotFoundError:
        logger.info('Directory not found "%s"', path)
        return DirSize()
    except PermissionError:
        logger.info('No permissions to read directory "%s"', path)
        return DirSize()
    size_bytes_all = 0
    size_bytes_new = 0
    num_files_all = 0
    num_files_new = 0
    for entry in entries:
        if event_stop.is_set():
            logger.warning('Stopping calculation')
            return DirSize()
        if not entry.is_symlink():
            if entry.is_file():
                stat_result = entry.stat()
                size_bytes_all += stat_result.st_size
                num_files_all += 1
                if stat_result.st_mtime > threshold_seconds:
                    size_bytes_new += stat_result.st_size
                    num_files_new += 1
            elif entry.is_dir():
                sub_dir_size = calc_dir_size(
                    entry.path, threshold_seconds, event_stop
                )
                if sub_dir_size.size_bytes_all:
                    size_bytes_all += sub_dir_size.size_bytes_all
                if sub_dir_size.size_bytes_new:
                    size_bytes_new += sub_dir_size.size_bytes_new
                if sub_dir_size.num_files_all:
                    num_files_all += sub_dir_size.num_files_all
                if sub_dir_size.num_files_new:
                    num_files_new += sub_dir_size.num_files_new
    return DirSize(
        size_bytes_all=size_bytes_all,
        size_bytes_new=size_bytes_new,
        num_files_all=num_files_all,
        num_files_new=num_files_new,
    )
