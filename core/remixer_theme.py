# pylint: disable=too-few-public-methods # Aknowledged
"""
Theme processing
"""
import math
from collections import defaultdict
from PySide6.QtGui import QColor

class RemixerTheme(): # pylint: disable=too-many-instance-attributes # Aknowledged
    """
    Represents theme
    """
    name_index = defaultdict(list)

    def __init__(self, theme_prefs, refresh_rate):
        """
        Parameters:
        theme_prefs (dict): Theme parameters in json,
        refresh_rate (int): Application refresh rate, used to calculate fade out time
        """
        self.name = theme_prefs["name"]
        self.sector = Sector(Color.from_json(theme_prefs["sector_outline"]),
                             Color.from_json(theme_prefs["sector_fill"]))
        self.focused_sector = AnimatedSector(Color.from_json(theme_prefs["focused_sector_outline"]),
                                             Color.from_json(theme_prefs["focused_sector_fill"]),
                                             theme_prefs["animation_speed"],
                                             theme_prefs["animation_speed_max_multiplier"])
        self.volume_arc = VolumeArc(Color.from_json(theme_prefs["volume_arc_bg_fill"]),
                                    Color.from_json(theme_prefs["volume_arc_fill"]),
                                    theme_prefs["volume_arc_animation_speed_multiplier"],
                                    theme_prefs["volume_ease_out_multiplier"])
        self.center_circle = CenterCircle(Color.from_json(theme_prefs["center_outline"]),
                                          Color.from_json(theme_prefs["center_fill"]),
                                          Color.from_json(theme_prefs["center_text"]),
                                          Color.from_json(theme_prefs["center_text_volume"]),
                                          theme_prefs["center_size_multiplier"])
        self.preferred_icon_color = Color.from_json(theme_prefs["prefer_icon_color"])
        self.show_zero_volume = theme_prefs["show_zero_volume"]
        self.icons = IconAnimation(theme_prefs["icon_size_multiplier"],
                                   theme_prefs["focused_icon_size_multiplier"],
                                   theme_prefs["icon_full_resize_angle"])
        self.fade_out_timeout = theme_prefs["fade_out_timeout"]*1000
        self.fade_out_speed = (math.floor(1000/refresh_rate))/(theme_prefs["fade_out_time"]*1000)
        RemixerTheme.name_index[self.name].append(self)

    def reset_config(self, theme_prefs, refresh_rate):
        """
        Function to reload theme parameters

        Parameters:
        theme_prefs (dict): Theme parameters in json,
        refresh_rate (int): Application refresh rate, used to calculate fade out time
        """
        self.sector = Sector(Color.from_json(theme_prefs["sector_outline"]),
                             Color.from_json(theme_prefs["sector_fill"]))
        self.focused_sector = AnimatedSector(Color.from_json(theme_prefs["focused_sector_outline"]),
                                             Color.from_json(theme_prefs["focused_sector_fill"]),
                                             theme_prefs["animation_speed"],
                                             theme_prefs["animation_speed_max_multiplier"])
        self.volume_arc = VolumeArc(Color.from_json(theme_prefs["volume_arc_bg_fill"]),
                                    Color.from_json(theme_prefs["volume_arc_fill"]),
                                    theme_prefs["volume_arc_animation_speed_multiplier"],
                                    theme_prefs["volume_ease_out_multiplier"])
        self.center_circle = CenterCircle(Color.from_json(theme_prefs["center_outline"]),
                                          Color.from_json(theme_prefs["center_fill"]),
                                          Color.from_json(theme_prefs["center_text"]),
                                          Color.from_json(theme_prefs["center_text_volume"]),
                                          theme_prefs["center_size_multiplier"])
        self.preferred_icon_color = Color.from_json(theme_prefs["prefer_icon_color"])
        self.show_zero_volume = theme_prefs["show_zero_volume"]
        self.icons = IconAnimation(theme_prefs["icon_size_multiplier"],
                                   theme_prefs["focused_icon_size_multiplier"],
                                   theme_prefs["icon_full_resize_angle"])
        self.fade_out_timeout = theme_prefs["fade_out_timeout"]*1000
        self.fade_out_speed = (math.floor(1000/refresh_rate))/(theme_prefs["fade_out_time"]*1000)

    @classmethod
    def find_by_name(cls, name):
        """
        Finds first theme by name
        Parameters:
        name(str): Name to find
        """
        return RemixerTheme.name_index[name][0]

    @classmethod
    def find_all_by_name(cls, name):
        """
        Finds all themes by name
        Parameters:
        name(str): Name to find
        """
        return RemixerTheme.name_index[name]

    @classmethod
    def exists(cls, name):
        """
        Checks if there is loaded theme in application
        Parameters:
        name(str): Name to find
        """
        return name in cls.name_index

class Color():
    """
    Custom color class
    """
    def __init__(self, color_r = 0, color_g = 0, color_b = 0, opacity = None):
        self.r = color_r
        self.g = color_g
        self.b = color_b
        self.opacity = opacity

    def to_QColor(self, opacity_mtp = 1): # pylint: disable=invalid-name # Reason: I think this is appropriate name
        """
        Returns color as QColor with specified opacity multiplier
        Parameters:
        opacity_multiplier(int): opacity with that QColor will be returned
        """
        return QColor(self.r,
                      self.g,
                      self.b,
                      int(self.opacity*opacity_mtp if self.opacity else 255*opacity_mtp))

    @classmethod
    def from_json(cls, json_color):
        """
        Returns color as QColor from json_color
        Parameters:
        json_color(dict): {"R": 255, "G": 255, "B": 255, "opacity": 255}
        """
        return cls(color_r = json_color["R"],
                   color_g = json_color["G"],
                   color_b = json_color["B"],
                   opacity = json_color["opacity"] if "opacity" in json_color else None)

class Sector():
    """
    Sector (pie, MenuItem) definitions 
    """
    def __init__(self, outline = Color(), fill = Color()):
        self.outline = outline
        self.fill = fill

class AnimatedSector(Sector):
    """
    Active pointer sector (pie) definitions 
    """
    def __init__(self, outline = Color(), fill = Color(), speed = 1, multiplier = 1):
        Sector.__init__(self, outline, fill)
        self.animation_speed = speed
        self.animation_multiplier = multiplier

class VolumeArc():
    """
    Arc around menu representing volume definitions
    """
    def __init__(self,
                 background_fill = Color(),
                 foreground_fill = Color(),
                 animation_speed = 1,
                 ease_out_speed = 1
        ):
        self.background = background_fill
        self.foreground = foreground_fill
        self.animation_speed = animation_speed
        self.ease_out_speed = ease_out_speed

class CenterCircle(): # pylint: disable=too-many-arguments,too-many-positional-arguments # Aknowledged
    """
    Circle in the center of menu defifnitions
    """
    def __init__(self,
                 outline,
                 fill,
                 text_color = Color(),
                 volume_text_color = Color(),
                 size_mp = 1
        ):
        self.outline = outline
        self.fill = fill
        self.text_color = text_color
        self.volume_text_color = volume_text_color
        self.size_multiplier = size_mp

class IconAnimation():
    """
    Icon animation definitions
    """
    def __init__(self, min_scaling = 1, max_scaling = 1, scaling_angle = 1):
        self.min_scaling = min_scaling
        self.max_scaling = max_scaling
        self.scaling_angle = scaling_angle
