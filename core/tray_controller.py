""" Loads Tray icon and initializes tray menu """
import os

from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from PySide6.QtGui import QIcon, QAction
from core.resource_loader import Loader

class TrayController:
    """ Loads Tray icon and initializes tray menu """
    def __init__(self, parent, callbacks):
        self.tray_icon = QSystemTrayIcon(parent)

        self.load_tray_icon("./icons/internal/AppIcon.png")

        self.tray_icon.setContextMenu(self.load_menu(parent, callbacks))
        self.tray_icon.show()

    def load_tray_icon(self, path):
        """ Loads tray icon """
        if os.path.exists(path):
            self.tray_icon.setIcon(QIcon(path))
        else:
            self.tray_icon.setIcon(QIcon(Loader.resource_path(path)))

    def load_menu(self, parent, callbacks):
        """ Creates menu """
        menu = QMenu()
        quit_action = QAction("Exit", parent)
        quit_action.triggered.connect(callbacks["close_app"])
        menu.addAction(quit_action)
        return menu
