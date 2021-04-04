import shutil
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest import TestCase, mock

from human_activities import (
    __application_id__,
    __application_name__,
    get_cache_dir,
)
from human_activities.config import change_user_dirs, get_fdignore_path

WIN_HOME = PureWindowsPath(r'C:\Documents and Settings\foo')
MAC_HOME = PurePosixPath('/Users/foo')
LINUX_HOME = PurePosixPath('/home/foo')
WIN_APPDATA = WIN_HOME / 'Application Data'
XDG_CACHE_HOME = LINUX_HOME / '.cache'


@mock.patch('platform.win32_ver', lambda: ('1',))
@mock.patch('platform.mac_ver', lambda: (None,))
@mock.patch('pathlib.Path.home', lambda: WIN_HOME)
class TestConfigWin(TestCase):
    @mock.patch.dict('os.environ', {'APPDATA': str(WIN_APPDATA)})
    def test_win(self):
        self.assertEqual(get_cache_dir(), WIN_APPDATA / __application_name__)

    @mock.patch.dict('os.environ', {'APPDATA': ''})
    def test_win_fallback(self):
        self.assertEqual(
            get_cache_dir(), WIN_HOME / '.cache' / __application_name__
        )


@mock.patch('platform.win32_ver', lambda: (None,))
@mock.patch('platform.mac_ver', lambda: ('1',))
@mock.patch('pathlib.Path.home', lambda: MAC_HOME)
class TestConfigMac(TestCase):
    def test_mac(self):
        self.assertEqual(
            get_cache_dir(), MAC_HOME / 'Caches' / __application_id__
        )


@mock.patch('platform.win32_ver', lambda: (None,))
@mock.patch('platform.mac_ver', lambda: (None,))
@mock.patch('pathlib.Path.home', lambda: LINUX_HOME)
class TestConfigLinux(TestCase):
    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': str(XDG_CACHE_HOME)})
    def test_linux(self):
        self.assertEqual(
            get_cache_dir(), XDG_CACHE_HOME / __application_name__
        )

    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': ''})
    def test_linux_fallback(self):
        self.assertEqual(
            get_cache_dir(), XDG_CACHE_HOME / __application_name__
        )


class TestConfigUserDirs(TestCase):
    def test_create_new_dirs(self):
        orig = '''
# This file is written by xdg-user-dirs-update
# If you want to change or add directories, just edit the line you're
# interested in. All local changes will be retained on the next run.
# Format is XDG_xxx_DIR="$HOME/yyy", where yyy is a shell-escaped
# homedir-relative path, or XDG_xxx_DIR="/yyy", where /yyy is an
# absolute path. No other format is supported.
#
XDG_DESKTOP_DIR="$HOME/Plocha"
XDG_DOWNLOAD_DIR="$HOME/Stažené"
XDG_TEMPLATES_DIR="$HOME/Šablony"
XDG_PUBLICSHARE_DIR="$HOME/Veřejné"
XDG_DOCUMENTS_DIR="$HOME"
XDG_MUSIC_DIR="$HOME/My Music"
XDG_PICTURES_DIR="$HOME/"
XDG_VIDEOS_DIR="$HOME/Videa"
'''
        expected = '''
# This file is written by xdg-user-dirs-update
# If you want to change or add directories, just edit the line you're
# interested in. All local changes will be retained on the next run.
# Format is XDG_xxx_DIR="$HOME/yyy", where yyy is a shell-escaped
# homedir-relative path, or XDG_xxx_DIR="/yyy", where /yyy is an
# absolute path. No other format is supported.
#
XDG_DESKTOP_DIR="$HOME/Plocha"
XDG_DOWNLOAD_DIR="$HOME/Stažené"
XDG_TEMPLATES_DIR="$HOME"
XDG_PUBLICSHARE_DIR="$HOME"
XDG_DOCUMENTS_DIR="$HOME"
XDG_MUSIC_DIR="$HOME"
XDG_PICTURES_DIR="$HOME"
XDG_VIDEOS_DIR="$HOME"
'''
        result = change_user_dirs(orig)
        self.assertEqual(result, expected)

    def test_create_new_dirs_custom(self):
        orig = '''XDG_TEMPLATES_DIR="/spam"
XDG_PUBLICSHARE_DIR="/spam"
XDG_DOCUMENTS_DIR="/spam"
'''
        result = change_user_dirs(orig)
        self.assertEqual(result, orig)


class TestConfigFdignore(TestCase):
    def setUp(self):
        self.config_dir = Path(tempfile.mkdtemp())
        self.config_global_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.config_dir)
        shutil.rmtree(self.config_global_dir)

    def test_user_fdignore(self):
        user_fdignore_path = (
            self.config_dir / f'{__application_name__}.fdignore'
        )
        user_fdignore_path.write_text('foo')
        self.assertEqual(
            get_fdignore_path(self.config_dir, self.config_global_dir),
            str(user_fdignore_path),
        )

    def test_global_fdignore_on_windows_or_mac(self):
        self.assertIsNone(get_fdignore_path(self.config_dir, None))

    def test_global_fdignore_on_linux(self):
        global_fdignore_path = (
            self.config_global_dir / f'{__application_name__}.fdignore'
        )
        global_fdignore_path.write_text('foo')
        self.assertEqual(
            get_fdignore_path(self.config_dir, self.config_global_dir),
            str(global_fdignore_path),
        )

    def test_global_fdignore_on_linux_in_bundle(self):
        self.assertIsNone(
            get_fdignore_path(self.config_dir, self.config_global_dir),
        )
