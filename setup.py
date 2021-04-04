import glob
from pathlib import Path

from setuptools import find_packages, setup

from human_activities import (
    __application_name__,
    __author_email__,
    __authors__,
    __summary__,
    __uri__,
    __version__,
)

setup(
    name=__application_name__,
    version=__version__,
    description=__summary__,
    long_description=(Path(__file__).parent / 'README.rst').read_text(),
    author=__authors__[0],
    author_email=__author_email__,
    url=__uri__,
    license='GNU General Public License v3 or later (GPLv3+)',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa: E501
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    package_data={'': ['locale/*/LC_MESSAGES/*.mo']},
    data_files=[
        ('share/applications', [f'data/{__application_name__}.desktop']),
        (
            'share/icons/hicolor/scalable/apps',
            [f'data/{__application_name__}.svg'],
        ),
        ('share/pixmaps', [f'data/{__application_name__}.png']),
        (
            f'etc/xdg/{__application_name__}',
            [f'human_activities/etc/{__application_name__}.fdignore'],
        ),
    ]
    + [
        (
            str(
                Path('share/locale')
                / Path(path).parent.relative_to('human_activities/locale')
            ),
            [path],
        )
        for path in glob.glob(
            'human_activities/locale/**/*.mo', recursive=True
        )
    ],
    entry_points={
        'console_scripts': [
            f'{__application_name__}=human_activities.cli:main'
        ]
    },
)
