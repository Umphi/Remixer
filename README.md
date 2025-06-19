# 🎧 Remixer

[![Pylint](https://github.com/Umphi/Remixer/actions/workflows/pylint.yml/badge.svg)](https://github.com/Umphi/Remixer/actions/workflows/pylint.yml)

**Remixer** is an application that extends keyboard volume key functionality with **per-application volume control**. It also supports custom control devices (e.g., rotary encoders).

> 💡 **Inspired by** [deej](https://github.com/omriharel/deej) (check this out, maybe that is what you are looking for)

---

## 🖼️ Preview

![Application](./assets/preview.gif)


---

## ⚙️ Features

- 🎧 Per-application volume control
- 🎹 Integration with keyboard media keys
- 🛠 Supports external control hardware
- 🎨 Custom themes and layouts (`themes.json`, theme creator application coming later)
- 🗂 Configurable via `settings.json`

---

## 🚀 Getting Started

### 🐍 Prerequisites

Install [Python 3](https://www.python.org/downloads/) on your system if not already available.  
To verify:
```bash
python --version
```

---

### 📦 Installation

#### Option 1: Download prebuilt binary (recommended for users)
You can download the ready-to-run version of **Remixer** from the [Releases section](https://github.com/Umphi/remixer/releases).  
Just download the latest `.zip` or `.exe`, unpack it, and run!

---

#### Option 2: Run from source

##### 1. Clone the repository
```bash
git clone https://github.com/Umphi/remixer
cd remixer
```

Or download manually:  
[Download as ZIP](https://github.com/Umphi/Remixer/archive/refs/heads/master.zip) and extract it.

##### 2. Install dependencies
```bash
pip install -r requirements.txt
```

##### 3. Configure
Edit the `settings.json` file to customize your configuration.

##### 4. Run the application
```bash
python main.py
```

---

## 🎛️ How to use

While the application window is hidden, your keyboard’s volume keys work as usual.
To open the window, press the ```Mute``` key on your keyboard.

Once the window appears:

 - ```Volume Up``` and ```Volume Down``` let you navigate through the menu (clockwise and counterclockwise).

 - ```Mute``` acts as the Enter key to select an item.

To hide the application, you can either press the corresponding "Hide" button in the main menu or simply wait a few seconds — the window will close automatically based on your theme settings.

This method of control works best with custom control devices, or when the volume adjustment on your keyboard is done using a rotary knob.


---

## 📁 Project Structure

```
remixer/
├── main.py                  # Main script
├── settings.json            # Configuration file
├── themes.json              # Themes file
├── requirements.txt         # Python dependencies
├── core/
│   ├── menu.py              # Menu elements
│   ├── remixer_theme.py     # Theme processing
│   ├── renderer.py          # Application drawing
│   ├── icon_manager.py      # Loading and providing icons
│   ├── settings.py          # Common application settings control
│   ├── drawing_window.py    # Main window definition
│   ├── input_handler.py     # Contains handlers for user inputs
│   ├── menu_manager.py      # Contains menu structure description
│   ├── resource_loader.py   # Loads resource files for pre-built Remixer
│   ├── tray_controller.py   # Controls tray menu in taskbar
│   └── ui_timers.py         # Contains timers for UI drawing
├── modules/
│   ├── serial_port.py       # Operating with custom controllers
│   ├── scroller.py          # Smooth in-system scrolling (currently supports only custom controllers)
│   └── input_controllers.py # User controllers definitions
├── icons/
│   └── internal/            # Internal icons for menu 
│       └── ... 
├── assets/                  # Data for documentation
│       └── ... 
└── ...
```

---

## 🛠 Contributing

Pull requests are welcome but please open an issue first to discuss what you'd like to change or add.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) and [THIRD-PARTY-LICENSES](./THIRD-PARTY-LICENSES.md) for details.

Although MIT license permits nearly unrestricted use, I would appreciate it if you keep the source code of derivative projects open to support open source software development 🤝

---

## 🌐 Links

- [deej by omriharel](https://github.com/omriharel/deej)
- [Python Downloads](https://www.python.org/downloads/)

---

Made by [Umphi](https://github.com/Umphi) 🖐
