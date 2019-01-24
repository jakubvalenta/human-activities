# Lidské aktivity

## Installation

### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
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
    pip install Pillow sqlalchemy wxpython
    ```

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

### Debian

```
make dist-debian-build dist-debian
```

### Mac

```
pip install pyinstaller
sh pyinstaller/pyinstaller_mac.sh
```

### Windows

```
pip install pyinstaller
pyinstaller/pyinstaller_win.cmd
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

### Testing

```
make test
```

### Linting

```
make lint
```
