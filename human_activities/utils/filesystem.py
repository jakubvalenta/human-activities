import logging
import os
import os.path
import stat
import subprocess
from threading import Event
from typing import Dict, Iterator, List, NamedTuple, Optional, Union

logger = logging.getLogger(__name__)


class DirSize(NamedTuple):
    size_bytes_all: Optional[int] = None
    size_bytes_new: Optional[int] = None
    num_files_all: Optional[int] = None
    num_files_new: Optional[int] = None


class FdDirEntry:
    def __init__(self, path, is_dir=False, is_file=False, is_symlink=False):
        self.path = path
        self._is_dir = is_dir
        self._is_file = is_file
        self._is_symlink = is_symlink
        self._cache: Dict[bool, os.stat_result] = {}

    @property
    def name(self):
        raise NotImplementedError

    @property
    def inode(self):
        raise NotImplementedError

    def is_file(self, follow_symlinks: bool = True) -> bool:
        return self._is_file

    def is_dir(self, follow_symlinks: bool = True) -> bool:
        return self._is_dir

    def is_symlink(self) -> bool:
        return self._is_symlink

    def stat(self, follow_symlinks: bool = True) -> os.stat_result:
        if follow_symlinks not in self._cache:
            self._cache[follow_symlinks] = os.stat(
                self.path, follow_symlinks=follow_symlinks
            )
        return self._cache[follow_symlinks]


TDirEntry = Union[FdDirEntry, os.DirEntry]


def has_hidden_attribute(entry: TDirEntry) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(
        getattr(entry.stat(), 'st_file_attributes', 0)
        & stat.FILE_ATTRIBUTE_HIDDEN  # type: ignore
    )


def is_hidden(entry: TDirEntry) -> bool:
    return entry.name.startswith('.') or has_hidden_attribute(entry)


def list_dirs(path: str) -> List[str]:
    return sorted(
        entry.path
        for entry in os.scandir(path)
        if entry.is_dir() and not is_hidden(entry)
    )


suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def humansize(nbytes: float) -> str:
    """https://stackoverflow.com/a/14996816"""
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = f'{nbytes:.2f}'.rstrip('0').rstrip('.')
    return f'{f} {suffixes[i]}'


def scan_dir(path: str) -> Iterator[TDirEntry]:
    try:
        completed_process = subprocess.run(
            ['fd', '-t', 'f', '.', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            universal_newlines=True,
            # Don't use arg 'text' for Python 3.6 compat.
        )
    except FileNotFoundError:
        logger.info('fd is not available')
        try:
            return os.scandir(path)
        except FileNotFoundError:
            logger.info('Directory not found "%s"', path)
            return
        except PermissionError:
            logger.info('No permissions to read directory "%s"', path)
            return
    except subprocess.CalledProcessError as err:
        logger.info(
            'fd returned error %d, stderr: "%s"',
            err.returncode,
            err.stderr,
        )
        return
    for path in completed_process.stdout.splitlines():
        yield FdDirEntry(path, is_file=True)


def calc_dir_size(
    path: str, threshold_seconds: float, event_stop: Event
) -> DirSize:
    entries = scan_dir(path)
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
            elif entry.is_dir() and not is_hidden(entry):
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
