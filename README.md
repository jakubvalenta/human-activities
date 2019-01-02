# Lidské aktivity

## Pre-requisites

- pipenv
- wxPython

Install on Arch Linux:

```
# pacman -S pipenv python-wxpython
```

## Usage

```
make run
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

### Mac (with Docker)

```
make dist-pyinstaller-docker
```

### Mac (without Docker)

```
make dist-pyinstaller
```
