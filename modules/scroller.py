"""
Class for smooth system per-pixel scrolling
"""
import ctypes
import threading
import time

# Constants for mouse input
INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000
WHEEL_DELTA = 120

class MOUSEINPUT(ctypes.Structure):
    """ Mouse input structures """
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    """
    System structure receiving mouse events
    """
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

SendInput = ctypes.windll.user32.SendInput

class AdaptiveTouchScroller:
    """ Scroller performs commands to smooth mouse scroll """
    def __init__(self, step_pixels=300, tick_rate_hz=120, base_decay_rate=0.5,
                 speed_min=1.0, speed_max=50.0, fps_min=5.0, fps_max=50.0):
        self.step_pixels = step_pixels
        self.tick_interval = 1.0 / tick_rate_hz
        self.base_decay_rate = base_decay_rate

        self.speed_min = speed_min
        self.speed_max = speed_max

        self.fps_min = fps_min
        self.fps_max = fps_max

        self._lock = threading.Lock()
        self._accumulated_delta = 0.0            # vertical scroll
        self._accumulated_delta_x = 0.0          # horizontal scroll
        self._running = True

        self.last_event_time = None
        self._speed_multiplier = speed_min

        self._thread = threading.Thread(target=self._scroll_loop, daemon=True)
        self._thread.start()

    def scroll_pixels(self, delta_pixels):
        """
        Scroll Vertical command
        
        Parameters:
        delta_pixels(int): Amount of pixels (positive or negative) to be scrolled
        """
        now = time.time()
        with self._lock:
            if self.last_event_time is not None:
                dt = now - self.last_event_time
                if dt > 0:
                    current_fps = 1.0 / dt
                    self._update_speed_multiplier(current_fps)
            self.last_event_time = now

            self._accumulated_delta -= delta_pixels * self._speed_multiplier

    def scroll_pixels_horizontal(self, delta_pixels):
        """
        Scroll Horizontal command
        
        Parameters:
        delta_pixels(int): Amount of pixels (positive or negative) to be scrolled
        """
        now = time.time()
        with self._lock:
            if self.last_event_time is not None:
                dt = now - self.last_event_time
                if dt > 0:
                    current_fps = 1.0 / dt
                    self._update_speed_multiplier(current_fps)
            self.last_event_time = now

            self._accumulated_delta_x += delta_pixels * self._speed_multiplier

    def _update_speed_multiplier(self, current_fps):
        """
        Calculates scrolling speed depending 
        on user pointer position change (button press) frequency
        
        Parameters:
        current_fps(int): Amount user commands per second
        """
        if current_fps <= self.fps_min:
            self._speed_multiplier = self.speed_min
        else:
            t = (current_fps - self.fps_min) / (self.fps_max - self.fps_min)
            self._speed_multiplier = self.speed_min + t * (self.speed_max - self.speed_min)

    def _scroll_loop(self):
        """
        Scroll loop to perform scroll smoothly
        """
        while self._running:
            time.sleep(self.tick_interval)
            with self._lock:
                delta = self._accumulated_delta
                delta_x = self._accumulated_delta_x

                if abs(self._accumulated_delta) < 0.1:
                    self._accumulated_delta = 0
                else:
                    self._accumulated_delta *= self.base_decay_rate

                if abs(self._accumulated_delta_x) < 0.1:
                    self._accumulated_delta_x = 0
                else:
                    self._accumulated_delta_x *= self.base_decay_rate

            wheel_delta = int((delta / self.step_pixels) * WHEEL_DELTA)
            wheel_delta_x = int((delta_x / self.step_pixels) * WHEEL_DELTA)

            if wheel_delta != 0:
                self._send_wheel_event(wheel_delta)

            if wheel_delta_x != 0:
                self._send_hwheel_event(wheel_delta_x)

    def _send_wheel_event(self, wheel_delta):
        """
        Sends scroll whell event ot system
        """
        inp = INPUT()
        # pylint: disable=attribute-defined-outside-init
        inp.type = INPUT_MOUSE
        inp.mi = MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=wheel_delta,
            dwFlags=MOUSEEVENTF_WHEEL,
            time=0,
            dwExtraInfo=None
        )
        # pylint: enable=attribute-defined-outside-init
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def _send_hwheel_event(self, wheel_delta):
        """
        Sends horizontal scroll whell event ot system
        """
        inp = INPUT()
        # pylint: disable=attribute-defined-outside-init
        inp.type = INPUT_MOUSE
        inp.mi = MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=wheel_delta,
            dwFlags=MOUSEEVENTF_HWHEEL,
            time=0,
            dwExtraInfo=None
        )
        # pylint: enable=attribute-defined-outside-init
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def stop(self):
        """
        Stops scroller from working
        """
        self._running = False
        self._thread.join()
