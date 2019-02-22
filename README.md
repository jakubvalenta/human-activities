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

### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
# make install DESTDIR=/
# systemctl enable human-activities.timer
# systemctl start human-activities.timer
```

### Mac

```
pip3 install Pillow sqlalchemy wxpython
```

### Windows

```
pip install Pillow sqlalchemy wxpython
```

## Usage

### Linux

```
make run
```

Debugging:

```
make run-debug
```

### Mac

```
python3 -m human_activities --verbose
```

### Windows

```
python -m human_activities --verbose
```

## Building distribution package

### Arch Linux

```
make dist-arch-linux-build dist-arch-linux
```

Notice that the package is not built from the currently checked out revision,
but from a git tag specified as `v` + Makefile variable `_version`.

### Debian

```
make dist-debian-build dist-debian
```

### Mac

```
pip3 install pyinstaller
sh mac/pyinstaller.sh
```

### Windows

```
pip install pyinstaller
win/pyinstaller.cmd
```

## Debugging

### Ubuntu

```
# apt install libgtk-3-dev
gsettings set org.gtk.Settings.Debug enable-inspector-keybinding true
```

Then start the app and run GTK Inspector with `CTRL+SHIFT+i`.

## Development

### Installation

```
make setup-dev
```

### Translation

Edit the `lang/*.po` files and then run:

```
make clean-lang gen-lang
```

### Testing

```
make test
```

### Linting

```
make lint
```
