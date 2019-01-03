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
    - [Cygwin](https://cygwin.com/setup-x86.exe) with packages:
        - git
        - make
        - nano
        - python3
        - python3-pip
    - [Python3](https://www.python.org/).

#. Open Cygwin Terminal.

#. Append to `.bash_profile`:

    ```
    alias python3=python
    alias pip3=pip
    ```

#. Clone this repo.

#. Install Python dependencies:

    ```
    $ pip3 install pipenv wxpython
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
