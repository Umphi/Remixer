# pylint: disable=too-many-locals,too-many-instance-attributes,too-many-arguments,too-many-positional-arguments,too-many-branches # WIP
"""
Application renderer
"""
import math
from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QPen, QFont, QFontMetrics
from core.menu import AppVolume, Placeholder
from core.menu_manager import MenuObserver

class Renderer(MenuObserver):
    """
    Class that draws application
    """
    focus_pie_angle = 0
    focus_pie_target = 0
    focus_pie_span = 0
    focus_pie_target_span = 0
    last_turn = None
    volume_animated = 1
    focused_index = 0
    opacity_multiplier = 1
    menu = None
    active_option = None
    current_volume = 1

    def __init__(self, screen_size, settings):
        self.screen_size = screen_size
        self.settings = settings

    def on_focus_changed(self, index, last_turn):
        """
        Implemented by MenuObserver. Called when menu focus changes
        """
        self.focused_index = index
        self.last_turn = last_turn
        self.set_angles()

    def on_menu_changed(self, menu):
        """
        Implemented by MenuObserver. Called when active menu changes
        """
        self.menu = menu
        self.set_angles()

    def set_angles(self, set_current = False):
        """
        Sets user pointer target angle(for animated shifting)

        Parameters:
            set_current (bool): Forces user pointer to change position instantly without animation.
        """
        angle = 360 / len(self.menu)
        start_angle = (self.focused_index * angle - 90) * 16
        span_angle = angle * 16
        self.focus_pie_target = int((start_angle+span_angle/2)/16)

        if self.focus_pie_target < 0:
            self.focus_pie_target = 360 + self.focus_pie_target
        if set_current:
            self.focus_pie_angle = self.focus_pie_target

    def set_active_option(self, option):
        """
        Sets active menu option flag
        """
        self.active_option = option

    def update_apps(self):
        """
        Function used to load icons where new application were open
        """
        self.settings.icon_manager.load_icons(AppVolume.get_pid_dict())
        self.settings.icon_manager.load_colored_icons()

    def draw(self, painter, theme):
        """
        Main draw function. Processes menu parameters and calls elements' drawing functions
        """
        if self.menu is None or len(self.menu) <= 0:
            return

        center = QPoint(self.screen_size.width()//2, self.screen_size.height()//2)
        radius = 150
        sectors = len(self.menu)

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

        for i, label in enumerate(self.menu):
            self.draw_sector(painter, theme, center, radius, sectors, i)

        self.draw_focus(painter, theme, center, radius, sectors, self.focus_pie_angle, speed)

        for i, label in enumerate(self.menu):
            self.draw_all_icons(painter, theme, center, radius, sectors, i, label)

        self.draw_center_label(painter, theme, center)


    def draw_sector(self, painter, theme, center, radius, sectors, i):
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
        angle = 360 / sectors
        start_angle = (i * angle - 90) * 16
        span_angle = angle * 16

        brush_color = theme.sector.fill.to_QColor(self.opacity_multiplier)
        pen_color = theme.sector.outline.to_QColor(self.opacity_multiplier)

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

    def draw_focus(self, painter, theme, center, radius, sectors, f_angle, speed = 0):
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
        angle = 360 / sectors
        span_angle = angle * 16
        start_angle = f_angle*16 - 0.5*self.focus_pie_span

        brush_color = theme.focused_sector.fill.to_QColor(self.opacity_multiplier)
        pen_color = theme.focused_sector.outline.to_QColor(self.opacity_multiplier)
        if speed > 2:
            pen_color = theme.focused_sector.fill.to_QColor(self.opacity_multiplier)

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

        label = self.menu[self.focused_index]
        self.draw_volume_arc(painter,
                            theme,
                            center,
                            radius,
                            start_angle,
                            span_angle,
                            sectors,
                            label
        )

    def draw_all_icons(self, painter, theme, center, radius, sectors, i, label):
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
        current_angle = i * 360 / sectors - 90 + (360 / sectors) / 2
        focused_angle = self.focus_pie_angle

        max_icon_multiplier = theme.icons.max_scaling
        min_icon_multiplier = theme.icons.min_scaling

        focus_angle_1 = (focused_angle-current_angle)%360
        if focus_angle_1 > 180:
            focus_angle_1 = 360 - focus_angle_1

        max_to_min_mtp_diff = max_icon_multiplier-min_icon_multiplier
        scaling_mtp = min((focus_angle_1/theme.icons.scaling_angle),1)

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
        icon = self.settings.icon_manager.icons.get(label.icon)
        #if f"{label.icon}_Colorable" in self.icon_manager.icons:
        if label.icon in self.settings.icon_manager.colored_icons:
            icon = self.settings.icon_manager.colored_icons.get(label.icon)

        if not icon:
            icon = self.settings.icon_manager.colored_icons.get("Unknown")

        icon_size = int(size_multiplier*32)
        angle_rad = math.radians(i * 360 / sectors - 90 + (360 / sectors) / 2)
        x = center.x() + math.cos(angle_rad) * (radius * 0.7) - icon_size // 2
        y = center.y() - math.sin(angle_rad) * (radius * 0.7) - icon_size // 2
        painter.setOpacity(self.opacity_multiplier)
        painter.drawPixmap(int(x), int(y), icon_size, icon_size, icon)

    def draw_volume_arc(self, painter, theme, center, radius,
                        start_angle, span_angle, sectors, label):
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

        item = self.menu.index(label)

        self.update_current_volume(item)

        self.update_volume_animation(theme)

        arc_rect = QRectF(
            center.x() - radius * 1.1 + radius * 0.05,
            center.y() - radius * 1.1 + radius * 0.05,
            radius * 2.2 - radius * 0.1,
            radius * 2.2 - radius * 0.1
        )

        full_angle = 360 - 360 / sectors
        animated_span = full_angle * self.volume_animated
        span_diff = self.focus_pie_span - span_angle
        animated_start = int(start_angle + self.focus_pie_span + (full_angle - animated_span) * 16)

        self.draw_arc(
            painter, arc_rect,
            theme.volume_arc.background,
            radius * 0.1,
            int(start_angle + self.focus_pie_span),
            int(full_angle * 16 - span_diff)
        )

        self.draw_arc(
            painter, arc_rect,
            theme.volume_arc.foreground,
            radius * 0.1,
            animated_start,
            int(animated_span * 16 - span_diff)
        )

    def draw_center_label(self, painter, theme, center):
        """
        Draws circle with information in the center of application menu

        Parameters:
            painter (QPainter): Used PyQt painter.
            center (QPoint): Position of center of application window.
            label (MenuItem): Menu Item with specified parameters of drawing.
        """
        label = self.menu[self.focused_index]
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
            if isinstance(label, AppVolume) and theme.show_zero_volume:
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

    def draw_arc(self, painter, rect, color, thickness, start_angle, span_angle):
        """
        Draws volume and background arcs with given parameters
        """
        pen = QPen(
                    color.to_QColor(self.opacity_multiplier),
                    int(thickness),
                    c=Qt.PenCapStyle.FlatCap
        )
        painter.setPen(pen)
        painter.drawArc(rect, int(start_angle), int(span_angle))

    def update_current_volume(self, item):
        """
        Sets target volume arc position
        """
        if self.active_option and isinstance(item, AppVolume) and item.session.Process:
            self.current_volume = item.session.SimpleAudioVolume.GetMasterVolume()
        elif not self.active_option:
            self.current_volume = 1

    def update_volume_animation(self, theme):
        """
        Performs animation of volume arc
        """
        vol_delta = 0.01 * theme.volume_arc.animation_speed

        if self.active_option:
            volume_difference = math.fabs(self.volume_animated - self.current_volume)
            vol_delta *= self.compute_ease_out_multiplier(
                                                            volume_difference,
                                                            0.3,
                                                            theme.volume_arc.ease_out_speed
            )

        if self.volume_animated < self.current_volume:
            self.volume_animated = min(self.current_volume, self.volume_animated+vol_delta)
        elif self.volume_animated > self.current_volume:
            self.volume_animated = max(self.current_volume, self.volume_animated-vol_delta)

    @staticmethod
    def compute_ease_out_multiplier(diff, threshold, speed):
        """
        Computes ease out multiplier for volume arc with given parameters
        """
        if diff >= threshold:
            return 1.0
        ratio = diff / threshold
        return 1.0 / ((1 - ratio) * (speed - 1) + 1)
