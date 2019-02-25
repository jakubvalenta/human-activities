Human Activities
================

*monitor size of directories*

Human Activities is an application that displays a pie chart icon in the Windows
Taskbar, macOS Menu Bar or Linux System Tray. The icon shows ratio between the
size of configured directories. When clicked, a menu with a list of the
directories and their exact size in bytes appears.

[screenshot icon+menu windows]

[screenshot icon+menu mac]

[screenshot icon+menu ubuntu]

The application can be configured to compare number of files instead of size of
directories. It can also be configured to only count files that are newer than
specified number of days.

[screenshot configuration]

Human Activities is an offline application. It doesn't send any data outside of
your computer.

Installation
------------

Windows
^^^^^^^

Requires Windows 7 or newer.

1. Download and open `Human Activities.exe`_. The app will start
   immediatelly, it doesn't need any special installation.
2. To automatically start Human Activities each time your PC starts, copy *Human
   Activities.exe* into the *Startup* folder of the Start Menu.

   [screenshot moving to startup]

3. If you need to click the arrow icon in the Taskbar to see Human Activities,
   open the *Customize* window of the Taskbar and choose *Show icon and
   notifications* next to the item *Human Activities*.

   [screenshot taskbar customize button]

   [screenshot taskbar customize window]

macOS
^^^^^

Tested on macOS Mojave.

1. Download `Human Activities.app`_ and move it to *Applications*.

   [screenshot moving to applications]

2. Human Activities can now be started from *Launcher*.

   [screenshot launcher]

3. To automatically start Human Activities each time your Mac starts, open
   *System Preferences* > *Users & Groups*, click on the tab *Login Items*,
   click on the little plus sign icon and select the app *Human Activities*.

   [screenshot users & groups preferences]

Ubuntu
^^^^^^

Tested on Ubuntu 18.04 LTS.

1. Download and open `human-activities_0.9.0-1_all.deb`_.
2. Click the button *Install* in the window that appears.

   [screenshot install window]

3. Human Acitivies can now be started from the main *Applications* menu. It will
   also start automatically every time your PC starts.

Arch Linux
^^^^^^^^^^

Download `human-activities-0.9.0-1-any.pkg.tar.xz`_ and install it using
pacman.

Usage
-----

Setup
^^^^^

When Human Activities is started for the first time, it will show a **setup
window** (this might take a few seconds).

[screenshot setup window]

Here you can choose which directories to monitor. You can only **choose existing
directories**. The app doesn't create any new directories itself. When you
remove a directory, it will only be remove from the app, your files will stay on
the disk. Human Activities never creates, modifies or deletes any files.

Icon
^^^^

[screenshot icon]

When the setup is finished, Human Activities shows a pie chart icon with ratio
between the size of the directories configured in the setup.

How is the pie chart calculated
"""""""""""""""""""""""""""""""

Let's assume we chose 2 directories in the setup:

- ``/Users/jakub/Paid work`` which is 1.5 GB large
- ``/Users/jakub/Unpaid work`` which is 3 GB large

Human Activities will first calculate the **sum of the size of these
directories**, which is 4.5 GB. This will be the **100%**. Therefore ``Paid work``
takes 33.3% and ``Unpaid work`` takes 66.6% of the total size. This percentage will then
be shown as a pie chart, which is ⅓ one color and ⅔ another color.

Colors
""""""

The **colors** are assigned to the directories automatically.

Menu
^^^^

[screenshot menu]

When you click the icon you can see a menu with the **exact size of the
directories** in bytes and the exact percentages.

You can also see a note, that **only files modified in the past 30 days** are
counted to the size of a directory. This behavior can be changed in the
*Advanced configuration*.

From this menu you can also reach the *Setup* (which you saw when you first
started the app) and the *Advanced configuration*. On Windows, these items are
accessible in separate menu that opens when you right-click the icon.

[screenshot windows right-click menu]

Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

[screenshot advanced configuration]

The advanced configuration allows you to:

- **Count the number of files instead of the size of the directories.**
- Change how new the files have to be to be counted.
- Give custom names to the configured directories.

Uninstallation
--------------

Windows
^^^^^^^

Delete *Human Activities.exe* from the *Startup* folder of the Start Menu.

macOS
^^^^^

Delete *Human Activities.app* from the *Applications* folder.

Ubuntu
^^^^^^

Open *Ubuntu Software*, click on the tab *Installed*, scroll to *Human Activities* and click the button *Remove*.

Arch Linux
^^^^^^^^^^

Uninstall the package ``human-activities`` using pacman.

Support and help
----------------

Please contact us at [TODO email].

Development
-----------

Building and running from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Windows
"""""""

::

   pip install Pillow sqlalchemy wxpython
   python -m human_activities --verbose

Mac
"""

::

   pip3 install Pillow sqlalchemy PyQt5
   python3 -m human_activities --verbose

Arch Linux
""""""""""

::

   # pacman -S pipenv python-wxpython
   $ make setup
   $ make run-debug

Creating distribution packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Windows
"""""""

::

   pip install pyinstaller
   win/pyinstaller.cmd

Mac
"""

::

   pip3 install pyinstaller
   sh mac/pyinstaller.sh

Debian
""""""

::

   make dist-debian-build dist-debian

Arch Linux
""""""""""

::

   make dist-arch-linux-build dist-arch-linux

Notice that the package is not built from the currently checked out revision,
but from a git tag specified as ``v`` + Makefile variable ``_version``.

Translation
^^^^^^^^^^^

Edit the ``lang/*.po`` files and then run::

   make clean-lang gen-lang

Testing and linting
^^^^^^^^^^^^^^^^^^^

::

   make test
   make lint

.. _Human Activities.exe: https://github.com/jakubvalenta/human-activities/releases/download/v0.9.0/Human%20Activities.exe
.. _Human Activities.app: https://github.com/jakubvalenta/human-activities/releases/download/v0.9.0/Human%20Activities.app
.. _human-activities_0.9.0-1_all.deb: https://github.com/jakubvalenta/human-activities/releases/download/v0.9.0/human-activities_0.9.0-1_all.deb
.. _human-activities-0.9.0-1-any.pkg.tar.xz: https://github.com/jakubvalenta/human-activities/releases/download/v0.9.0/human-activities-0.9.0-1-any.pkg.tar.xz
