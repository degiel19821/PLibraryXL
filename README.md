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
   * [1. Parsing Steam Login Users (with Custom VDF Path)](#1-parsing-steam-login-users-with-custom-vdf-path)
   * [2. JSON Configuration Management & Dot-Notation Updates](#2-json-configuration-management--dot-notation-updates)
   * [3. System Process Monitoring](#3-system-process-monitoring)
   * [4. Managing Binary Steam Shortcuts (`shortcuts.vdf` with Custom Paths)](#4-managing-binary-steam-shortcuts-shortcutsvdf-with-custom-paths)
   * [5. UMU / Proton Launcher Integration](#5-umu--proton-launcher-integration)
   * [6. SteamGridDB Integration with Advanced Filters](#6-steamgriddb-integration-with-advanced-filters)
   * [7. Error Handling](#7-error-handling)
5. [API Reference Summary](#api-reference-summary)

---

## Features Overview

* **Steam VDF Parsing:** Safely reads and parses Steam's `loginusers.vdf` configuration file, with full support for custom file paths, automatically computing both `SteamID64` and `SteamID32`.
* **JSON Configuration Engine:** Create, read, write, and manipulate JSON config files with advanced dot-notation key paths (e.g., `settings.graphics.resolution`).
* **Batch Configuration Updates:** Update multiple configuration values simultaneously in a single transaction.
* **Binary Steam Shortcuts (`shortcuts.vdf`):** Full CRUD support for non-Steam game shortcuts, complete with automatic sequential re-indexing, multi-field management, and custom VDF path overrides.
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
* **Login Users:** Specify or browse to any custom `loginusers.vdf` file path. Clicking **"Parse Login Users"** invokes `SteamForgeLib.parse_steam_login_users(vdf_path)`, populating a detailed table with account identifiers, persona names, and login preferences.

### Tab 2: JSON Config Management
* **File Operations:** Create pre-populated test configurations, load existing files, or edit JSON content directly in the embedded text editor.
* **Single & Batch Updates:** Test dot-notation updates (`settings.graphics.fullscreen`) or provide a JSON dictionary of multiple updates to test batch transactions.

### Tab 3: Steam Shortcuts Management
* **Target Selection:** Configure the target `SteamID32` and custom base Steam paths or direct VDF file paths to locate user-specific `shortcuts.vdf` files.
* **Interactive Dialogs:** Load, view, add, or edit non-Steam shortcuts across all binary fields. Deleting entries automatically re-indexes remaining shortcuts.

### Tab 4: UMU / Proton Launcher Integration
* **Launcher Testing:** Configure a target executable, `umu-run` path, Proton version, game ID, WINEPREFIX, and launch arguments to visually test running isolated Windows programs on Linux via the library wrapper.

### Tab 5: SteamGridDB Integration & Preview
* **API Testing:** Enter your SteamGridDB API key securely, choose between name-based search or direct ID lookup, and apply filters for asset dimensions (`600x900`) and file types (`png`).
* **Live Image Preview:** Selecting any row in the search results table automatically downloads and renders a high-quality preview of the artwork in the integrated viewer panel.

---

## Core API Usage & Code Examples

### 1. Parsing Steam Login Users (with Custom VDF Path)

Read local Steam account configurations from default or custom VDF file paths to extract user IDs and profile info.

```python
from SteamForgeLib import SteamForgeLib

# Example A: Using the default Linux Steam path (/home/deck/.local/share/Steam/config/loginusers.vdf)
try:
    accounts = SteamForgeLib.parse_steam_login_users()
    print(f"Found {len(accounts)} Steam account(s) from default path.")
except Exception as e:
    print(f"Failed to parse default login users: {e}")

# Example B: Providing a custom VDF file path (e.g., Windows backup, flatpak, or custom mount)
custom_vdf_path = "/mnt/backup/Steam/config/loginusers.vdf"
try:
    accounts = SteamForgeLib.parse_steam_login_users(vdf_path=custom_vdf_path)
    print(f"Found {len(accounts)} Steam account(s) from custom path:")
    for acc in accounts:
        print(f" - {acc['AccountName']} (ID64: {acc['SteamID64']}, ID32: {acc['SteamID32']})")
except Exception as e:
    print(f"Failed to parse custom login users path: {e}")
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
path = SteamForgeLib.create_config(config_file, initial_data=initial_data, overwrite=True)
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
config_data = SteamForgeLib.read_config(config_file)
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

### 4. Managing Binary Steam Shortcuts (`shortcuts.vdf` with Custom Paths)

Read, add, edit, and remove non-Steam game shortcuts using standard user IDs or custom VDF file overrides.

```python
from SteamForgeLib import SteamForgeLib

steam_id_32 = 12345678  # Replace with the user's 32-bit Steam ID

# Example A: Using standard base steam path resolution
try:
    shortcuts = SteamForgeLib.read_shortcuts(steam_id_32)
    print(f"Loaded {len(shortcuts)} shortcuts from default userdata directory.")
except Exception as e:
    print(f"Notice: {e}")

# Example B: Overriding with a custom shortcuts.vdf file path directly
custom_shortcuts_path = "/home/deck/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata/12345678/config/shortcuts.vdf"
try:
    shortcuts = SteamForgeLib.read_shortcuts(steam_id_32, vdf_path=custom_shortcuts_path)
    print(f"Loaded {len(shortcuts)} shortcuts from custom flatpak path.")
except Exception as e:
    print(f"Failed to read custom shortcuts path: {e}")

# Adding a new shortcut with the custom path override
new_shortcut = {
    "appname": "My Custom Game",
    "exe": '"/usr/bin/mygame"',
    "StartDir": '"/usr/bin"',
    "icon": "",
    "ShortcutPath": "",
    "LaunchOptions": "",
    "IsHidden": 0,
    "AllowDesktopConfig": 1,
    "AllowOverlay": 1,
    "OpenVR": 0,
    "Devkit": 0,
    "DevkitGameID": "",
    "DevkitOverrideAppID": 0,
    "LastPlayTime": 0,
    "FlatpakAppID": "",
    "tags": {"Favorites": 1}
}

SteamForgeLib.add_shortcut(steam_id_32, new_shortcut, vdf_path=custom_shortcuts_path)
print("New shortcut added successfully to custom VDF path.")
```

### 5. UMU / Proton Launcher Integration

Launch Windows executables via `umu-run` with isolated prefixes and custom Proton versions.

```python
from SteamForgeLib import SteamForgeLib

try:
    process = SteamForgeLib.launch_with_umu(
        target_exe="/path/to/game/game.exe",
        umu_run_path="umu-run",
        proton_version="/path/to/proton/Experimental",
        game_id="123456",
        prefix_path="/path/to/wineprefix",
        launch_options=["-dx11", "-windowed"],
        log_output=True
    )
    print(f"Successfully launched game with UMU (PID: {process.pid})")
except Exception as e:
    print(f"Launch failed: {e}")
```

### 6. SteamGridDB Integration with Advanced Filters

Search for games on SteamGridDB and retrieve customized artwork assets filtered by dimensions and file types.

```python
from SteamForgeLib import SteamForgeLib

API_KEY = "your_steamgriddb_api_key_here"

try:
    # Fetch custom icon assets for a game with size and format filtering
    images = SteamForgeLib.get_sgdb_images_by_name(
        api_key=API_KEY,
        game_name="Hades",
        image_type="icons",           # Options: 'grids', 'heroes', 'logos', 'icons'
        sizes=["512x512"],            # Filter by exact dimensions
        filetypes=["png", "ico"]      # Filter by file extension
    )

    print(f"Retrieved {len(images)} matching icon(s):")
    for img in images:
        print(f" - ID: {img['id']} | Dimensions: {img['width']}x{img['height']} | URL: {img['url']}")
except Exception as e:
    print(f"SteamGridDB query failed: {e}")
```

### 7. Error Handling

`SteamForgeLib` implements a custom exception hierarchy derived from `SteamForgeError` for precise try-except blocks:
* `VDFParseError`: Issues reading or interpreting VDF structures.
* `ConfigError`: Issues reading, writing, or manipulating JSON configuration files.
* `ProcessMonitorError`: Failures when hooking into the OS process table via `psutil`.
* `UMUError`: Failures establishing the wrapper or locating dependencies for `umu-run`.
* `ShortcutError`: Indexing errors, permission issues, or file corruptions during shortcuts.vdf transactions.
* `SteamGridDBError`: HTTP timeouts, missing assets, or invalid JSON payloads from the API.

---

## API Reference Summary

| Method | Return Type | Description |
| --- | --- | --- |
| `SteamForgeLib.get_default_steam_path()` | `str` | Dynamically resolves the default Steam installation path based on the host OS. |
| `SteamForgeLib.parse_steam_login_users(vdf_path)` | `list` | Parses `loginusers.vdf` (accepts custom `vdf_path`) and extracts account dicts with ID64/ID32. |
| `SteamForgeLib.create_config(file_path, initial_data, overwrite)` | `str` | Creates a new JSON configuration file and returns its absolute path. |
| `SteamForgeLib.read_config(file_path)` | `dict` | Reads and parses a JSON configuration file. |
| `SteamForgeLib.write_config(file_path, data, indent)` | `None` | Dumps dictionary data into a JSON configuration file atomically. |
| `SteamForgeLib.update_config_value(file_path, key_path, value)` | `None` | Updates a single config value using dot notation. |
| `SteamForgeLib.update_config_values(file_path, updates)` | `None` | Batch updates multiple config keys simultaneously. |
| `SteamForgeLib.is_steam_running()` | `bool` | Checks active OS processes via `psutil` for Steam instances. |
| `SteamForgeLib.launch_with_umu(target_exe, ...)` | `subprocess.Popen` | Launches a Windows `.exe` using `umu-run` with custom Proton & WINEPREFIX. |
| `SteamForgeLib.get_shortcuts_path(steam_id_32, base_steam_path)` | `str` | Returns the absolute path to a user's `shortcuts.vdf` file based on ID and base path. |
| `SteamForgeLib.read_shortcuts(steam_id_32, vdf_path)` | `dict` | Reads binary `shortcuts.vdf` (accepts custom `vdf_path`) for a given Steam user. |
| `SteamForgeLib.write_shortcuts(steam_id_32, dict, vdf_path)` | `None` | Dumps shortcut records back to binary VDF format (accepts custom `vdf_path`). |
| `SteamForgeLib.add_shortcut(steam_id_32, shortcut_data, path)` | `None` | Appends a new non-Steam shortcut entry (accepts custom `path`/`vdf_path`). |
| `SteamForgeLib.edit_shortcut(steam_id_32, index, updates, path)` | `None` | Modifies an existing shortcut by numeric index (accepts custom `path`/`vdf_path`). |
| `SteamForgeLib.remove_shortcut(steam_id_32, index, path)` | `None` | Removes a shortcut and auto-re-indexes remaining items (accepts custom `path`/`vdf_path`). |
| `SteamForgeLib.search_sgdb_game(api_key, game_name)` | `dict` | Autocomplete searches SteamGridDB for game details. |
| `SteamForgeLib.get_sgdb_images_by_id(api_key, id, type, ...)` | `list` | Fetches game assets by ID with size and filetype filtering. |
| `SteamForgeLib.get_sgdb_images_by_name(api_key, name, type, ...)` | `list` | Convenience wrapper resolving a game name to fetch filtered assets. |