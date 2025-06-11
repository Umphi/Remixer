"""
Main application module of Remixer. 
It is little bit of a chaos there right now. Working on it.
"""

import sys
import time
import json
import os
import math
import keyboard

from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
from PyQt6.QtGui import QPainter, QColor, QIcon, QAction
from PyQt6.QtCore import Qt, QTimer, QSize
from pycaw.pycaw import AudioUtilities

from core.renderer import Renderer
from core.menu import Menu, Placeholder, Button, AppVolume
from core.remixer_theme import RemixerTheme as Theme
from core.settings import SettingsManager
from modules.scroller import AdaptiveTouchScroller as Scroller
from modules.serial_port import SerialDevice


class DrawingWindow(QMainWindow):
    """
    DrawingWindow object of PyQt6 ... speaks for itself
    """
    # pylint: disable=too-many-instance-attributes
    # Rework in progress.
    def __init__(self, app):
        super().__init__()

        self.refresh_rate = 165

        self.settings = SettingsManager(refresh_rate=self.refresh_rate)

        self.renderer = None

        self.init_ui()
        self._init_timers()

        self.setWindowFlag(Qt.WindowType.Tool)

        self.credits = "Version: 1.0 Alpha\nRemixer\nby Umphi"

        self.last_volume_adjust_time = 0
        self.volume_adjust_rate = 1

        self.quit_action = QAction("Exit", self)
        self.quit_action.triggered.connect(app.quit)
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists("./icons/internal/AppIcon.png"):
            self.tray_icon.setIcon(QIcon('./icons/internal/AppIcon.png'))
        else:
            self.tray_icon.setIcon(QIcon(self.resource_path('./icons/internal/AppIcon.png')))

        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        self.scroller = Scroller(
                                step_pixels=300,
                                tick_rate_hz=self.refresh_rate,
                                base_decay_rate=0.5,
                                speed_min=1.0,
                                speed_max=50.0,
                                fps_min=7.5,
                                fps_max=50.0
        )

        self.icons = {}
        self.colored_icons = {}
        self.sessions = []

        self.menu_visible = False

        self.current_menu = {}
        self.menu_stack = []
        self.menu_keys = []

        self.scroll_mode = False
        self.scroll_direction = "vertical"

        self._reload_apps()

    def init_ui(self):
        """
        Initialize UI.
        """
        self.screen_size = QSize(330, 330)
        screen = self.screen_size
        self.setGeometry(30, 1025, screen.width(), screen.height())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.renderer = Renderer(screen, self.refresh_rate, self.settings)

        self.pen_width = 4
        self.pen_color = QColor(255, 0, 0)

    def _init_timers(self):
        """
        Starts timer for UI refresh, inactivity timer and UI fade timer
        """
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_step)
        self.fade_timer.setInterval(math.floor(1000/self.refresh_rate))

        self.draw_timer = QTimer(self)
        self.draw_timer.timeout.connect(self._updatescreen)
        self.draw_timer.start(math.floor(1000/self.refresh_rate))

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(self.settings.get_selected_theme().fade_out_timeout)
        self.inactivity_timer.timeout.connect(self.hide_menu)

    def _updatescreen(self):
        """
        Forces UI refresh
        """
        if self.menu_visible:
            self.update()

    def paintEvent(self, event): # pylint: disable=unused-argument disable=invalid-name # Reason: Method provided by PyQt
        """
        Method handling drawing operation by PyQt
        """
        if not self.menu_visible:
            return

        theme = self.settings.get_showing_theme()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self.menu_visible:
            self.renderer.draw(painter, theme, self.current_menu.items)

    def _reload_apps(self):
        """
        Reloads menu with updating available applications producing sound.
        """
        if self.menu_visible:
            return

        self.sessions = AudioUtilities.GetAllSessions()

        current_menu = Menu("Main", None, None)
        current_menu.add_item(Menu("Settings",
                                "Settings",
                                [
                                    Menu(
                                        "Theme",
                                        "Theme"
                                    ),
                                    Placeholder(
                                                "Credits",
                                                "Credits",
                                                self.credits
                                    ),
                                    Button(
                                            "Back",
                                            "Back", 
                                            self.menu_back
                                    ),
                                    Menu(
                                            "Exit",
                                            "Exit",
                                            [
                                                Button("Back",
                                                      "Back",
                                                      self.menu_back
                                                      ),
                                                Button("Confirm Exit",
                                                       "Exit", 
                                                       sys.exit
                                                       )
                                            ]
                                        )
                                    ]
                                )
                            )
        current_menu.add_item(Button("Hide", "Close", self.hide_menu))

        for theme in self.settings.themes:
            current_menu.index("Settings").index("Theme").add_item(theme)

        for session in self.sessions:
            if session.Process:
                name = session.Process.name()
                if name in self.settings.ignored_apps:
                    continue
                alias = self.settings.aliases.get(name, name.replace(".exe", ""))
                current_menu.add_item(
                                    AppVolume(
                                            alias,
                                            name,
                                            session,
                                            filename_ = name,
                                            pid_ = session.Process.pid
                                    )
                )

        self.current_menu = current_menu
        self.menu_stack = []

        self.renderer.update_apps()

    def _set_focus_target(self, set_current=False):
        """
        Sets user pointer target angle(for animated shifting)

        Parameters:
            set_current (bool): Forces user pointer to change position instantly without animation.
        """
        angle = 360 / len(self.current_menu.items)
        start_angle = (self.renderer.focused_index * angle - 90) * 16
        span_angle = angle * 16
        self.renderer.focus_pie_target = int((start_angle+span_angle/2)/16)

        if self.renderer.focus_pie_target < 0:
            self.renderer.focus_pie_target = 360 + self.renderer.focus_pie_target
        if set_current:
            self.renderer.focus_pie_angle = self.renderer.focus_pie_target

    def _fade_step(self):
        """
        Counts opacity for smooth menu disappearing.
        """
        self.renderer.opacity_multiplier -= self.settings.theme.fade_out_speed
        if self.renderer.opacity_multiplier <= 0:
            self.fade_timer.stop()
            self.menu_visible = False
            self.renderer.set_active_option(None)
            self.renderer.opacity_multiplier = 1
            self.renderer.set_turn(None)

            self.settings.theme = self.settings.get_selected_theme()

            self.renderer.volume_animated = 1

            if len(self.menu_stack) > 0:
                self.menu_stack.reverse()
                self.current_menu, focused_index = self.menu_stack.pop()
                self.renderer.set_focused_index(focused_index)
                self.menu_stack.clear()
                self.renderer.focus_pie_target_span = 360*16/len(self.current_menu.items)
                self.renderer.focus_pie_span = self.renderer.focus_pie_target_span
        self.update()

    def show_menu(self):
        """
        Shows circular menu (application)
        """
        self._reload_apps()
        self.menu_visible = True
        self.renderer.set_focused_index(0)
        self._set_focus_target(True)
        self.inactivity_timer.start()

    def hide_menu(self):
        """
        Starts opacity counter for smooth menu disappearing
        """
        self.inactivity_timer.stop()
        self.fade_timer.start()


    def scroll(self, scroll_direction, _direction):
        """
        Handles scroll action in scroll_mode (only with custom controls)

        Parameters:
            scroll_direction (str): "horizontal" or "vertical" scrolling.
            _direction (str): "clockwise" or "anticlockwise".
        """
        if scroll_direction == "horizontal":
            self.scroller.scroll_pixels_horizontal(10 if _direction == "clockwise" else -10)
        else:
            self.scroller.scroll_pixels(10 if _direction == "clockwise" else -10)

    def adjust_volume(self, option, delta):
        """
        Main function to change application volume

        Parameters:
            option (AppVolume): AppVolume(MenuItem) element in menu.
            delta (float): 0 < delta < 1 parameter to shift volume.
        """
        if option.session.Process:
            volume = option.session.SimpleAudioVolume
            new_volume = max(0, min(1, volume.GetMasterVolume() + delta))
            volume.SetMasterVolume(new_volume, None)
            self.renderer.current_volume = new_volume

    def get_volume_delta(self, base_delta):
        """
        Calculates progressive delta to shift volume in relation to user commands frequency.

        Parameters:
            base_delta (float): Default delta (like if user pressed volume button one time only).
        """
        now = time.time()
        dt = now - self.last_volume_adjust_time

        if dt > 0.28:
            self.volume_adjust_rate = 1

        if dt < 0.12:
            self.volume_adjust_rate = min(10, self.volume_adjust_rate + 0.5)
        else:
            self.volume_adjust_rate = max(1, self.volume_adjust_rate - 0.5)

        self.last_volume_adjust_time = now
        return base_delta * self.volume_adjust_rate

    def change_theme(self, theme):
        """
        Activates in settings.

        Parameters:
            Theme (Theme): Theme to activate.
        """
        self.settings.change_theme(theme)
        self.inactivity_timer.setInterval(self.settings.get_selected_theme().fade_out_timeout)
        self.load_colored_icons()

    def menu_back(self):
        """
        Returns to parent menu.
        """
        self.current_menu, focused_index = self.menu_stack.pop()
        self.renderer.set_focused_index(focused_index)
        self.renderer.set_turn(None)
        self._set_focus_target()


    def control_click_safe(self):
        """
        Mute button press handler (or volume knob press, or whatever custom control you use).
        Typical action in scroll mode: 
            changes "vertical" to "horizontal" and vice versa
        Typical action in default mode:
            shows menu if hidden,
            performs Menu Items' actions if menu shown
        """
        if self.scroll_mode:
            if self.scroll_direction == "horizontal":
                self.scroll_direction = "vertical"
            else:
                self.scroll_direction = "horizontal"
            return

        if not self.menu_visible:
            self.show_menu()
            return

        self.renderer.set_turn(None)

        focused_option = self.current_menu.items[self.renderer.focused_index]
        self.inactivity_timer.start()

        if self.renderer.active_option:
            self.renderer.set_active_option(None)
            return

        if isinstance(focused_option, Button):
            focused_option.action()
        elif isinstance(focused_option, AppVolume):
            self.renderer.set_active_option(focused_option)
            if self.renderer.active_option.session.Process:
                sav = self.renderer.active_option.session.SimpleAudioVolume
                self.renderer.current_volume = sav.GetMasterVolume()
            self.renderer.volume_animated = 1
        elif isinstance(focused_option, Menu):
            self.menu_stack.append((self.current_menu, self.renderer.focused_index))
            self.current_menu = focused_option
            self.renderer.focused_index = 0

            if focused_option.name == "Theme":
                focused_index = focused_option.indexof(self.settings.get_showing_theme().name)
                self.renderer.set_focused_index(focused_index)

            self._set_focus_target()
        elif isinstance(focused_option, Theme):
            self.change_theme(focused_option)
            self.current_menu, focused_index = self.menu_stack.pop()
            self.renderer.set_focused_index(focused_index)
            self._set_focus_target()

    def control_up_safe(self):
        """
        Volume up button press handler (or volume knob turning clockwise, or whatever).
        Typical action in scroll mode: scrolls "clockwise"
        Typical action in default mode: controls user pointer, moving it clockwise
        """
        if self.scroll_mode:
            self.scroll(self.scroll_direction, "clockwise")
            return
        if not self.menu_visible:
            keyboard.send(-175)
            return

        self.renderer.set_turn("right")

        self.inactivity_timer.start()
        if self.renderer.active_option is None:
            focused_index = (self.renderer.focused_index - 1) % len(self.current_menu.items)
            self.renderer.set_focused_index(focused_index)
            self._set_focus_target()
        else:
            self.adjust_volume(self.renderer.active_option, self.get_volume_delta(0.01))

    def control_down_safe(self):
        """
        Volume down button press handler (or volume knob turning counterclockwise, or whatever).
        Typical action in scroll mode: scrolls "anticlockwise"
        Typical action in default mode: controls user pointer, moving it counterclockwise
        """
        if self.scroll_mode:
            self.scroll(self.scroll_direction, "anticlockwise")
            return
        if not self.menu_visible:
            keyboard.send(-174)
            return

        self.renderer.set_turn("left")

        self.inactivity_timer.start()
        if self.renderer.active_option is None:
            focused_index = (self.renderer.focused_index + 1) % len(self.current_menu.items)
            self.renderer.set_focused_index(focused_index)
            self._set_focus_target()
        else:
            self.adjust_volume(self.renderer.active_option, -self.get_volume_delta(0.01))

    def control_double_click_safe(self):
        """
        Custom control double click handler.
        Still unused.
        """
        return

    def control_hold_safe(self):
        """
        Custom control double click handler (not implemented for keyboard controls yet).
        Changes application mode from default to scroll mode and vice versa. 
        """
        self.scroll_mode = not self.scroll_mode


    def control_click(self):
        """
        Actual mute button press handler (or volume knob press, or whatever).
        Due to the specifics of PyQt, control_click_safe cannot be called directly.
        """
        QTimer.singleShot(0, self.control_click_safe)

    def control_up(self):
        """
        Actual volume up press handler (or volume knob turning clockwise, or whatever).
        Due to the specifics of PyQt, control_up_safe cannot be called directly.
        """
        QTimer.singleShot(0, self.control_up_safe)

    def control_down(self):
        """
        Actual volume down press handler (or volume knob turning counterclockwise, or whatever).
        Due to the specifics of PyQt, control_down_safe cannot be called directly.
        """
        QTimer.singleShot(0, self.control_down_safe)

    def control_double_click(self):
        """
        Actual custom control double click handler.
        Due to the specifics of PyQt, control_double_click_safe cannot be called directly.
        """
        QTimer.singleShot(0, self.control_double_click_safe)

    def control_hold(self):
        """
        Actual custom control double click handler (not implemented for keyboard controls yet).
        Due to the specifics of PyQt, control_hold_safe cannot be called directly.
        """
        QTimer.singleShot(0, self.control_hold_safe)

    def resource_path(self, relative_path):
        """
        Loads resources from internal storage.
        Used in pre-built version of Remixer
        Parameters:
            relative_path (str): Path to resource.
        """
        try:
            base_path = sys._MEIPASS   # pylint: disable=protected-access disable=no-member   # Reason: Used to load resources in pre-built version of Remixer
        except Exception:              # pylint: disable=broad-exception-caught               # Reason: Intercepts any errors, no action required
            base_path = os.path.abspath(".")
        relative_path = relative_path.replace("./", "").replace("/","\\")

        return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app_ = QApplication(sys.argv)
    window = DrawingWindow(app_)
    window.show()

    with open('./settings.json', 'r', encoding='utf-8') as file_:
        settings_ = json.load(file_)
        if "SerialCOM" in settings_ and "SerialBaud" in settings_:
            SerialDevice.set_com(
                                settings_["SerialCOM"],
                                SerialDevice.baud_from_int(settings_["SerialBaud"])
            )
            SerialDevice.add_event(
                                SerialDevice.RotaryEncoder.EncoderEvents.ANTICLOCKWISE,
                                window.control_down
            )
            SerialDevice.add_event(
                                SerialDevice.RotaryEncoder.EncoderEvents.CLOCKWISE,
                                window.control_up
            )
            SerialDevice.add_event(
                                SerialDevice.RotaryEncoder.ButtonEvents.CLICK,
                                window.control_click
            )
            SerialDevice.add_event(SerialDevice.RotaryEncoder.ButtonEvents.DOUBLE_CLICK,
                                   window.control_double_click
            )
            SerialDevice.add_event(SerialDevice.RotaryEncoder.ButtonEvents.LONG_CLICK,
                                   window.control_hold
            )

    keyboard.add_hotkey(-175, window.control_up, suppress=True)
    keyboard.add_hotkey(-174, window.control_down, suppress=True)
    keyboard.add_hotkey(-173, window.control_click, suppress=True)

    sys.exit(app_.exec())
