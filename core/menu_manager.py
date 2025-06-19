"""
Menu manager contains menu structure description and performs user commands.
Also implements information observer
"""
from pycaw.pycaw import AudioUtilities
from core.menu import Menu, Placeholder, Button, AppVolume, ThemeItem

class MenuObserver:
    """
    Dynamically causes information update in inherited classes
    """
    def on_focus_changed(self, index: int, last_turn: str):
        """
        Runs when focus changed in menu
        """

    def on_menu_changed(self, menu):
        """
        Runs when active menu changes
        """

class MenuManager:
    """
    Menu manager contains menu structure description and performs user commands.
    """
    dynamic_modules = []
    def __init__(self, settings, callbacks: dict):
        self.current_menu = {}
        self.menu_stack = []
        self.settings = settings
        self.observers = []
        self.focused_index = 0
        self.callbacks = callbacks
        self.last_turn = None

        self.reload_menu()

    def add_observer(self, observer: MenuObserver):
        """
        Adds observer to notify with updated info to the list.
        """
        self.observers.append(observer)

    def notify_focus(self):
        """
        Notifies observers with changed focus index.
        """
        for obs in self.observers:
            obs.on_focus_changed(self.focused_index, self.last_turn)

    def notify_menu(self):
        """
        Notifies observers about active menu change.
        """
        for obs in self.observers:
            obs.on_menu_changed(self.current_menu.items)

    def get_focus_item(self):
        """
        Returns item under user cursor.
        """
        if not self.current_menu.items:
            return None
        return self.current_menu.items[self.focused_index]

    def set_focus_by_condition(self, predicate):
        """
        Sets menu focus by condition
        """
        for idx, item in enumerate(self.current_menu.items):
            if predicate(item):
                self.focused_index = idx
                self.notify_focus()
                break

    def build_menu(self):
        """
        Loads menu with available applications producing sound.
        """

        menu = Menu("Main", None, None)
        menu.add_item(Menu("Menu",
                            "Settings",
                            [
                                Menu(
                                    "Themes",
                                    "Themes"
                                ),
                                Placeholder(
                                    "Credits",
                                    "Credits",
                                    "Version: 1.0 Beta\nRemixer\nby Umphi"
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
                                                self.callbacks["close_app"]
                                                )
                                    ]
                                )
                            ]
                    )
        )
        menu.add_item(Button("Hide", "Close", self.callbacks["hide_menu"]))

        for module in self.dynamic_modules:
            if module.is_enabled(self.settings):
                menu.index("Menu").add_item(module.get_menu_item(self))

        for theme in self.settings.themes:
            menu.index("Menu").index("Themes").add_item(
                                                    ThemeItem(theme,
                                                              self.settings,
                                                              self,
                                                              f"{theme.name}Theme"
                                                    )
            )

        sessions = AudioUtilities.GetAllSessions()

        for session in sessions:
            if session.Process:
                name = session.Process.name()
                if name in self.settings.ignored_apps:
                    continue
                alias = self.settings.aliases.get(name, name.replace(".exe", ""))
                menu.add_item(
                            AppVolume(
                                    alias,
                                    name,
                                    session
                            )
                )
        return menu

    def reload_menu(self):
        """
        Fully reloads and activates menu
        """
        self.current_menu = self.build_menu()
        self.menu_stack = []
        self.focused_index = 0
        self.last_turn = None

        self.notify_menu()
        self.notify_focus()

    def return_top_level_menu(self):
        """
        Switches to the top level of active menu
        """
        self.last_turn = None
        if len(self.menu_stack) > 0:
            self.menu_stack.reverse()
            self.current_menu, self.focused_index = self.menu_stack.pop()
            self.menu_stack.clear()

            self.notify_focus()
            self.notify_menu()

    def menu_back(self):
        """
        Returns to parent menu.
        """
        self.last_turn = None
        if not self.menu_stack:
            return
        self.current_menu, self.focused_index = self.menu_stack.pop()
        self.notify_focus()
        self.notify_menu()

    def rotate(self, delta):
        """
        Performs changing menu focus with given delta.
        Positive delta to move pointer clockwise.
        """
        if delta <= -1:
            self.last_turn = "left"
        elif delta >= 1:
            self.last_turn = "right"
        else:
            self.last_turn = None

        self.focused_index = (self.focused_index - delta) % len(self.current_menu.items)
        focused = self.get_focus_item()
        if hasattr(focused, 'on_focus'):
            focused.on_focus()

        self.notify_focus()

    def menu_enter(self, menu):
        """
        Activates menu under focused by cursor position
        """
        self.last_turn = None
        self.menu_stack.append((self.current_menu, self.focused_index))
        self.current_menu = menu
        self.focused_index = 0

        self.notify_focus()
        self.notify_menu()
