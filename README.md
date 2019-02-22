# Human Activities

/monitor size of directories/

Human Activities is an application that displays a pie chart icon in the Windows
Taskbar, macOS Menu Bar or Linux System Tray. The icon shows ratio between the
size of configured directories. When clicked, a menu with a list of the
directories and their exact size in bytes appears.

The application can be configured to compare number of files instead of size of
directories. It can also be configured to only count files that are newer than
specified number of days.

## Installation

### Windows

1. Download and open [Human Activities.exe][]. The app will start
   immediatelly, it doesn't need any special installation.
2. To automatically start /Human Activities/ each time your PC starts, copy
   /Human Activities.exe/ into the /Startup/ folder of the Start Menu.
3. If you need to click the arrow icon in the Taskbar to see /Human Activities/,
   open the /Customize/ window of the Taskbar and choose /Show icon and
   notifications/ next to the item /Human Activities/.

### macOS

1. Download [Human Activities.app][] and move it to /Applications/.
2. /Human Activities/ can now be started from /Launcher/.
3. To automatically start /Human Activities/ each time your Mac starts, open
   /System Preferences/ > /Users & Groups/, click on the tab /Login Items/,
   click on the little plus sign icon and select the app /Human Activities/.

### Ubuntu

1. Download and open [human-activities_0.8.0-1_all.deb][].
2. Click the button /Install/ in the window that appears.
3. /Human Acitivies/ can now be started from the main /Applications/ menu. It
   will also start automatically every time your PC starts.

### Arch Linux

Download [human-activities-0.8.0-1-any.pkg.tar.xz][] and install it using
pacman. Then enable and start the `human-activities.timer` systemd unit.

## Usage

When Human Activities is started for the first time, it will show a setup window
(this might take a few seconds).

TODO

## Uninstallation

### Windows

Delete /Human Activities.exe/ from the /Startup/ folder of the Start Menu.

### macOS

Delete /Human Activities.app/ from the /Applications/ folder.

### Ubuntu

Open /Ubuntu Software/, click on the tab /Installed/, scroll to /Human Activities/ and click the button /Remove/.

### Arch Linux

```
pacman -Rcsn human-activities
```

## Development

### Building and running from source

#### Windows

```
pip install Pillow sqlalchemy wxpython
python -m human_activities --verbose
```

#### Mac

```
pip3 install Pillow sqlalchemy PyQt5
python3 -m human_activities --verbose
```

#### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
$ make run-debug
```

### Creating distribution packages

#### Windows

```
pip install pyinstaller
win/pyinstaller.cmd
```

#### Mac

```
pip3 install pyinstaller
sh mac/pyinstaller.sh
```

#### Debian

```
make dist-debian-build dist-debian
```

#### Arch Linux

```
make dist-arch-linux-build dist-arch-linux
```

Notice that the package is not built from the currently checked out revision,
but from a git tag specified as `v` + Makefile variable `_version`.

### Translation

Edit the `lang/*.po` files and then run:

```
make clean-lang gen-lang
```

### Testing and linting

```
make test
make lint
```

[Human Activities.exe]: <https://human-activities.jakubvalenta.cz/download/0.8.0/Human%20Activities.exe>
[Human Activities.app]: <https://human-activities.jakubvalenta.cz/download/0.8.0/Human%20Activities.app>
[human-activities_0.8.0-1_all.deb]: <https://human-activities.jakubvalenta.cz/download/0.8.0/human-activities_0.8.0-1_all.deb>
[human-activities-0.8.0-1-any.pkg.tar.xz]: <https://human-activities.jakubvalenta.cz/download/0.8.0/human-activities-0.8.0-1-any.pkg.tar.xz>
