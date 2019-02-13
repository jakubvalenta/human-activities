# Lidské Aktivity

## Installation

### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
# make install DESTDIR=/
# systemctl enable lidske-aktivity.timer
# systemctl start lidske-aktivity.timer
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
python3 -m lidske_aktivity --verbose
```

### Windows

```
python -m lidske_aktivity --verbose
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

### Linux with Pyinstaller

```
make dist-pyinstaller-build dist-pyinstaller
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
