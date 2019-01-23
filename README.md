# Lidské aktivity

## Installation

### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
```

### Windows

#. Install pre-requisites:

    - [Visual C++ Redistributable for Visual Studio
       2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145).
    - [Git](https://www.git-scm.com/).
    - [Python3](https://www.python.org/).

#. Open Git bash.

#. Clone this repo.

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
