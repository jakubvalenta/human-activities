import csv
import logging
import os
import stat
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Thread
from typing import Callable, Dict, Iterator, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class Directory:
    path: Path
    size: int


@dataclass
class FileSystem:
    directories: List[Directory]
    size: int


def _has_hidden_attribute(path: Path) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(getattr(path.stat(), 'st_file_attributes', 0) &
                stat.FILE_ATTRIBUTE_HIDDEN)


def _is_hidden(path: Path) -> bool:
    return path.name.startswith('.') or _has_hidden_attribute(path)


def _list_dirs(path: Path) -> Iterator[Path]:
    return sorted(
        p for p in path.iterdir()
        if p.is_dir() and not _is_hidden(p)
    )


def calc_path_size(path: Path) -> int:
    """See https://stackoverflow.com/a/37367965"""
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
                total += calc_path_size(entry.path)
    return total


def calc_directory_size(directory: Directory,
                        cache_path: Path,
                        callback: Callable[[Directory], None]) -> None:
    path = directory.path
    logger.warn('Scanning %s', path)
    size = calc_path_size(path)
    logger.warn('Scanned %s, size = %d', path, size)
    new_directory = Directory(path, size)
    write_directory_to_cache(cache_path, new_directory)
    callback(new_directory)


def create_file_system(root_path: Path) -> FileSystem:
    directories = [
        Directory(path=path, size=0)
        for path in _list_dirs(root_path)
    ]
    return FileSystem(directories=directories, size=0)


def try_int(val: any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def read_cache(cache_path: Path) -> Iterator[Dict[str, Union[str, int]]]:
    if not cache_path.is_file():
        return iter([])
    with cache_path.open() as f:
        for row in csv.reader(f):
            if len(row) != 2:
                continue
            path, size_raw = row
            size = try_int(size_raw)
            if size is None:
                continue
            yield {
                'path': path,
                'size': size,
            }


def read_cache_dict(cache_path: Path) -> Dict[str, int]:
    return {
        Path(cache_item['path']): cache_item['size']
        for cache_item in read_cache(cache_path)
    }


def write_directory_to_cache(cache_path: Path, directory: Directory) -> None:
    if not directory.path or directory.size is None:
        return
    with cache_path.open('a') as f:
        writer = csv.writer(f)
        writer.writerow([str(directory.path), directory.size])


def load_cached_directories(directories: List[Directory],
                            path: Path) -> Iterator[Directory]:
    if not directories:
        return iter([])
    cache_dict = read_cache_dict(path)
    for directory in directories:
        if directory.path in cache_dict:
            size = cache_dict[directory.path]
            yield Directory(path=directory.path, size=size)
        else:
            yield directory


def update(file_system: FileSystem,
           func: Callable[[List[Directory]], FileSystem]) -> FileSystem:
    directories = list(func(file_system.directories))
    size = sum(directory.size for directory in directories)
    return FileSystem(directories=directories, size=size)


def load_cache(file_system: FileSystem, path: Path) -> FileSystem:
    return update(file_system, partial(load_cached_directories, path=path))


def init_file_system(cache_path: Path,
                     root_path: Optional[Path] = Path.home()) -> FileSystem:
    if not root_path.is_dir():
        logger.error('Path %s doesn\'t exist', root_path)
        return FileSystem(directories=[], size=0)
    file_system = create_file_system(root_path)
    return load_cache(file_system, cache_path)


def scan_file_system(file_system: FileSystem,
                     cache_path: Path,
                     callback: Callable[[Directory], None]) -> None:
    for i, directory in enumerate(file_system.directories):
        func = partial(calc_directory_size, directory, cache_path, callback)
        thread = Thread(target=func)
        thread.start()
