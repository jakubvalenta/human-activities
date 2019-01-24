import logging
import os
import textwrap
import time
import traceback
from threading import Event
from typing import Callable, Iterable, List, NamedTuple, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

from lidske_aktivity.config import (
    CACHE_PATH, UNIT_NUM_FILES, UNIT_SIZE_BYTES, TNamedDirs,
)
from lidske_aktivity.icon import (
    COLOR_BLACK, COLOR_GRAY, Color, color_from_index,
)
from lidske_aktivity.utils import filesystem, func
from lidske_aktivity.utils.math import safe_div

logger = logging.getLogger(__name__)

Base = declarative_base()


class Stat(Base):  # type: ignore
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    size_bytes = Column(Integer)
    num_files = Column(Integer)
    threshold_days_ago = Column(Integer, nullable=False)
    directory_id = Column(Integer, ForeignKey('directories.id'))
    directory = relationship('Directory', back_populates='stats')

    def __repr__(self) -> str:
        return (f'Stat(size_bytes={self.size_bytes}, '
                f'num_files={self.num_files}, '
                f'threshold_days_ago={self.threshold_days_ago})')


class Directory(Base):  # type: ignore
    __tablename__ = 'directories'

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, unique=True)
    stats = relationship(
        'Stat',
        back_populates='directory',
        cascade='all, delete, delete-orphan'
    )

    def find_value(self, unit: str, threshold_days_ago: int) -> Optional[int]:
        for stat in self.stats:
            if stat.threshold_days_ago == threshold_days_ago:
                return getattr(stat, unit)
        return None

    def __repr__(self) -> str:
        return f'Directory(path={self.path}, stats={self.stats})'


def create_database_engine():
    engine = create_engine(f'sqlite:///{CACHE_PATH}')
    Base.metadata.create_all(engine)
    return engine


try:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    engine = create_database_engine()
except DatabaseError:
    os.remove(CACHE_PATH)
    engine = create_database_engine()
session_factory = sessionmaker(bind=engine)


class Directories(list):
    _session: Session

    def __init__(self):
        self._session = scoped_session(session_factory)

    def load(self, paths: Iterable[str]):
        """Load Directory objects for passed paths from the databse.

        Create new objects for those that were not found in the database.
        """
        paths = list(paths)
        query = (
            self._session.query(Directory)
            .filter(Directory.path.in_(paths))
            .order_by(Directory.path)
        )
        directories_dict = {
            directory.path: directory
            for directory in query
        }
        for path in paths:
            if path in directories_dict:
                directory = directories_dict[path]
                logger.info('DB: Loaded %s', directory)
            else:
                directory = Directory(path=path)
                logger.info('DB: Inserting %s', directory)
                self._session.add(directory)
            self.append(directory)

    def clear(self):
        for directory in self:
            logger.info('DB: Deleting %s', directory)
            self._session.delete(directory)
        super().clear()

    def save(self):
        self._session.commit()

    def __del__(self):
        self._session.close()


class DirectoryView(NamedTuple):
    label: str
    value: Optional[float] = None
    fraction: float = 0
    text: str = ''
    tooltip: str = ''
    pending: bool = True


class DirectoryViews(dict):
    _unit: str
    _threshold_days_ago: int

    def config(self,
               unit: str,
               threshold_days_ago: int,
               named_dirs: TNamedDirs):
        self._unit = unit
        self._threshold_days_ago = threshold_days_ago
        self.clear()
        for path, label in named_dirs.items():
            self[path] = DirectoryView(label)

    def load(self, *directories: Directory, **view_args):
        for directory in directories:
            if directory.path not in self:
                logger.error(
                    'Directory view for path %s doesn\'t exist',
                    directory.path
                )
                continue
            value = directory.find_value(self._unit, self._threshold_days_ago)
            self[directory.path] = self[directory.path]._replace(
                value=value,
                **view_args
            )
        self._recalculate()

    def _recalculate(self):
        total = sum(
            directory_view.value or 0
            for directory_view in self.values()
        )
        for path, directory_view in self.items():
            if directory_view.value is None:
                fraction = 0
            else:
                fraction = safe_div(directory_view.value, total)
            text = self._format_text(
                directory_view.label,
                directory_view.value,
                fraction,
                directory_view.pending
            )
            tooltip = self._format_tooltip(
                fraction,
                self._unit,
                self._threshold_days_ago
            )
            self[path] = directory_view._replace(
                fraction=fraction,
                text=text,
                tooltip=tooltip
            )
        logger.info('Recalculated fractions: %s', self.fractions)

    @staticmethod
    def _format_text(label: str,
                     value: Optional[float],
                     fraction: float,
                     pending: bool):
        s = f'{label}: '
        if value is not None:
            s += f'{fraction:.0%}'
        if pending:
            s += '...'
        elif value is None:
            s += 'n/a'
        return s

    @staticmethod
    def _format_tooltip(fraction: float,
                        unit: str,
                        threshold_days_ago: int) -> str:
        unit_text = {
            UNIT_SIZE_BYTES: 'of the size ',
            UNIT_NUM_FILES: '',
        }[unit]
        if threshold_days_ago == 0:
            set_text = 'all files in configured directories'
        else:
            set_text = (f'the files modified in the past '
                        f'{threshold_days_ago} days')
        s = f'{fraction:.2%} {unit_text}of {set_text}'
        return textwrap.fill(s)

    @property
    def paths(self) -> List[str]:
        return list(self.keys())

    @property
    def fractions(self) -> List[float]:
        return [dv.fraction for dv in self.values()]

    @property
    def texts(self) -> List[str]:
        return [dv.text for dv in self.values()]

    @property
    def tooltip(self) -> str:
        return '\n'.join(self.texts)

    def get_colors_with_one_highlighted(
            self,
            i: int,
            grayscale: bool = False) -> List[Color]:
        colors = [COLOR_GRAY for i in range(len(self))]
        if grayscale:  # TODO: Remove when finally decided for one option.
            colors[i] = COLOR_BLACK
        else:
            colors[i] = color_from_index(i)
        return colors


@func.measure_time
def scan_directory(path: str,
                   unit: str,
                   threshold_days_ago: int,
                   event_stop: Event,
                   callback: Callable[[Directory], None],
                   test: bool = False):
    logger.info('Scanning "%s"', path)
    try:
        session = scoped_session(session_factory)
        directory = session.query(Directory).filter(
            Directory.path == path
        ).one()
        threshold_seconds_ago = threshold_days_ago * 24 * 3600
        threshold_seconds = time.time() - threshold_seconds_ago
        dir_size = filesystem.calc_dir_size(
            directory.path,
            threshold_seconds=threshold_seconds,
            event_stop=event_stop
        )
        directory.stats.clear()
        directory.stats.append(
            Stat(
                size_bytes=dir_size.size_bytes_all,
                num_files=dir_size.num_files_all,
                threshold_days_ago=0
            )
        )
        if threshold_days_ago != 0:
            directory.stats.append(
                Stat(
                    size_bytes=dir_size.size_bytes_new,
                    num_files=dir_size.num_files_new,
                    threshold_days_ago=threshold_days_ago
                )
            )
        if test:
            func.random_wait(event_stop)
        logger.info('Scanned "%s": %s', directory.path, directory.stats)
        logger.info('DB: Updating %s', directory)
        session.commit()
        callback(directory)
    except Exception:
        logger.error('Exception while scanning "%s"', path)
        logger.info(traceback.format_exc())
    finally:
        session.close()
