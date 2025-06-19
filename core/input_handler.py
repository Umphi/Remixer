""" Handles input commands from user """
import time

import keyboard
from core.menu import ThemeItem, AppVolume, Button, Menu

class InputHandler():
    """ Handles input commands from user """
    def __init__(self, parent):
        self.window = parent
        self.renderer = self.window.renderer
        self.menu_manager = self.window.menu_manager

        self.scroll_mode = False
        self.scroll_direction = "vertical"

        self.last_volume_adjust_time = 0
        self.volume_adjust_rate = 1

    def control_click(self):
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

        if not self.window.menu_visible:
            self.window.show_menu()
            return

        focused = self.menu_manager.get_focus_item()
        self.window.start_inactivity_signal.emit()

        if self.renderer.active_option:
            self.renderer.set_active_option(None)
            return

        if isinstance(focused, Button):
            focused.action()
        elif isinstance(focused, AppVolume):
            self.renderer.set_active_option(focused)
            if self.renderer.active_option.session.Process:
                sav = self.renderer.active_option.session.SimpleAudioVolume
                self.renderer.current_volume = sav.GetMasterVolume()
            self.renderer.volume_animated = 1
        elif isinstance(focused, Menu):
            self.menu_manager.menu_enter(focused)
            current_theme = self.window.settings.get_showing_theme().name
            self.menu_manager.set_focus_by_condition(
                lambda item:
                    isinstance(item, ThemeItem) and item.name == current_theme
            )

    def control_up(self):
        """
        Volume up button press handler (or volume knob turning clockwise, or whatever).
        Typical action in scroll mode: scrolls "clockwise"
        Typical action in default mode: controls user pointer, moving it clockwise
        """
        if self.scroll_mode:
            self.scroll(self.scroll_direction, "clockwise")
            return
        if not self.window.menu_visible:
            keyboard.send(-175)
            return

        self.window.start_inactivity_signal.emit()
        if self.renderer.active_option is None:
            self.menu_manager.rotate(1)
        else:
            self.adjust_volume(self.renderer.active_option, self.get_volume_delta(0.01))

    def control_down(self):
        """
        Volume down button press handler (or volume knob turning counterclockwise, or whatever).
        Typical action in scroll mode: scrolls "anticlockwise"
        Typical action in default mode: controls user pointer, moving it counterclockwise
        """
        if self.scroll_mode:
            self.scroll(self.scroll_direction, "anticlockwise")
            return
        if not self.window.menu_visible:
            keyboard.send(-174)
            return

        self.window.start_inactivity_signal.emit()
        if self.renderer.active_option is None:
            self.menu_manager.rotate(-1)
        else:
            self.adjust_volume(self.renderer.active_option, -self.get_volume_delta(0.01))

    def control_double_click(self):
        """
        Custom control double click handler.
        Still unused.
        """
        return

    def control_hold(self):
        """
        Custom control double click handler (not implemented for keyboard controls yet).
        Changes application mode from default to scroll mode and vice versa. 
        """
        self.scroll_mode = not self.scroll_mode

    def adjust_volume(self, option, delta):
        """
        Main function to change application volume.

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

    def scroll(self, scroll_direction, _direction):
        """
        Handles scroll action in scroll_mode (only with custom controls).

        Parameters:
            scroll_direction (str): "horizontal" or "vertical" scrolling.
            _direction (str): "clockwise" or "anticlockwise".
        """
        if scroll_direction == "horizontal":
            self.window.scroller.scroll_pixels_horizontal(10 if _direction == "clockwise" else -10)
        else:
            self.window.scroller.scroll_pixels(10 if _direction == "clockwise" else -10)
