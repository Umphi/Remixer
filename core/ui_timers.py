""" Initializing timers for UI drawing """
import math
from PySide6.QtCore import QTimer

class UITimers():
    """ Initializing timers for UI drawing """
    def __init__(self, parent, settings):
        self.draw_timer = QTimer(parent)
        self.draw_timer.start(math.floor(1000/settings.refresh_rate))
        self.draw_timer.timeout.connect(parent._updatescreen)

        self.fade_timer = QTimer(parent)
        self.fade_timer.setInterval(math.floor(1000/settings.refresh_rate))
        self.fade_timer.timeout.connect(parent._fade_step)

        self.inactivity_timer = QTimer(parent)
        self.inactivity_timer.setInterval(settings.get_selected_theme().fade_out_timeout)
        self.inactivity_timer.timeout.connect(parent.hide_menu)

    def start_inactivity(self):
        """ Starts inactivity timer """
        self.inactivity_timer.start()

    def stop_inactivity(self):
        """ Stops inactivity timer """
        self.inactivity_timer.stop()

    def start_fade(self):
        """ Starts fade timer """
        self.fade_timer.start()

    def stop_fade(self):
        """ Stops fade timer """
        self.fade_timer.stop()
