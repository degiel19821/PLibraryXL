# SteamForgeLib (`SteamForgeLib`)

`SteamForgeLib` is a robust, lightweight, and object-oriented Python library designed to simplify interaction with the Steam client ecosystem, configuration files, binary shortcuts, external metadata APIs, and Proton/UMU compatibility layers.

It unifies **Steam `loginusers.vdf` parsing**, **JSON configuration management** (with dot notation support), **binary Steam shortcuts (`shortcuts.vdf`) management**, **system process monitoring via `psutil`**, **UMU / Proton launcher integration (`launch_with_umu`)**, and **SteamGridDB API integration** into a single cohesive library.

This repository also includes a fully-featured **PySide6 graphical user interface (`SteamForgeLibGUI.py`)**, built specifically as a live testing workbench and demonstration suite for every single feature and method in the library.

> **Important Note on Dependencies:** **Only the testing GUI (`SteamForgeLibGUI.py`) requires PySide6.** The core library (`SteamForgeLib.py`) does **not** use PySide6 and depends only on lightweight community standards (`vdf` and `psutil`), making it fully suitable for headless scripts, automation tools, or backend services.

## Table of Contents

1. [Features Overview](#features-overview)
2. [Prerequisites & Installation](#prerequisites--installation)
3. [The Testing & Demonstration GUI (`SteamForgeLibGUI.py`)](#the-testing--demonstration-gui-steamforgelibguippy)
4. [Core API Usage & Code Examples](#core-api-usage--code-examples)
   * [1. Parsing Steam Login Users](#1-parsing-steam-login-users)
   * [2. JSON Configuration Management & Dot-Notation Updates](#2-json-configuration-management--dot-notation-updates)
   * [3. System Process Monitoring](#3-system-process-monitoring)
   * [4. Managing Binary Steam Shortcuts (`shortcuts.vdf`)](#4-managing-binary-steam-shortcuts-shortcutsvdf)
   * [5. UMU / Proton Launcher Integration](#5-umu--proton-launcher-integration)
   * [6. SteamGridDB Integration with Advanced Filters](#6-steamgriddb-integration-with-advanced-filters)
5. [API Reference Summary](#api-reference-summary)

---

## Features Overview

* **Steam VDF Parsing:** Safely reads and parses Steam's `loginusers.vdf` configuration file, automatically computing both `SteamID64` and `SteamID32`.
* **JSON Configuration Engine:** Create, read, write, and manipulate JSON config files with advanced dot-notation key paths (e.g., `settings.graphics.resolution`).
* **Batch Configuration Updates:** Update multiple configuration values simultaneously in a single transaction.
* **Binary Steam Shortcuts (`shortcuts.vdf`):** Full CRUD support for non-Steam game shortcuts, complete with automatic sequential re-indexing and multi-field management (launch options, flags, VR, tags).
* **System Process Monitoring:** Quickly verify whether the official Steam client is active on the host OS via `psutil`.
* **UMU / Proton Integration:** Directly launch Windows executables using `umu-launcher` (`umu-run`) with custom Proton versions, WINEPREFIX paths, and game identifiers.
* **SteamGridDB Integration:** Query games via autocomplete search or direct ID lookup, fetch assets (`grids`, `heroes`, `logos`, `icons`), and apply filters for image dimensions and file types (`png`, `ico`, `jpg`).
* **Interactive Test GUI (`SteamForgeLibGUI.py`):** A multi-tab desktop app allowing live inspection, manipulation, and visual preview of all library operations.

---

## Prerequisites & Installation

Depending on how you plan to use `SteamForgeLib`, you can install either just the lightweight core dependencies or the full GUI stack. 

### Automated Setup (Recommended for GUI Testing)

For the easiest way to test the full stack, use the provided helper scripts. They will automatically create an isolated Python virtual environment (`.venv`), install all required dependencies (including PySide6), and launch the interface:

```bash
# Make the scripts executable
chmod +x run_gui.sh uninstall.sh

# Setup the environment and launch the GUI
./run_gui.sh

# When you're done, you can cleanly remove the environment and cache files
./uninstall.sh
```

### Manual Installation

#### 1. Core Library Only (Headless / Backend / Scripts)

If you are only importing `SteamForgeLib` into your own scripts or backend tools, you only need `vdf` and `psutil`:

```bash
pip install vdf psutil
```

#### 2. Full Stack with Testing GUI

If you want to manually run the interactive PySide6 graphical testing workbench (`SteamForgeLibGUI.py`), install PySide6 alongside the core packages:

```bash
pip install PySide6 vdf psutil
python3 SteamForgeLibGUI.py
```

Ensure `SteamForgeLib.py` and `SteamForgeLibGUI.py` are located in the same working directory.

---

## The Testing & Demonstration GUI (`SteamForgeLibGUI.py`)

The companion GUI application (`SteamForgeLibGUI.py`) serves as an interactive testing sandbox and demonstration suite for `SteamForgeLib`. Designed strictly for testing and demonstrating the library's capabilities visually, it features a tabbed layout and a real-time execution log window at the bottom.

### Tab 1: Steam Process & Users
* **Process Monitoring:** Click **"Check if Steam is Running"** to execute `SteamForgeLib.is_steam_running()` and instantly check process states via `psutil`.
* **Login Users:** Specify or browse to your `loginusers.vdf` file. Clicking **"Parse Login Users"** invokes `SteamForgeLib.parse_steam_login_users()`, populating a detailed table with account identifiers, persona names, and login preferences.

### Tab 2: JSON Config Management
* **File Operations:** Create pre-populated test configurations, load existing files, or edit JSON content directly in the embedded text editor.
* **Single & Batch Updates:** Test dot-notation updates (`settings.graphics.fullscreen`) or provide a JSON dictionary of multiple updates to test batch transactions.

### Tab 3: Steam Shortcuts Management
* **Target Selection:** Configure the target `SteamID32` and base Steam path to locate user-specific `shortcuts.vdf` files.
* **Interactive Dialogs:** Load, view, add, or edit non-Steam shortcuts across all 13 binary fields (executable paths, tags, start directories, hidden/overlay flags). Deleting entries automatically re-indexes remaining shortcuts.

### Tab 4: UMU / Proton Launcher Integration
* **Launcher Testing:** Configure a target executable, `umu-run` path, Proton version, game ID, WINEPREFIX, and launch arguments to visually test running isolated Windows programs on Linux via the library wrapper.

### Tab 5: SteamGridDB Integration & Preview
* **API Testing:** Enter your SteamGridDB API key securely, choose between name-based search or direct ID lookup, and apply filters for asset dimensions (`600x900`) and file types (`png`).
* **Live Image Preview:** Selecting any row in the search results table automatically downloads and renders a high-quality preview of the artwork in the integrated viewer panel.

---

## Core API Usage & Code Examples

### 1. Parsing Steam Login Users

Read local Steam account configurations to extract user IDs and profile info.

```python
from SteamForgeLib import SteamForgeLib

# Parse login users from the default path (or pass a custom vdf_path)
success, accounts, count, error = SteamForgeLib.parse_steam_login_users()

if success:
    print(f"Found {count} Steam account(s):")
    for acc in accounts:
        print(f" - {acc['AccountName']} (ID64: {acc['SteamID64']}, ID32: {acc['SteamID32']})")
else:
    print(f"Failed to parse login users: {error}")
```

### 2. JSON Configuration Management & Dot-Notation Updates

Create configuration files and update nested parameters cleanly using dot notation.

```python
from SteamForgeLib import SteamForgeLib

config_file = "my_app_config.json"

# 1. Create a configuration file with initial data
initial_data = {
    "settings": {
        "graphics": {
            "resolution": "1920x1080",
            "fullscreen": True
        },
        "volume": 75
    }
}
success, path, error = SteamForgeLib.create_config(config_file, initial_data=initial_data, overwrite=True)
if success:
    print(f"Config created at: {path}")

# 2. Update a single nested key using dot notation
SteamForgeLib.update_config_value(config_file, "settings.graphics.resolution", "2560x1440")

# 3. Perform batch updates on multiple keys at once
SteamForgeLib.update_config_values(config_file, {
    "settings.volume": 90,
    "settings.graphics.fullscreen": False,
    "user.profile.name": "PlayerOne"
})

# 4. Read back the updated configuration
success, config_data, error = SteamForgeLib.read_config(config_file)
print("Updated Config:", config_data)
```

### 3. System Process Monitoring

Check if the official Steam client is currently active on the host machine.

```python
from SteamForgeLib import SteamForgeLib

if SteamForgeLib.is_steam_running():
    print("Steam client is currently running.")
else:
    print("Steam client is not running.")
```

### 4. Managing Binary Steam Shortcuts (`shortcuts.vdf`)

Read, add, edit, and remove non-Steam game shortcuts for a specific Steam user account.

```python
from SteamForgeLib import SteamForgeLib

steam_id_32 = 12345678  # Replace with the user's 32-bit Steam ID

# 1. Read existing shortcuts
success, shortcuts, count, error = SteamForgeLib.read_shortcuts(steam_id_32)
if success:
    print(f"Loaded {count} non-Steam shortcuts.")

# 2. Add a new non-Steam shortcut
new_shortcut = {
    "appname": "My Custom Emulator",
    "exe": '"/usr/bin/emu"',
    "StartDir": '"/usr/bin"',
    "icon": "",
    "ShortcutPath": "",
    "LaunchOptions": "-roms /path/to/roms",
    "IsHidden": 0,
    "AllowDesktopConfig": 1,
    "AllowOverlay": 1,
    "OpenVR": 0,
    "Devkit": 0,
    "DevkitGameID": "",
    "DevkitOverrideAppID": 0,
    "LastPlayTime": 1700000000,
    "FlatpakAppID": "",
    "tags": {"Emulator": 1, "Retro": 1}
}

success, error = SteamForgeLib.add_shortcut(steam_id_32, new_shortcut)
if success:
    print("New shortcut added successfully.")

# 3. Remove a shortcut by index (automatically re-indexes remaining entries)
# SteamForgeLib.remove_shortcut(steam_id_32, index=0)
```

### 5. UMU / Proton Launcher Integration

Launch Windows executables via `umu-run` with isolated prefixes and custom Proton versions.

```python
from SteamForgeLib import SteamForgeLib

success, process, error = SteamForgeLib.launch_with_umu(
    target_exe="/path/to/game/game.exe",
    umu_run_path="umu-run",
    proton_version="/path/to/proton/Experimental",
    game_id="123456",
    prefix_path="/path/to/wineprefix",
    launch_options=["-dx11", "-windowed"],
    log_output=True
)

if success:
    print(f"Successfully launched game with UMU (PID: {process.pid})")
else:
    print(f"Launch failed: {error}")
```

### 6. SteamGridDB Integration with Advanced Filters

Search for games on SteamGridDB and retrieve customized artwork assets filtered by dimensions and file types.

```python
from SteamForgeLib import SteamForgeLib

API_KEY = "your_steamgriddb_api_key_here"

# Fetch custom icon assets for a game with size and format filtering
success, images, error = SteamForgeLib.get_sgdb_images_by_name(
    api_key=API_KEY,
    game_name="Hades",
    image_type="icons",           # Options: 'grids', 'heroes', 'logos', 'icons'
    sizes=["512x512"],            # Filter by exact dimensions
    filetypes=["png", "ico"]      # Filter by file extension
)

if success:
    print(f"Retrieved {len(images)} matching icon(s):")
    for img in images:
        print(f" - ID: {img['id']} | Dimensions: {img['width']}x{img['height']} | URL: {img['url']}")
else:
    print(f"SteamGridDB query failed: {error}")
```

---

## API Reference Summary

| Method | Return Type | Description |
| --- | --- | --- |
| `SteamForgeLib.parse_steam_login_users(vdf_path)` | `tuple[bool, list, int, str]` | Parses `loginusers.vdf` and extracts account dicts with ID64/ID32. |
| `SteamForgeLib.create_config(file_path, initial_data, overwrite)` | `tuple[bool, str, str]` | Creates a new JSON configuration file. |
| `SteamForgeLib.read_config(file_path)` | `tuple[bool, dict, str]` | Reads and parses a JSON configuration file. |
| `SteamForgeLib.write_config(file_path, data, indent)` | `tuple[bool, str]` | Dumps dictionary data into a JSON configuration file. |
| `SteamForgeLib.update_config_value(file_path, key_path, value)` | `tuple[bool, str]` | Updates a single config value using dot notation. |
| `SteamForgeLib.update_config_values(file_path, updates)` | `tuple[bool, str]` | Batch updates multiple config keys simultaneously. |
| `SteamForgeLib.is_steam_running()` | `bool` | Checks active OS processes via `psutil` for Steam instances. |
| `SteamForgeLib.launch_with_umu(target_exe, ...)` | `tuple[bool, subprocess.Popen, str]` | Launches a Windows `.exe` using `umu-run` with custom Proton & WINEPREFIX. |
| `SteamForgeLib.read_shortcuts(steam_id_32, vdf_path)` | `tuple[bool, dict, int, str]` | Reads binary `shortcuts.vdf` for a given Steam user. |
| `SteamForgeLib.write_shortcuts(steam_id_32, dict, vdf_path)` | `tuple[bool, str]` | Dumps shortcut records back to binary VDF format. |
| `SteamForgeLib.add_shortcut(steam_id_32, shortcut_data, path)` | `tuple[bool, str]` | Appends a new non-Steam shortcut entry. |
| `SteamForgeLib.edit_shortcut(steam_id_32, index, updates, path)` | `tuple[bool, str]` | Modifies an existing shortcut by numeric index. |
| `SteamForgeLib.remove_shortcut(steam_id_32, index, path)` | `tuple[bool, str]` | Removes a shortcut and auto-re-indexes remaining items. |
| `SteamForgeLib.search_sgdb_game(api_key, game_name)` | `tuple[bool, dict, str]` | Autocomplete searches SteamGridDB for game details. |
| `SteamForgeLib.get_sgdb_images_by_id(api_key, id, type, ...)` | `tuple[bool, list, str]` | Fetches game assets by ID with size and filetype filtering. |
| `SteamForgeLib.get_sgdb_images_by_name(api_key, name, type, ...)` | `tuple[bool, list, str]` | Convenience wrapper resolving a game name to fetch filtered assets. |