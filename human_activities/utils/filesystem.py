import logging
import os
import os.path
import pkgutil
import stat
import subprocess
from threading import Event
from typing import Dict, Iterable, Iterator, List, NamedTuple, Optional, Union

from pathspec import PathSpec

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


def parse_fdignore(b: bytes) -> Iterator[str]:
    for line in b.decode().splitlines():
        s = line.rstrip()
        if s and not s.startswith('#'):
            yield s


def find_files_fd(
    path: str, fdignore_path: Optional[str] = None
) -> Iterator[FdDirEntry]:
    cmd = ['fd', '-t', 'f']
    if fdignore_path is not None:
        cmd += ['--ignore-file', fdignore_path]
    else:
        fdignore_bytes = pkgutil.get_data(
            'human_activities.etc', 'human-activities.fdignore'
        )
        if fdignore_bytes:
            ignore_rules = parse_fdignore(fdignore_bytes)
            for ignore_rule in ignore_rules:
                cmd += ['-E', ignore_rule]
    cmd += ['.', path]
    try:
        completed_process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            universal_newlines=True,
            # Don't use arg 'text' for Python 3.6 compat.
        )
    except subprocess.CalledProcessError as err:
        logger.info(
            'fd returned error %d, stderr: "%s"',
            err.returncode,
            err.stderr,
        )
        return
    for path in completed_process.stdout.splitlines():
        yield FdDirEntry(path, is_file=True)


def find_files_python(
    path: str, pathspec: Optional[PathSpec] = None
) -> Iterator[os.DirEntry]:
    try:
        entries = os.scandir(path)
    except FileNotFoundError:
        logger.info('Directory not found "%s"', path)
        return
    except PermissionError:
        logger.info('No permissions to read directory "%s"', path)
        return
    if pathspec is None:
        fdignore_bytes = pkgutil.get_data(
            'human_activities.etc', 'human-activities.fdignore'
        )
        if fdignore_bytes:
            pathspec = PathSpec.from_lines(
                'gitwildmatch', fdignore_bytes.decode().splitlines()
            )
    for entry in entries:
        if entry.is_symlink():
            continue
        if is_hidden(entry) or pathspec.match_file(entry.path):
            continue
        if entry.is_file():
            yield entry
        elif entry.is_dir():
            yield from find_files_python(entry.path, pathspec=pathspec)


def find_files(path: str, fdignore_path: Optional[str]) -> Iterator[TDirEntry]:
    try:
        yield from find_files_fd(path, fdignore_path)
    except FileNotFoundError:
        logger.info('fd is not available')
        yield from find_files_python(path)


def calc_entries_size(
    entries: Iterable[TDirEntry], threshold_seconds: float, event_stop: Event
) -> DirSize:
    size_bytes_all = 0
    size_bytes_new = 0
    num_files_all = 0
    num_files_new = 0
    for entry in entries:
        if event_stop.is_set():
            logger.warning('Stopping calculation')
            break
        stat_result = entry.stat()
        size_bytes_all += stat_result.st_size
        num_files_all += 1
        if stat_result.st_mtime > threshold_seconds:
            size_bytes_new += stat_result.st_size
            num_files_new += 1
    return DirSize(
        size_bytes_all=size_bytes_all,
        size_bytes_new=size_bytes_new,
        num_files_all=num_files_all,
        num_files_new=num_files_new,
    )
