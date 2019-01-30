from pathlib import Path

from setuptools import find_packages, setup

from lidske_aktivity import (
    __application_name__, __author_email__, __authors__, __license__,
    __summary__, __uri__, __version__,
)

setup(
    name=__application_name__,
    version=__version__,
    description=__summary__,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    author=__authors__[0],
    author_email=__author_email__,
    url=__uri__,
    license=__license__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    data_files=[
        ('share/applications', [f'data/{__application_name__}.desktop']),
        ('share/icons/hicolor/scalable/apps',
         [f'data/{__application_name__}.svg']),
        ('share/pixmaps', [f'data/{__application_name__}.png']),
    ],
    entry_points={
        'console_scripts': [
            f'{__application_name__}=lidske_aktivity.cli:main',
        ],
    },
)
