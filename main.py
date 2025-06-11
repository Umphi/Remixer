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
import psutil
import win32gui
import win32ui

from PIL import Image
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPixmap, QIcon, QAction
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, QSize
from pycaw.pycaw import AudioUtilities

from classes.menu import Menu, Placeholder, Button, AppVolume
from classes.remixer_theme import RemixerTheme as Theme
from classes.scroller import AdaptiveTouchScroller as Scroller
from classes.serial_port import SerialDevice


class DrawingWindow(QMainWindow):
    """
    DrawingWindow ... speaks for itself
    """
    def __init__(self, app):
        super().__init__()

        self.refresh_rate = 165

        self.init_ui()
        self.init_timers()

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

        self.scroller = Scroller(step_pixels=300,
                                 tick_rate_hz=self.refresh_rate,
                                 base_decay_rate=0.5,
                                 speed_min=1.0,
                                 speed_max=50.0,
                                 fps_min=7.5,
                                 fps_max=50.0
                                 )

        self.aliases = {}
        self.ignore = {}
        self.icons = {}
        self.colored_icons = {}
        self.sessions = []
        self.themes = {}

        self.opacity_multiplier = 1

        self.current_volume = 1
        self.active_option = None
        self.menu_visible = False
        self.focused_index = 0

        self.focus_pie_angle = 0
        self.focus_pie_target = 0
        self.focus_pie_span = 0
        self.focus_pie_target_span = 0
        self.volume_animated = 1
        self.last_turn = None

        self.selected_theme = None
        self.theme = None

        self.current_menu = {}
        self.menu_stack = []
        self.menu_keys = []

        self.scroll_mode = False
        self.scroll_direction = "vertical"

        self.load_settings()
        self.reload_apps()
        self.load_colored_icons()

    def init_ui(self):
        """
        Initialize UI.
        """
        self.screen_size = QSize(330, 330)
        screen = self.screen_size
        self.setGeometry(30, 1025, screen.width(), screen.height())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)

        self.pen_width = 4
        self.pen_color = QColor(255, 0, 0)

        self.opacity_multiplier = 1

    def init_timers(self):
        """
        Starts timer for UI refresh, inactivity timer and UI fade timer
        """
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_step)
        self.fade_timer.setInterval(math.floor(1000/self.refresh_rate))

        self.draw_timer = QTimer(self)
        self.draw_timer.timeout.connect(self.updatescreen)
        self.draw_timer.start(math.floor(1000/self.refresh_rate))

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(3000)
        self.inactivity_timer.timeout.connect(self.hide_menu)

    def updatescreen(self):
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

        theme = self.selected_theme

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        center = QPoint(self.screen_size.width()//2, self.screen_size.height()//2)
        radius = 150
        sectors = len(self.current_menu.items)

        for i, label in enumerate(self.current_menu.items):
            self.draw_sector(painter, center, radius, sectors, i, label)

        focus_angle_1 = (self.focus_pie_target-self.focus_pie_angle)%360

        distance_between_angles = 360 - focus_angle_1 if focus_angle_1 > 180 else focus_angle_1

        typical_far_angle = 80

        speed_multiplier = 1

        if distance_between_angles > typical_far_angle:
            diff_coef = (1 - (180-distance_between_angles)/(180-typical_far_angle))
            speed_multiplier = (theme.focused_sector.animation_multiplier - 1) * diff_coef + 1

        speed = 0
        if focus_angle_1 != 0:
            speed = theme.focused_sector.animation_speed*speed_multiplier

            if self.last_turn is None:
                if focus_angle_1 > 180:
                    speed = (speed if (360 - focus_angle_1) > speed else 360-focus_angle_1)
                    self.focus_pie_angle -= speed
                elif focus_angle_1 <= 180:
                    speed = (speed if focus_angle_1 > speed else focus_angle_1)
                    self.focus_pie_angle += speed
            else:
                if focus_angle_1 <= speed:
                    self.focus_pie_angle = self.focus_pie_target
                else:
                    if self.last_turn == "right":
                        self.focus_pie_angle -= speed
                    elif self.last_turn == "left":
                        self.focus_pie_angle += speed
            if self.focus_pie_angle >= 360:
                self.focus_pie_angle -= 360
            if self.focus_pie_angle < 0:
                self.focus_pie_angle = 360 + self.focus_pie_angle

        span_difference = math.fabs(self.focus_pie_span-self.focus_pie_target_span)
        ease_out_mp = 1/((min(span_difference/16,25)/25)*(theme.volume_arc.ease_out_speed*0.2-1)+1)
        span_changing = 16*theme.volume_arc.animation_speed*speed_multiplier*ease_out_mp

        if span_difference > span_changing:
            span_changing_speed = span_changing
        else:
            span_changing_speed = math.fabs(self.focus_pie_span-self.focus_pie_target_span)

        if focus_angle_1 != 0 and speed * 2 > span_changing_speed:
            span_changing_speed = speed * 2

        if self.focus_pie_span < self.focus_pie_target_span:
            self.focus_pie_span += span_changing_speed
        elif self.focus_pie_span > self.focus_pie_target_span:
            self.focus_pie_span -= span_changing_speed

        self.draw_focus(painter, center, radius, sectors, self.focus_pie_angle, speed)

        for i, label in enumerate(self.current_menu.items):
            if isinstance(label, Theme):
                continue
            self.draw_all_icons(painter, center, radius, sectors, i, label)

        self.draw_center_label(painter, center)


    def draw_sector(self, painter, center, radius, sectors, i, label):
        """
        Draws menu sector (pie).

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of imaginary circle that will be cut for pies.
            radius (int): Radius of imaginary circle in pixels.
            sectors (int): Count of items in current menu.
            i (int): Index of active menu item.
            label (MenuItem): Menu Item with specific parameters of drawing.
        """
        if not self.menu_visible:
            return

        angle = 360 / sectors
        start_angle = (i * angle - 90) * 16
        span_angle = angle * 16

        is_focused = i == self.focused_index
        brush_color = self.selected_theme.sector.fill.to_QColor(self.opacity_multiplier)
        pen_color = self.selected_theme.sector.outline.to_QColor(self.opacity_multiplier)

        painter.setPen(pen_color)
        painter.setBrush(brush_color)

        painter.drawPie(
                        int(center.x() - radius),
                        int(center.y() - radius),
                        int(radius * 2),
                        int(radius * 2),
                        int(start_angle),
                        int(span_angle)
                        )

        if is_focused:
            if isinstance(label, Theme):
                self.selected_theme = label

    def draw_focus(self, painter, center, radius, sectors, f_angle, speed = 0):
        """
        Draws user pointer sector (pie).

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of imaginary circle that will be cut for pies.
            radius (int): Radius of imaginary circle in pixels.
            sectors (int): Count of items in current menu.
            f_angle (int): Angle on the circle that pointer should point.
            speed (float): Used to remove outline when pointer moving fast to prevent flickering.
        """
        if not self.menu_visible:
            return

        angle = 360 / sectors
        span_angle = angle * 16
        start_angle = f_angle*16 - 0.5*self.focus_pie_span

        brush_color = self.selected_theme.focused_sector.fill.to_QColor(self.opacity_multiplier)
        pen_color = self.selected_theme.focused_sector.outline.to_QColor(self.opacity_multiplier)
        if speed > 2:
            pen_color = self.selected_theme.focused_sector.fill.to_QColor(self.opacity_multiplier)

        painter.setPen(pen_color)
        painter.setBrush(brush_color)

        draw_radius = radius * 1.1
        draw_size = int(draw_radius * 2)

        self.focus_pie_target_span = span_angle

        painter.drawPie(
                        int(center.x() - draw_radius),
                        int(center.y() - draw_radius),
                        draw_size,
                        draw_size,
                        int(start_angle),
                        int(self.focus_pie_span)
        )

        label = self.current_menu.items[self.focused_index]
        self.draw_volume_arc(painter, center, radius, start_angle, span_angle, sectors, label)

    def draw_all_icons(self, painter, center, radius, sectors, i, label):
        """
        Calculates icon drawing position and size depending
        on the position relative to user pointer.
        Then pass parameters to draw_icon(...)

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of application window.
            radius (int): Radius of imaginary circle in pixels.
            sectors (int): Count of items in current menu.
            i (int): Index of menu element.
            label (MenuItem): Menu Item with specified parameters of drawing.
        """
        if not self.menu_visible:
            return

        current_angle = i * 360 / sectors - 90 + (360 / sectors) / 2
        focused_angle = self.focus_pie_angle

        max_icon_multiplier = self.selected_theme.icons.max_scaling
        min_icon_multiplier = self.selected_theme.icons.min_scaling

        focus_angle_1 = (focused_angle-current_angle)%360
        if focus_angle_1 > 180:
            focus_angle_1 = 360 - focus_angle_1

        max_to_min_mtp_diff = max_icon_multiplier-min_icon_multiplier
        scaling_mtp = min((focus_angle_1/self.selected_theme.icons.scaling_angle),1)

        multiplier = max_icon_multiplier
        multiplier -= max_to_min_mtp_diff*scaling_mtp
        self.draw_icon(painter, label, center, radius, i, sectors, multiplier)

    def draw_icon(self, painter, label, center, radius, i, sectors, size_multiplier=1):
        """
        Draws icon with given by draw_all_icons parameters.

        Parameters:
            painter (QPainter): Used PyQt painter.
            label (MenuItem): Menu Item with specified parameters of drawing.
            center (QPoint): Position of center of application window.
            radius (int): Radius of imaginary circle in pixels.
            i (int): Index of menu element.
            sectors (int): Count of items in current menu.
            size_multiplier (float): Image size multiplier.
        """
        if not self.menu_visible:
            return

        icon = self.icons.get(label.icon)
        if f"{label.icon}_Colorable" in self.icons:
            if label.icon in self.colored_icons:
                icon = self.colored_icons.get(label.icon)

        if not icon:
            icon = self.colored_icons.get("Unknown")

        icon_size = int(size_multiplier*32)
        angle_rad = math.radians(i * 360 / sectors - 90 + (360 / sectors) / 2)
        x = center.x() + math.cos(angle_rad) * (radius * 0.7) - icon_size // 2
        y = center.y() - math.sin(angle_rad) * (radius * 0.7) - icon_size // 2
        painter.setOpacity(self.opacity_multiplier)
        painter.drawPixmap(int(x), int(y), icon_size, icon_size, icon)

    def draw_volume_arc(self, painter, center, radius, start_angle, span_angle, sectors, label):
        """
        Draws arc around menu used as current volume slider indicator.
        Actually draws 2 arcs, one above another, to create outline/shadow.

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of application window.
            radius (int): Radius of imaginary circle in pixels.
            start_angle (int): Start angle of arc.
            span_angle (int): Span angle of arc.
            sectors (int): Count of items in current menu.
            label (MenuItem): Menu Item with specified parameters of drawing.
        """

        theme = self.selected_theme
        arc_speed = theme.volume_arc.animation_speed
        if not self.menu_visible:
            return

        item = self.current_menu.index(label)

        if self.active_option:
            if isinstance(item, AppVolume):
                if item.session.Process:
                    self.current_volume = item.session.SimpleAudioVolume.GetMasterVolume()

            volume_difference = math.fabs(self.volume_animated - self.current_volume)
            ease_activation_difference = 0.3
            ease_out_multiplier = 1
            if volume_difference < ease_activation_difference:
                ease_out_multiplier = 1-volume_difference/ease_activation_difference
                ease_out_multiplier = 1/(ease_out_multiplier*(theme.volume_arc.ease_out_speed-1)+1)

            vol_delta = 0.01*arc_speed*ease_out_multiplier
            if self.volume_animated < self.current_volume:
                self.volume_animated = min(self.current_volume, self.volume_animated+vol_delta)
            elif self.volume_animated > self.current_volume:
                self.volume_animated = max(self.current_volume, self.volume_animated-vol_delta)
        else:
            self.current_volume = 1
            self.volume_animated = min(self.current_volume, self.volume_animated+0.01*arc_speed)

        arc_rect = QRectF(
            center.x() - radius * 1.1 + radius * 0.05,
            center.y() - radius * 1.1 + radius * 0.05,
            radius * 2.2 - radius * 0.1,
            radius * 2.2 - radius * 0.1
        )

        span_diff = self.focus_pie_span-span_angle
        span_angle = self.focus_pie_span

        painter.setPen(
                    QPen(
                        theme.volume_arc.background.to_QColor(self.opacity_multiplier),
                        int(radius * 0.1),
                        cap=Qt.PenCapStyle.FlatCap
                    )
        )
        painter.drawArc(
                        arc_rect,
                        int(start_angle + span_angle),
                        int((360 - 360/sectors) * 16-span_diff)
        )

        painter.setPen(
                    QPen(
                        theme.volume_arc.foreground.to_QColor(self.opacity_multiplier),
                        int(radius * 0.1),
                        cap=Qt.PenCapStyle.FlatCap
                    )
        )
        full_wo_one = 360 - 360/sectors
        diff = full_wo_one - full_wo_one * self.volume_animated
        start = int(start_angle + span_angle + (diff) * 16)
        painter.drawArc(arc_rect, start, int(full_wo_one * self.volume_animated * 16-span_diff))

    def draw_center_label(self, painter, center):
        """
        Draws circle with information in the center of application menu

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of application window.
            label (MenuItem): Menu Item with specified parameters of drawing.
        """
        theme = self.selected_theme

        if not self.menu_visible:
            return

        label = self.current_menu.items[self.focused_index]
        text = label.name

        volume = 0
        mute = 0

        if isinstance(label, AppVolume):
            if label.session.Process:
                volume = label.session.SimpleAudioVolume.GetMasterVolume()

        font = QFont('Helvetica', 10, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        ha = fm.horizontalAdvance(text)

        painter.setBrush(theme.center_circle.fill.to_QColor(self.opacity_multiplier))
        painter.setPen(theme.center_circle.outline.to_QColor(self.opacity_multiplier))
        center_size = int(theme.center_circle.size_multiplier * 120)
        painter.drawEllipse(
                            center.x() - center_size//2,
                            center.y() - center_size//2,
                            center_size,
                            center_size
        )

        painter.setFont(font)
        painter.setPen(theme.center_circle.text_color.to_QColor(self.opacity_multiplier))

        if isinstance(label, Placeholder):
            text = label.text
            line_height = fm.height()
            line_space = 3
            lines = text.split("\n")
            #full_height = len(lines)*line_height+(len(lines)-1)*3
            for i, line in enumerate(lines):
                ha = fm.horizontalAdvance(line)
                painter.drawText(
                                center.x() - ha // 2,
                                center.y() + i * (line_height + line_space) + 7,
                                line
                )
        else:
            painter.drawText(center.x() - ha // 2, center.y() + 6, text)

        volume = round(volume*100)
        if volume <= 0:
            if isinstance(label, AppVolume) and self.selected_theme.show_zero_volume:
                volume = "Mute"
            else:
                volume = ""
        else:
            volume = f"{volume}%"

        if mute == 1:
            volume = "Mute"

        hav = fm.horizontalAdvance(volume)
        painter.setPen(theme.center_circle.volume_text_color.to_QColor(self.opacity_multiplier))
        painter.drawText(center.x() - hav // 2, center.y() + 35, volume)


    def reload_apps(self):
        """
        Reloads menu with updating available applications producing sound.
        """
        if self.menu_visible:
            return

        self.sessions = AudioUtilities.GetAllSessions()

        pids = {}

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

        for theme in self.themes:
            current_menu.index("Settings").index("Theme").add_item(theme)

        for session in self.sessions:
            if session.Process:
                name = session.Process.name()
                if name in self.ignore:
                    continue
                alias = self.aliases.get(name, name.replace(".exe", ""))
                current_menu.add_item(AppVolume(alias, name, session, filename_ = name))
                pids[name] = session.Process.pid

        self.current_menu = current_menu
        self.menu_stack = []

        self.load_icons(pids)

    def fade_step(self):
        """
        Counts opacity for smooth menu disappearing.
        """
        self.opacity_multiplier -= self.theme.fade_out_speed
        if self.opacity_multiplier <= 0:
            self.fade_timer.stop()
            self.menu_visible = False
            self.active_option = None
            self.opacity_multiplier = 1
            self.last_turn = None

            self.selected_theme = self.theme

            self.current_volume = 1
            self.volume_animated = 1

            if len(self.menu_stack) > 0:
                self.menu_stack.reverse()
                self.current_menu, self.focused_index = self.menu_stack.pop()
                self.menu_stack.clear()
                self.focus_pie_target_span = 360*16/len(self.current_menu.items)
                self.focus_pie_span = self.focus_pie_target_span
        self.update()

    def show_menu(self):
        """
        Shows circular menu (application)
        """
        self.reload_apps()
        self.menu_visible = True
        self.focused_index = 0
        self.set_focus_target(True)
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
            self.current_volume = new_volume

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
        Activates chosen theme and writes it in config.

        Parameters:
            Theme (Theme): Theme to activate.
        """
        self.theme = theme
        self.selected_theme = self.theme
        self.load_colored_icons()
        settings = {}
        with open('settings.json', 'r', encoding='utf-8') as file:
            settings = json.load(file)
            settings["SelectedTheme"] = theme.name
        with open('settings.json', 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)

    def menu_back(self):
        """
        Returns to parent menu.
        """
        self.current_menu, self.focused_index = self.menu_stack.pop()
        self.focus_pie_target_span = 360*16/len(self.current_menu.items)
        self.last_turn = None
        self.set_focus_target()

    def set_focus_target(self, set_current=False):
        """
        Sets user pointer target angle(for animated shifting)

        Parameters:
            set_current (bool): Forces user pointer to change position instantly without animation.
        """
        angle = 360 / len(self.current_menu.items)
        start_angle = (self.focused_index * angle - 90) * 16
        span_angle = angle * 16
        self.focus_pie_target = int((start_angle+span_angle/2)/16)

        if self.focus_pie_target < 0:
            self.focus_pie_target = 360 + self.focus_pie_target
        if set_current:
            self.focus_pie_angle = self.focus_pie_target


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

        self.last_turn = None

        focused_option = self.current_menu.items[self.focused_index]
        self.inactivity_timer.start()

        if self.active_option:
            self.active_option = None
            return

        if isinstance(focused_option, Button):
            focused_option.action()
        elif isinstance(focused_option, AppVolume):
            self.active_option = focused_option
            self.current_volume = 1
            if self.active_option.session.Process:
                sav = self.active_option.session.SimpleAudioVolume
                self.current_volume = sav.GetMasterVolume()
            self.volume_animated = 1
        elif isinstance(focused_option, Menu):
            self.menu_stack.append((self.current_menu, self.focused_index))
            self.current_menu = focused_option
            self.focused_index = 0

            if focused_option.name == "Theme":
                self.focused_index = focused_option.indexof(self.theme.name)

            self.set_focus_target()
        elif isinstance(focused_option, Theme):
            self.change_theme(focused_option)
            self.current_menu, self.focused_index = self.menu_stack.pop()
            self.set_focus_target()

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

        self.last_turn = "right"

        self.inactivity_timer.start()
        if self.active_option is None:
            self.focused_index = (self.focused_index - 1) % len(self.current_menu.items)
            self.set_focus_target()
        else:
            self.adjust_volume(self.active_option, self.get_volume_delta(0.01))

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

        self.last_turn = "left"

        self.inactivity_timer.start()
        if self.active_option is None:
            self.focused_index = (self.focused_index + 1) % len(self.current_menu.items)
            self.set_focus_target()
        else:
            self.adjust_volume(self.active_option, -self.get_volume_delta(0.01))

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


    def load_settings(self):
        """
        Loads and processes settings and themes on program startup.
        """
        try:
            theme = ""
            with open('./settings.json', 'r', encoding='utf-8') as file:
                settings = json.load(file)
                self.aliases = settings["Aliases"]
                self.ignore = settings["IgnoreProcesses"]
                self.image_replacements = settings["ImageReplacements"]

                theme = settings["SelectedTheme"]
            with open('./themes.json', 'r', encoding='utf-8') as file:
                themes_json = json.load(file)
                themes = []
                for theme_config in themes_json:
                    if Theme.exists(theme_config):
                        Theme.find_by_name(theme_config).reset_config(themes_json.get(theme))
                    else:
                        themes.append(Theme(themes_json.get(theme_config), self.refresh_rate))
                self.themes = themes
                self.theme = Theme.find_by_name(theme)
                self.selected_theme = self.theme
                self.inactivity_timer.setInterval(self.theme.fade_out_timeout)
        except FileNotFoundError:
            pass

    def load_icons(self, pids):
        """
        Loads icons in memory for applications with specified pids.
        Parameters:
            pids (dict): Dictionary with PIDs of applications providing volume controls.
        """
        os.makedirs("./icons", exist_ok=True)
        for proc, pid in pids.items():
            if not os.path.exists(f"./icons/{proc}.png"):
                if proc in self.image_replacements:
                    for procutil in psutil.process_iter():
                        if procutil.name() == self.image_replacements[proc]:
                            self.extract_icon(psutil.Process(procutil.pid).exe(), proc)
                else:
                    self.extract_icon(psutil.Process(pid).exe(), proc)

        for file in os.listdir("./icons"):
            name = file.replace(".png", "")
            if name not in self.icons:
                self.icons[name] = QPixmap(f"./icons/{file}")
        if os.path.exists("./icons/internal"):
            for file in os.listdir("./icons/internal"):
                name = file.replace(".png", "")
                if name not in self.icons:
                    self.icons[name] = QPixmap(f"./icons/internal/{file}")
        for file in os.listdir(self.resource_path("./icons/internal")):
            name = file.replace(".png", "")
            if name not in self.icons:
                self.icons[name] = QPixmap(self.resource_path(f"./icons/internal/{file}"))

    def load_colored_icons(self):
        """
        Loads available (usually, only internal) icons with specified in theme color.
        """
        for file in os.listdir(self.resource_path("./icons/internal")):
            name = file.replace(".png", "")
            if name.endswith("_Colorable"):
                image = Image.open(self.resource_path(f"./icons/internal/{file}"))
                image_pixels = image.load()

                image_colored = Image.new(image.mode, image.size)
                colored_pixels = image_colored.load()

                for i in range(image_colored.size[0]):
                    for j in range(image_colored.size[1]):
                        colored_pixels[i,j] = (
                                                self.selected_theme.preferred_icon_color.r,
                                                self.selected_theme.preferred_icon_color.g,
                                                self.selected_theme.preferred_icon_color.b,
                                                image_pixels[i,j][3]
                        )

                self.colored_icons[name.replace("_Colorable", "")] = image_colored.toqpixmap()
                image.close()
                image_colored.close()

        if os.path.exists("./icons/internal"):
            for file in os.listdir("./icons/internal"):
                name = file.replace(".png", "")
                if name.endswith("_Colorable"):
                    image = Image.open(f"./icons/internal/{file}")
                    image_pixels = image.load()

                    image_colored = Image.new(image.mode, image.size)
                    colored_pixels = image_colored.load()

                    for i in range(image_colored.size[0]):
                        for j in range(image_colored.size[1]):
                            colored_pixels[i,j] = (
                                                self.selected_theme.preferred_icon_color.r,
                                                self.selected_theme.preferred_icon_color.g,
                                                self.selected_theme.preferred_icon_color.b,
                                                image_pixels[i,j][3]
                            )

                    self.colored_icons[name.replace("_Colorable", "")] = image_colored.toqpixmap()
                    image.close()
                    image_colored.close()

    def extract_icon(self, path, name):
        """
        Extract icon from Windows application and creates compatible icon.
        Parameters:
            path (str): Path to application directory.
            name (str): Windows Executable name.
        """
        path = path.replace("\\", "/")

        large, small = win32gui.ExtractIconEx(path, 0)
        if not large:
            return
        if small is not None:
            win32gui.DestroyIcon(small[0])

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), large[0])

        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (32, 32), bmpstr, 'raw', 'BGRA', 0, 1)
        img.save(f'./icons/{name}.png')

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
