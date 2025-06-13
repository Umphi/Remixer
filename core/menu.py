"""
Menu construction items
"""
from collections import defaultdict
from core.remixer_theme import RemixerTheme as Theme


class MenuItem:
    """
    Default menu item class.
    """
    all_items = defaultdict(list)

    def __init__(self, name_, icon_ = None):
        self.name = name_
        self.icon = icon_
        self.all_items[name_].append(self)

    @classmethod
    def find_items_by_name(cls, name_):
        """
        Finds menu items by name.
        """
        return MenuItem.all_items[name_]

    @classmethod
    def find_first_item_by_name(cls, name_):
        """
        Finds first menu item with specified name.
        """
        return MenuItem.all_items[name_][0]


class Menu(MenuItem):
    """
    MenuItem that is Menu by itself.
    """
    nameindex = defaultdict(list)
    def __init__(self, name_, icon_=None, items_=None):
        super().__init__(name_, icon_)
        self.items = items_
        if items_ is not None:
            self.items = items_
            for item in self.items:
                self.nameindex[item.name] = item

    def add_item(self, menuitem):
        """
        Adds MenuItem to submenu.
        """
        if self.items is None:
            self.items = []
        self.items.append(menuitem)
        for item in self.items:
            self.nameindex[item.name] = item

    def index(self, name):
        """
        Finds containing MenuItem by name.

        Parameters:
        name (str): Name to return MenuItem in submenu.
        """
        return self.nameindex[name]

    def indexof(self, name):
        """
        Returns index of MenuItem in submenu by name.

        Parameters:
        name (str): Name to return index.
        """
        for i, item in enumerate(self.items):
            if item.name == name:
                return i
        return -1

class Placeholder(MenuItem):
    """
    MenuItem without any action apart from showing text.
    """
    def __init__(self, name_, icon_=None, text_=""):
        super().__init__(name_, icon_)
        self.text = text_

class Button(MenuItem):
    """
    MenuItem with assigned function callback that can be used for anything.
    """
    def __init__(self, name_, icon_=None, action_=None):
        super().__init__(name_, icon_)
        self.action = action_

class AppVolume(MenuItem):
    """
    MenuItem representing AppVolume object.
    Contains information about session to control volume.
    """
    pids = defaultdict()

    def __init__(self, name_, icon_ = None, session_ = None):
        super().__init__(name_, icon_)
        self.session = session_
        if session_ is not None and session_.Process:
            self.filename = session_.Process.name()
            self.pid = session_.Process.pid
            self.pids[name_] = session_.Process.pid

    @classmethod
    def get_pid_dict(cls):
        """
        Returns all available applications' PID
        """
        return AppVolume.pids

class ThemeItem(Button):
    """
    ThemeItem separates RemixerTheme object and Renderer
    """
    def __init__(self, theme: Theme, settings, menu_manager, icon_ = None):
        super().__init__(theme.name, icon_, self.apply_theme)
        self.theme = theme
        self.settings = settings
        self.menu_manager = menu_manager

    def apply_theme(self):
        """
        Function called when ThemeItem pressed by user
        """
        self.settings.change_theme(self.theme)
        self.menu_manager.menu_back()

    def on_focus(self):
        """
        Function called when ThemeItem focused by user in Themes menu
        """
        self.settings.set_showing_theme(self.theme)
