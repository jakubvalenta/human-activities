from pathlib import Path

from setuptools import find_packages, setup

from lidske_aktivity import (
    __author_email__, __authors__, __license__, __summary__, __uri__,
    __version__,
)

setup(
    name='lidske-aktivity',
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
        ('share/applications', ['data/lidske-aktivity.desktop']),
        ('etc/xdg/autostart', ['data/lidske-aktivity.desktop']),
        ('share/icons/hicolor/scalable/apps', ['data/lidske-aktivity.svg']),
        ('share/pixmaps', ['data/lidske-aktivity.png']),
    ],
    entry_points={
        'console_scripts': [
            'lidske-aktivity=lidske_aktivity.cli:main',
        ],
    },
)
