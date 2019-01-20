import logging
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Event, Thread
from typing import Iterable, List, NamedTuple

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

from lidske_aktivity.config import (
    CACHE_PATH, VALUE_NAME_NUM_FILES, VALUE_NAME_SIZE_BYTES, Config,
    TNamedDirs, load_config, save_config,
)
from lidske_aktivity.icon import COLOR_GRAY, Color, color_from_index
from lidske_aktivity.utils import filesystem, func
from lidske_aktivity.utils.math import safe_div

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(f'sqlite:///{CACHE_PATH}')
session_factory = sessionmaker(bind=engine)


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

    def get_value(self, value_name: str, threshold_days_ago: int) -> float:
        for stat in self.stats:
            if stat.threshold_days_ago == threshold_days_ago:
                return getattr(stat, value_name)
        return 0

    def __repr__(self) -> str:
        return f'Directory(path={self.path}, stats={self.stats})'


Base.metadata.create_all(engine)


class Directories(list):
    _session: Session

    def __init__(self, paths: List[str]):
        self._session = scoped_session(session_factory)
        self.load(paths)

    def load(self, paths: Iterable[str]):
        """Create Directory objects for all passed paths.

        Either load from database (cache) or create new.
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
    value: float = 0
    fraction: float = 0
    text: str = ''
    tooltip: str = ''
    pending: bool = True


class DirectoryViews(dict):
    _value_name: str
    _threshold_days_ago: int

    def __init__(self,
                 value_name: str,
                 threshold_days_ago: int):
        self._value_name = value_name
        self._threshold_days_ago = threshold_days_ago

    def load(self, configured_dirs: TNamedDirs):
        self.clear()
        for path, label in configured_dirs.items():
            self[path] = DirectoryView(label)

    def update_all(self, directories: Directories):
        for directory in directories:
            value = directory.get_value(
                self._value_name,
                self._threshold_days_ago
            )
            self[directory.path] = self[directory.path]._replace(value=value)
        self._recalculate()

    def update_one(self, directory: Directory):
        value = directory.get_value(
            self._value_name,
            self._threshold_days_ago
        )
        self[directory.path] = self[directory.path]._replace(
            value=value,
            pending=False
        )
        self._recalculate()

    def _recalculate(self):
        total = sum(directory_view.value for directory_view in self.values())
        for path, directory_view in self.items():
            fraction = safe_div(directory_view.value, total)
            if directory_view.pending:
                text = f'{directory_view.label}: ...'
            else:
                text = f'{directory_view.label}: {fraction:.0%}'
            tooltip = self._format_tooltip(
                fraction,
                self._value_name,
                self._threshold_days_ago
            )
            self[path] = directory_view._replace(
                fraction=fraction,
                text=text,
                tooltip=tooltip
            )
        logger.info('Recalculated fractions: %s', self.fractions)

    @staticmethod
    def _format_tooltip(fraction: float,
                        value_name: str,
                        threshold_days_ago: int) -> str:
        value_text = {
            VALUE_NAME_SIZE_BYTES: 'of the size ',
            VALUE_NAME_NUM_FILES: '',
        }[value_name]
        if threshold_days_ago == 0:
            set_text = 'all files in configured directories'
        else:
            set_text = (f'the files modified in the past '
                        f'{threshold_days_ago} days')
        s = f'{fraction:.2%} {value_text}of {set_text}'
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

    def get_colors_with_one_highlighted(self, i: int) -> List[Color]:
        colors = [COLOR_GRAY for i in range(len(self))]
        colors[i] = color_from_index(i)
        return colors


class Model:
    _config: Config
    _directories: Directories
    directory_views: DirectoryViews

    _scan_event_stop: Event
    _scan_thread: Thread

    def __init__(self):
        self._config = load_config()
        self._directories = Directories(
            self._config.configured_dirs.keys(),
        )
        self.directory_views = DirectoryViews(
            self._config.value_name,
            self._config.threshold_days_ago
        )
        self._init()

    def _init(self):
        self._directories.load(self._config.configured_dirs.keys())
        self._directories.save()
        self.directory_views.load(self._config.configured_dirs)
        self.directory_views.update_all(self._directories)
        self._scan_start()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, config: Config):
        self._config = config
        save_config(config)
        self._directories.clear()
        self._init()

    def _scan_start(self):
        self._scan_event_stop = Event()

        def orchestrator():
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self._scan_directory, directory.path)
                    for directory in self._directories
                ]
                wait(futures)

        self._scan_thread = Thread(target=orchestrator)
        self._scan_thread.start()

    def scan_stop(self):
        self._scan_event_stop.set()
        self._scan_thread.join()
        logger.info('Scan stopped')

    @func.measure_time
    def _scan_directory(self, path: str):
        session = scoped_session(session_factory)
        directory = session.query(Directory).filter(
            Directory.path == path
        ).one()
        logger.info('Calculating size of "%s"', directory.path)
        threshold_seconds_ago = self._config.threshold_days_ago * 24 * 3600
        threshold_seconds = time.time() - threshold_seconds_ago
        dir_size = filesystem.calc_dir_size(
            directory.path,
            threshold_seconds=threshold_seconds,
            event_stop=self._scan_event_stop
        )
        directory.stats.clear()
        directory.stats.append(
            Stat(
                size_bytes=dir_size.size_bytes_all,
                num_files=dir_size.num_files_all,
                threshold_days_ago=0
            )
        )
        if self._config.threshold_days_ago != 0:
            directory.stats.append(
                Stat(
                    size_bytes=dir_size.size_bytes_new,
                    num_files=dir_size.num_files_new,
                    threshold_days_ago=self._config.threshold_days_ago
                )
            )
        if self._config.test:
            func.random_wait(self._scan_event_stop)
        logger.info(
            'Calculated size of "%s": %s',
            directory.path,
            directory.stats
        )
        logger.info('DB: Updating %s', directory)
        session.commit()
        self.directory_views.update_one(directory)
        session.close()
