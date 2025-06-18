"""
Input Controller contains methods to initialize user controls
"""
import keyboard
from modules.serial_port import SerialDevice

def init_serial_controls(settings, callbacks):
    """ Serial Device Initializer """
    if settings.serial_com == "" or settings.serial_baud == 0:
        return

    SerialDevice.set_com(
                        settings.serial_com,
                        SerialDevice.baud_from_int(settings.serial_baud)
    )
    SerialDevice.add_event(
                        SerialDevice.RotaryEncoder.EncoderEvents.ANTICLOCKWISE,
                        callbacks["ccw"]
    )
    SerialDevice.add_event(
                        SerialDevice.RotaryEncoder.EncoderEvents.CLOCKWISE,
                        callbacks["cw"]
    )
    SerialDevice.add_event(
                        SerialDevice.RotaryEncoder.ButtonEvents.CLICK,
                        callbacks["press"]
    )
    SerialDevice.add_event(SerialDevice.RotaryEncoder.ButtonEvents.DOUBLE_CLICK,
                        callbacks["double"]
    )
    SerialDevice.add_event(SerialDevice.RotaryEncoder.ButtonEvents.LONG_CLICK,
                        callbacks["hold"]
    )

def init_keyboard_controls(callbacks):
    """ Keyboard hotkeys initializer"""
    keyboard.add_hotkey(-175, callbacks["cw"], suppress=True)
    keyboard.add_hotkey(-174, callbacks["ccw"], suppress=True)
    keyboard.add_hotkey(-173, callbacks["press"], suppress=True)
