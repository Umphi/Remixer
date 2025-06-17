"""
Used for loading images and paint available icons to theme accent color
"""
import os
import psutil
import win32gui
import win32ui
from PIL import Image
from PySide6.QtGui import QPixmap
from core.resource_loader import Loader

class IconManager:
    """
    Used for loading images and paint available icons to theme accent color
    """
    icons = {}
    colored_icons = {}
    def __init__(self, settings, pids):
        self.settings = settings
        self.load_icons(pids)
        self.load_colored_icons()
        self.load_colored_theme_icons()

    def load_icons(self, pids):
        """
        Loads icons in memory for applications with specified pids.
        Parameters:
            pids (dict): Dictionary with PIDs of applications providing volume controls.
        """
        os.makedirs("./icons", exist_ok=True)
        for proc, pid in pids.items():
            if os.path.exists(f"./icons/{proc}.png"):
                continue

            self.extract_with_replacement(proc, pid)

        for file in os.listdir("./icons"):
            name = file.replace(".png", "")
            if name not in self.icons:
                self.icons[name] = QPixmap(f"./icons/{file}")

        if os.path.exists("./icons/internal"):
            for file in os.listdir("./icons/internal"):
                name = file.replace(".png", "")
                if name not in self.icons:
                    self.icons[name] = QPixmap(f"./icons/internal/{file}")

        for file in os.listdir(Loader.resource_path("./icons/internal")):
            name = file.replace(".png", "")
            if name not in self.icons:
                self.icons[name] = QPixmap(Loader.resource_path(f"./icons/internal/{file}"))

    def extract_with_replacement(self, proc, pid):
        """
        Checks if image replacement application available.
        If not loads standard icon.
        """
        if proc in self.settings.image_replacements:
            for procutil in psutil.process_iter():
                if procutil.name() == self.settings.image_replacements[proc]:
                    self.extract_icon(psutil.Process(procutil.pid).exe(), proc)
        else:
            self.extract_icon(psutil.Process(pid).exe(), proc)

    def load_colored_icons(self):
        """
        Loads available (usually, only internal) icons with specified in theme color.
        """
        theme = self.settings.get_showing_theme()
        for file in os.listdir(Loader.resource_path("./icons/internal")):
            name = file.replace(".png", "")
            if name.endswith("_Colorable"):
                image = Image.open(Loader.resource_path(f"./icons/internal/{file}"))
                image_pixels = image.load()

                image_colored = Image.new(image.mode, image.size)
                colored_pixels = image_colored.load()

                for i in range(image_colored.size[0]):
                    for j in range(image_colored.size[1]):
                        colored_pixels[i,j] = (
                                                theme.preferred_icon_color.r,
                                                theme.preferred_icon_color.g,
                                                theme.preferred_icon_color.b,
                                                image_pixels[i,j][3]
                        )

                self.colored_icons[name.replace("_Colorable", "")] = image_colored.toqpixmap()
                image.close()
                image_colored.close()

        if os.path.exists("./icons/internal"):
            for file in os.listdir("./icons/internal"):
                name = file.replace(".png", "")
                if name.endswith("_Colorable"):
                    image = Image.open(f"./icons/internal/{file}")
                    image_pixels = image.load()

                    image_colored = Image.new(image.mode, image.size)
                    colored_pixels = image_colored.load()

                    for i in range(image_colored.size[0]):
                        for j in range(image_colored.size[1]):
                            colored_pixels[i,j] = (
                                                theme.preferred_icon_color.r,
                                                theme.preferred_icon_color.g,
                                                theme.preferred_icon_color.b,
                                                image_pixels[i,j][3]
                            )

                    self.colored_icons[name.replace("_Colorable", "")] = image_colored.toqpixmap()
                    image.close()
                    image_colored.close()

    def load_colored_theme_icons(self):
        """
        Loads and paint images for theme preview.
        """
        themes = self.settings.themes
        icon_name = "Theme_Colorable.png"
        if icon_name in os.listdir(Loader.resource_path("./icons/internal")):
            image = Image.open(Loader.resource_path(f"./icons/internal/{icon_name}"))
            image_pixels = image.load()

            for theme in themes:
                image_colored = Image.new(image.mode, image.size)
                colored_pixels = image_colored.load()

                for i in range(image_colored.size[0]):
                    for j in range(image_colored.size[1]):
                        colored_pixels[i,j] = (
                                                theme.preferred_icon_color.r,
                                                theme.preferred_icon_color.g,
                                                theme.preferred_icon_color.b,
                                                image_pixels[i,j][3]
                        )

                self.colored_icons[f"{theme.name}Theme"] = image_colored.toqpixmap()
                image_colored.close()

            image.close()

        if os.path.exists("./icons/internal"):
            if icon_name in os.listdir("./icons/internal"):
                image = Image.open(f"./icons/internal/{icon_name}")
                image_pixels = image.load()

                image_colored = Image.new(image.mode, image.size)
                colored_pixels = image_colored.load()

                for theme in themes:
                    image_colored = Image.new(image.mode, image.size)
                    colored_pixels = image_colored.load()

                    for i in range(image_colored.size[0]):
                        for j in range(image_colored.size[1]):
                            colored_pixels[i,j] = (
                                                    theme.preferred_icon_color.r,
                                                    theme.preferred_icon_color.g,
                                                    theme.preferred_icon_color.b,
                                                    image_pixels[i,j][3]
                            )

                    self.colored_icons[f"{theme.name}Theme"] = image_colored.toqpixmap()
                    image_colored.close()

                image.close()

    def extract_icon(self, path, name):
        """
        Extract icon from Windows application and creates compatible icon.
        Parameters:
            path (str): Path to application directory.
            name (str): Windows Executable name.
        """
        path = path.replace("\\", "/")

        large, small = win32gui.ExtractIconEx(path, 0)
        if not large:
            return
        if small is not None:
            win32gui.DestroyIcon(small[0])

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), large[0])

        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (32, 32), bmpstr, 'raw', 'BGRA', 0, 1)
        img.save(f'./icons/{name}.png')
