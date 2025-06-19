"""
Drawing Window of PySide6 ... speaks for itself
"""
import sys

from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QSize, Signal

from core.renderer import Renderer
from core.menu import AppVolume
from core.ui_timers import UITimers
from core.menu_manager import MenuManager
from core.tray_controller import TrayController
from core.input_handler import InputHandler


class DrawingWindow(QMainWindow):
    """
    Drawing Window of PySide6 ... speaks for itself
    """
    start_inactivity_signal = Signal()
    stop_inactivity_signal = Signal()
    start_fade_signal = Signal()
    stop_fade_signal = Signal()
    close_application_signal = Signal()

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        callbacks = {
                "hide_menu": self.hide_menu,
                "close_app": self.close_application_signal.emit
        }

        self.close_application_signal.connect(sys.exit)

        screen = self._init_ui()

        self.menu_manager = MenuManager(self.settings, callbacks=callbacks)
        self.tray = TrayController(self, callbacks)
        self.renderer = Renderer(screen, self.settings)
        self.input = InputHandler(self)

        self.menu_manager.add_observer(self.renderer)

        self._init_timers()

        self.menu_visible = False

    def _init_ui(self):
        """ Initialize UI. """
        screen = QSize(330, 330)

        self.setGeometry(30, 1025, screen.width(), screen.height())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.Tool)

        return screen

    def _init_timers(self):
        """ Starts timer for UI refresh, inactivity timer and UI fade timer """
        self.timers = UITimers(self, self.settings)

        self.start_inactivity_signal.connect(self.timers.start_inactivity)
        self.stop_inactivity_signal.connect(self.timers.stop_inactivity)
        self.start_fade_signal.connect(self.timers.start_fade)
        self.stop_fade_signal.connect(self.timers.stop_fade)

    def _fade_step(self):
        """ Counts opacity for smooth menu disappearing. """
        self.renderer.render_state.opacity_multiplier -= self.settings.theme.fade_out_speed
        if self.renderer.render_state.opacity_multiplier <= 0:
            self.timers.stop_fade()
            self.menu_visible = False
            self.renderer.set_active_option(None)
            self.renderer.render_state.opacity_multiplier = 1

            self.settings.theme = self.settings.get_selected_theme()

            self.renderer.volume_animated = 1

        self.update()

    def _updatescreen(self):
        """ Forces UI refresh """
        if self.menu_visible:
            self.update()

    def paintEvent(self, _):
        """ Method handling drawing operation by PySide. """
        if not self.menu_visible:
            return

        theme = self.settings.get_showing_theme()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self.menu_visible:
            self.renderer.draw(painter, theme)

    def show_menu(self):
        """ Shows circular menu (application). """
        self.menu_manager.reload_menu()
        self.settings.icon_manager.load_icons(AppVolume.get_pid_dict())
        self.menu_visible = True
        self.menu_manager.return_top_level_menu()
        self.start_inactivity_signal.emit()

    def hide_menu(self):
        """ Starts opacity counter for smooth menu disappearing. """
        self.stop_inactivity_signal.emit()
        self.start_fade_signal.emit()
