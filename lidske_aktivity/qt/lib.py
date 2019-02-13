import logging
import signal
import sys

from PyQt5 import QtGui, QtWidgets

logger = logging.getLogger(__name__)


def refresh(*args):
    logger.warning('Hello')


class Application(QtWidgets.QApplication):
    def event(self, e):
        return QtWidgets.QApplication.event(self, e)


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)
        self.refresh_action = self.menu.addAction("Refresh")
        self.exit_action = self.menu.addAction("Exit")
        self.refresh_action.triggered.connect(refresh)
        self.setContextMenu(self.menu)


def main():
    app = Application(sys.argv)
    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtWidgets.QStyle.SP_FileIcon))
    tray_icon = SystemTrayIcon(icon)
    tray_icon.exit_action.triggered.connect(app.quit)
    signal.signal(signal.SIGINT, lambda *a: app.quit())
    # Timer calls Application.event repeatedly.
    app.startTimer(200)
    tray_icon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
