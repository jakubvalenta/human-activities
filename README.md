# Lidské aktivity

## Installation

### Arch Linux

```
# pacman -S pipenv python-wxpython
$ make setup
```

### Windows

#. Install pre-requisites:

    - [Git](https://www.git-scm.com/).
    - [Python3](https://www.python.org/).
    - [Cygwin](https://cygwin.com/setup-x86.exe) including 'make' and 'nano'.
    - [Visual C++ Redistributable for Visual Studio
       2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145).

#. Open Cygwin Terminal.

#. Clone this repo.

#. Install Python dependencies:

    ```
    $ pip install pipenv wxpython
    $ make setup
    ```

## Usage

```
make run
```

Debugging:

```
make run-debug
```

When there is no `python3` executable:

```
pipenv run python -m lidske_aktivity --verbose
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
make dist-pyinstaller
```
