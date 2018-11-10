import csv
import logging
import os
import stat
from dataclasses import dataclass
from functools import partial
from pathlib import Path
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


def calc_directory_size(path: Path) -> int:
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
                total += calc_directory_size(entry.path)
    return total


def init_file_system(root_path: Path) -> FileSystem:
    directories = [
        Directory(path=path, size=0)
        for path in _list_dirs(root_path)
    ]
    return FileSystem(directories=directories, size=0)


def read_cache(path: Path) -> List[Dict[str, Union[str, int]]]:
    if not path.is_file():
        return []
    with path.open() as f:
        return [
            {
                'path': row['path'],
                'size': int(row['size']),
            }
            for row in csv.DictReader(f)
            if 'path' in row and 'size' in row
        ]


def read_cache_dict(path: Path) -> Dict[str, int]:
    return {
        Path(cache_item['path']): cache_item['size']
        for cache_item in read_cache(path)
    }


def write_directory_to_cache(path: Path, directory: Directory):
    cache = read_cache(path)
    cache.append({
        'path': str(directory.path),
        'size': directory.size,
    })
    with path.open('w') as f:
        writer = csv.DictWriter(f, ['path', 'size'])
        writer.writeheader()
        writer.writerows(cache)


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


def scan_directories(directories: List[Directory],
                     cache_path: Path) -> Iterator[Directory]:
    for i, directory in enumerate(directories):
        logger.warn('Scanning %s', directory.path)
        size = calc_directory_size(directory.path)
        logger.warn('Scanned %s, size = %d', directory.path, size)
        directory = Directory(path=directory.path, size=size)
        write_directory_to_cache(cache_path, directory)
        yield directory


def scan_file_system(file_system: FileSystem,
                     cache_path: Path) -> FileSystem:
    return update(
        file_system,
        partial(scan_directories, cache_path=cache_path))


def watch(callback: Callable[[FileSystem], None],
          cache_path: Path,
          root_path: Optional[Path] = Path.home()):
    if not root_path.is_dir():
        logger.error('Path %s doesn\'t exist', root_path)
        return FileSystem(directories=[], size=0)
    file_system = init_file_system(root_path)
    callback(file_system)
    file_system = load_cache(file_system, cache_path)
    callback(file_system)
    file_system = scan_file_system(file_system, cache_path)
    callback(file_system)
