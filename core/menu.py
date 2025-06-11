"""
Menu construction items
"""
from collections import defaultdict


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
            self.items = list()
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

    def __init__(self, name_, icon_ = None, session_ = None, filename_ = None, pid_ = -1):
        super().__init__(name_, icon_)
        self.session = session_
        self.filename = filename_
        self.pid = pid_
        self.pids[name_] = pid_

    @classmethod
    def get_pid_dict(cls):
        return AppVolume.pids
