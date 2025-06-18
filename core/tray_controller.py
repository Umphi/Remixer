""" Loads Tray icon and initializes tray menu """
import os

from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from PySide6.QtGui import QIcon, QAction
from core.resource_loader import Loader

class TrayController:
    """ Loads Tray icon and initializes tray menu """
    def __init__(self, parent, callbacks):
        self.tray_icon = QSystemTrayIcon(parent)

        if os.path.exists("./icons/internal/AppIcon.png"):
            self.tray_icon.setIcon(QIcon('./icons/internal/AppIcon.png'))
        else:
            self.tray_icon.setIcon(QIcon(Loader.resource_path('./icons/internal/AppIcon.png')))

        self.tray_menu = QMenu()

        self.quit_action = QAction("Exit", parent)
        self.quit_action.triggered.connect(callbacks["close_app"])
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
