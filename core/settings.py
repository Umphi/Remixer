"""
Settings manager performs application settings control
"""
import json
from core.remixer_theme import RemixerTheme as Theme
from core.icon_manager import IconManager
from core.menu import AppVolume

class SettingsManager: # pylint: disable=too-many-instance-attributes # Aknowledged
    """
    Controls application settings throughout run 
    """
    DEFAULT_SETTINGS_PATH = './settings.json'
    DEFAULT_THEMES_PATH = './themes.json'

    def __init__(self, settings_path=None, themes_path=None):
        self.settings_path = settings_path or self.DEFAULT_SETTINGS_PATH
        self.themes_path = themes_path or self.DEFAULT_THEMES_PATH

        self.refresh_rate = 60
        self.aliases = {}
        self.ignored_apps = {}
        self.themes = []
        self.image_replacements = {}
        self.selected_theme = None
        self.theme = None

        self.serial_com = ""
        self.serial_baud = 0

        self._load_settings()

        self.icon_manager = IconManager(self, AppVolume.get_pid_dict())

    def _load_settings(self):
        """
        Loads and processes settings.
        """
        try:
            theme = ""
            with open('./settings.json', 'r', encoding='utf-8') as file:
                settings = json.load(file)
                self.aliases = settings["Aliases"]
                self.ignored_apps = settings["IgnoreProcesses"]
                self.image_replacements = settings["ImageReplacements"]
                self.refresh_rate = settings["RefreshRate"]

                if "SerialCOM" in settings and "SerialBaud" in settings:
                    self.serial_com = settings["SerialCOM"]
                    self.serial_baud = settings["SerialBaud"]

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
                self.selected_theme = Theme.find_by_name(theme)
                self.theme = self.selected_theme
        except FileNotFoundError:
            pass

    def change_theme(self, theme):
        """
        Activates chosen theme and writes it in config.

        Parameters:
            Theme (Theme): Theme to activate.
        """
        self.selected_theme = theme
        self.theme = theme
        self.icon_manager.load_colored_icons()

        settings = {}
        with open('settings.json', 'r', encoding='utf-8') as file:
            settings = json.load(file)
            settings["SelectedTheme"] = theme.name
        with open('settings.json', 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)

    def get_selected_theme(self):
        """
        Gets selected theme
        """
        return self.selected_theme

    def get_showing_theme(self):
        """
        Gets currently shown theme
        """
        return self.theme

    def set_showing_theme(self, theme):
        """
        Sets currently showing theme
        """
        self.theme = theme
