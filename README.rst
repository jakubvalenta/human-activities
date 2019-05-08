Human Activities
================

*monitor size of directories*

Human Activities is an application that displays a pie chart icon in the Windows
Taskbar, macOS Menu Bar or Linux System Tray. The icon shows ratio between the
number of files in configured directories. When clicked, a menu with a list of
the directories and the exact number of files appears.

.. image:: ./screenshots/human_activities_macos.png
   :alt: Human Activities running on macOS

.. image:: ./screenshots/human_activities_win7.png
   :alt: Human Activities running on Windows 7

.. image:: ./screenshots/human_activities_ubuntu.png
   :alt: Human Activities running on Ubuntu

The application can be configured to compare the size of the data in the
directories instead of the number of files in them. It can also be configured to
only count files that are newer than specified number of days.

.. image:: ./screenshots/human_activities_macos_configuration.png
   :alt: Advanced configuration of Human Activities

Human Activities is an offline application. It doesn't send any data over the
internet.

The `Human Activities`_ project was partially financed by `The Foundation for
Contemporary Arts Prague`_.

Installation
------------

Windows 7 and 8
^^^^^^^^^^^^^^^

1. Download and open `Human.Activities-win7.exe`_. The app will start
   immediately. No installation process is required.
2. To launch the application automatically each time you start the computer,
   copy ``Human Activities.exe`` into the *Startup* folder of the Start Menu.
3. To make sure that the application icon is always visible:

   a) Click the arrow icon in the Taskbar and select *Customize*.
   b) In the window that opens up, choose *Show icon and notifications* next to
      the item *Human Activities*.

Windows 10
^^^^^^^^^^

1. Download and open `Human.Activities-win10.exe`_. The app will start
   immediately. No installation process is required.
2. To launch the application automatically each time you start the computer:

   a) Press ``WIN+R``. In the window that pops up, write the command
      ``shell:startup`` and click OK.
   b) Then move ``Human Activities.exe`` to the window that opens up.

3. To make sure that the application icon is always visible:

   a) Click on the arrow icon (*Show Hidden Icons*) in the Taskbar and select *Taskbar Settings*.
   b) In the window that opens up, click on *Select which icons appear on the
      Taskbar* and then switch item *Human Acitivities* on.

macOS
^^^^^

Requires macOS Mojave.

1. Download `Human.Activities.0.11.0.zip`_ and open it.
2. Move the file ``Human.Activities.app`` to *Applications*.
3. Human Activities can now be started from *Launcher*.
4. To launch the application automatically each time you start the computer:

   a) Open *System Preferences* > *Users & Groups*.
   b) Click on the tab *Login Items*,
   c) Click on the little plus sign icon and select the app *Human Activities*.

Ubuntu
^^^^^^

Tested on Ubuntu 18.04 LTS.

1. Download and open `human-activities_0.11.0-1_all.deb`_.
2. Click the button *Install* in the window that opens up.
3. Human Acitivies can now be started from the main *Applications* menu. It will
   also start automatically each time you start the computer.

Arch Linux
^^^^^^^^^^

Download `human-activities-0.11.0-1-any.pkg.tar.xz`_ and install it using
pacman.

Usage
-----

Setup
^^^^^

When Human Activities is started for the first time, it will show a **setup
window** (this might take a few seconds).

.. image:: ./screenshots/human_activities_macos_setup.png
   :alt: Setup of Human Activities

Here you can choose which directories to monitor. You can only **choose existing
directories**. The app doesn't create any new directories itself. When you
remove a directory, it will only be remove from the app, your files will stay on
the disk. Human Activities never creates, modifies or deletes any files.

Icon and menu
^^^^^^^^^^^^^

.. image:: ./screenshots/human_activities_macos.png
   :alt: Human Activities running on macOS

When the setup is finished, Human Activities shows a **pie chart** icon with
ratio between the number of files in the directories configured in the
setup. The **colors** are assigned to the directories automatically.

When you click the icon you can see a **menu** with the exact number of files in
the directories and the exact percentages.

You can also see a note, that **only files modified in the past 30 days** are
counted to the size of a directory. This behavior can be changed in the
*Advanced configuration*.

From the menu, you can also reach the *Setup* (which you saw when you first
started the app) and the *Advanced configuration*. On Windows, these items are
accessible in separate menu that opens when you right-click the icon.

How is the pie chart calculated
"""""""""""""""""""""""""""""""

Let's assume we chose 2 directories in the setup:

- ``/Users/jakub/Paid work`` which contains 15 files
- ``/Users/jakub/Unpaid work`` which contains 30 files

Human Activities will first calculate the **sum of the number of files in both
directories**, which is 45. This will be the **100%**. Therefore ``Paid work``
takes 33.3% and ``Unpaid work`` takes 66.6% of the total number of files. This
percentage will then be shown as a pie chart, which is ⅓ one color and ⅔ another
color.

Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./screenshots/human_activities_macos_configuration.png
   :alt: Advanced configuration of Human Activities

The advanced configuration allows you to:

- **Count the size of the data in the directories instead of the number of files
  in them.**
- Change how new (in terms of modification time) the files have to be to be
  counted.
- Give custom names to the configured directories.

Uninstallation
--------------

Windows 7
^^^^^^^^^

Delete ``Human Activities.exe`` from the *Startup* folder of the Start Menu.

Windows 10
^^^^^^^^^^

1. Press ``WIN+R``. In the window that pops up, write the command
   ``shell:startup`` and click OK.
2. Then delete ``Human Activities.exe`` from the window that opens up.

macOS
^^^^^

Delete ``Human.Activities.app`` from the *Applications* folder.

Ubuntu
^^^^^^

1. Open *Ubuntu Software* and click on the tab *Installed*.
2. Scroll to *Human Activities* and click the button *Remove*.

Arch Linux
^^^^^^^^^^

Uninstall the package ``human-activities`` using pacman.

Support and help
----------------

Please use `GitHub Issues`_.

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
   make dist-mac

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

.. _Human Activities: http://humanactivities.cz/
.. _The Foundation for Contemporary Arts Prague: https://fca.fcca.cz/en/news/
.. _Human.Activities-win7.exe: https://github.com/jakubvalenta/human-activities/releases/download/v0.11.0/Human.Activities-win7.exe
.. _Human.Activities-win10.exe: https://github.com/jakubvalenta/human-activities/releases/download/v0.11.0/Human.Activities-win10.exe
.. _Human.Activities.0.11.0.zip: https://github.com/jakubvalenta/human-activities/releases/download/v0.11.0/Human.Activities.0.11.0.zip
.. _human-activities_0.11.0-1_all.deb: https://github.com/jakubvalenta/human-activities/releases/download/v0.11.0/human-activities_0.11.0-1_all.deb
.. _human-activities-0.11.0-1-any.pkg.tar.xz: https://github.com/jakubvalenta/human-activities/releases/download/v0.11.0/human-activities-0.11.0-1-any.pkg.tar.xz
.. _GitHub Issues: https://github.com/jakubvalenta/human-activities/issues
