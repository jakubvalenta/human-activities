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

### Windows

#. Install [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145).

#. Install [Git](https://www.git-scm.com/).

#. Install [Python3](https://www.python.org/).

    Check _Add python to environment variables_.

#. Open Git Bash.

#. Configure Git:

    ```
    git config --global user.name "Jakub Valenta"
    git config --global user.email "jakub@jakubvalenta.cz"
    ```

#. Clone this repo:

    ```
    git clone gogs@lab.saloun.cz:jakub/art-lidske-aktivity-gtk.git
    ```

#. Install Python dependencies:

    ```
    pip install Pillow gettext_windows sqlalchemy wxpython
    ```

#. Optional: Install additional language pack via Windows Update to test translations.

## Usage

### Linux and Mac

```
make run
```

Debugging:

```
make run-debug
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
pip install pyinstaller
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
