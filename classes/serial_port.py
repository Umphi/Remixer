"""
Class for working with custom controls, sending commands over serial interface
"""
import threading
from enum import Enum
import serial


class SerialDevice:
    """
    Custom Serial Device Worker
    """
    _instance = None
    _lock = threading.Lock()

    _port = ''
    _baudrate = 0
    _timeout = 1

    _serial = None
    _thread = None
    _running = False

    _events = {}

    class BaudRates(Enum):
        """
        Available baud rates
        """
        BAUD_300 = 300
        BAUD_600 = 600
        BAUD_1200 = 1200
        BAUD_2400 = 2400
        BAUD_4800 = 4800
        BAUD_9600 = 9600
        BAUD_19200 = 19200
        BAUD_38400 = 38400
        BAUD_57600 = 57600
        BAUD_115200 = 115200
        BAUD_230400 = 230400
        BAUD_460800 = 460800
        BAUD_921600 = 921600

    class RotaryEncoder:
        """
        Events of Rotary Encoder available to listen
        """
        class EncoderEvents(Enum):
            """
            Events of Rotary Encoder turns
            """
            ANTICLOCKWISE = "Rotary Encoder:: direction: ANTICLOCKWISE "
            CLOCKWISE = "Rotary Encoder:: direction: CLOCKWISE "

        class ButtonEvents(Enum):
            """
            Events of Rotary Encoder button
            """
            PRESS = "Rotary Encoder:: button down"
            RELEASE = "Rotary Encoder:: button up"
            CLICK = "Rotary Encoder:: button single press"
            DOUBLE_CLICK = "Rotary Encoder:: button double press"
            LONG_CLICK = "Rotary Encoder:: button long press"

    class BaudException(Exception):
        """
        Invalid baud rate Exception
        """

    class COMException(Exception):
        """
        Invalid COM port Exception
        """

    @classmethod
    def baud_from_int(cls, baud_int):
        """
        Gives appropriate Baud Rate value from int
        """
        try:
            return cls.BaudRates(baud_int)
        except ValueError as e:
            raise SerialDevice.BaudException("Unsupported baud rate") from e

    @classmethod
    def set_com(cls, com_port, baud):
        """Set SerialDevice COM port parameters"""
        if not isinstance(baud, cls.BaudRates):
            raise SerialDevice.BaudException("Invalid baud")
        cls._port = com_port
        cls._baudrate = baud.value

    @classmethod
    def _initialize(cls):
        """Port initialization and thread start"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    try:
                        cls._serial = serial.Serial(
                                                    port=cls._port,
                                                    baudrate=cls._baudrate,
                                                    timeout=cls._timeout
                        )
                        cls._running = True
                        cls._thread = threading.Thread(target=cls._read_loop, daemon=True)
                        cls._thread.start()
                    except serial.SerialException:
                        cls._running = False

    @classmethod
    def add_event(cls, event_enum, callback):
        """Add event to serial message"""
        if cls._port == '':
            raise SerialDevice.COMException("COM is not valid")

        cls._initialize()

        if isinstance(event_enum, cls.RotaryEncoder.EncoderEvents):
            event_name = event_enum.value
        elif isinstance(event_enum, cls.RotaryEncoder.ButtonEvents):
            event_name = event_enum.value
        else:
            event_name = event_enum

        with cls._lock:
            if event_enum not in cls._events:
                cls._events[event_name] = []
            cls._events[event_name].append(callback)

    @classmethod
    def _read_loop(cls):
        """Main loop"""
        while cls._running:
            try:
                if cls._serial.in_waiting:
                    line = cls._serial.readline().decode(errors='ignore').strip()
                    if line:
                        cls._dispatch_event(line)
            except serial.SerialException as e:
                print(f"Port read error: {e}")
                cls._running = False

    @classmethod
    def _dispatch_event(cls, line):
        """Event handling"""
        for event_name, callbacks in cls._events.items():
            if str(line).startswith(event_name):
                for callback in callbacks:
                    callback()

    @classmethod
    def stop(cls):
        """Stop reading and close port"""
        with cls._lock:
            cls._running = False
            if cls._thread and cls._thread.is_alive():
                cls._thread.join()
            if cls._serial and cls._serial.is_open:
                cls._serial.close()
            print("Port closed")
            cls._instance = None
            cls._events.clear()
