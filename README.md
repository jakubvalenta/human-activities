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

#. Open Command Prompt.

#. Clone this repo.

#. Install Python dependencies:

    ```
    $ pip install pipenv wxpython pyinstaller
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
make dist-pyinstaller
```

### Windows

```
pyinstaller/bin/pyinstaller_win.cmd
```
