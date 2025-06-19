"""
Main.py of Remixer. 
"""

import sys

from PySide6.QtWidgets import QApplication
from core.settings import SettingsManager
from core.drawing_window import DrawingWindow
from modules.input_controllers import init_keyboard_controls, init_serial_controls


if __name__ == "__main__":
    app_ = QApplication(sys.argv)

    settings = SettingsManager()

    window = DrawingWindow(settings)
    window.show()

    callbacks = {
                "ccw": window.input.control_down,
                "cw": window.input.control_up,
                "press": window.input.control_click,
                "double": window.input.control_double_click,
                "hold": window.input.control_hold
    }

    init_keyboard_controls(callbacks)
    init_serial_controls(settings, callbacks)

    sys.exit(app_.exec())
