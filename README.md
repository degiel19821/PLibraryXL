# SteamForgeLib (`SteamForgeLib`)

`SteamForgeLib` is a lightweight, object-oriented Python library designed to simplify interaction with the Steam client ecosystem, configuration files, binary shortcuts, installed game manifests, and SteamGridDB artwork APIs.

It combines Steam `loginusers.vdf` parsing, JSON configuration management with dot-notation support, binary `shortcuts.vdf` handling, library folder scanning, Steam process monitoring, protocol launching, and Proton/UMU integration into one clean, dependency-light package.

This repository also includes a companion `SteamForgeLibGUI.py` application for live testing, debugging, and demonstration of the library's features.

> Important: The GUI depends on `PySide6`, but the core `SteamForgeLib.py` module does not. The library core only requires lightweight runtime dependencies such as `vdf` and `psutil`.

## Features Overview

* **Steam VDF Parsing:** Safely reads and parses `loginusers.vdf` files, including custom paths, and computes both `SteamID64` and `SteamID32` automatically.
* **JSON Configuration Engine:** Create, read, write, and update JSON config files using nested dot-notation keys like `settings.graphics.resolution`.
* **Batch Configuration Updates:** Apply multiple updates in one transaction with `update_config_values()`.
* **Binary Steam Shortcuts (`shortcuts.vdf`):** Full support for reading, writing, editing, adding, and removing non-Steam shortcuts, including custom VDF path overrides.
* **Official Steam Games Scanning:** Locate Steam library folders using `libraryfolders.vdf` and scan `appmanifest_*.acf` files for installed official games.
* **System Process Monitoring:** Detect whether Steam is currently running on the host OS via `psutil`.
* **UMU / Proton Integration:** Launch Windows executables with `umu-run` using custom Proton versions, `WINEPREFIX`, and launch arguments.
* **Steam Protocol Launching:** Trigger Steam launches through the native `steam://rungameid/<app_id>` protocol handler.
* **Local Artwork Discovery:** Search local Steam cache folders for cached artwork such as grids, heroes, logos, and icons.
* **SteamGridDB Integration:** Query games by name or ID, fetch artwork assets, and filter results by sizes and file types.
* **Interactive Test GUI (`SteamForgeLibGUI.py`):** A desktop testing sandbox for live inspection and interaction with the library.

---

## Prerequisites & Installation

### Core library only

If you are using `SteamForgeLib` in scripts or backend tools, install the minimal required packages:

```bash
pip install vdf psutil
```

### Full GUI stack

If you want to run the testing GUI, install PySide6 as well:

```bash
pip install PySide6 vdf psutil
python3 SteamForgeLibGUI.py
```

Ensure `SteamForgeLib.py` and `SteamForgeLibGUI.py` are in the same directory.

---

## The Testing & Demonstration GUI (`SteamForgeLibGUI.py`)

The GUI is a desktop workbench for exercising the library interactively. It is intended for debugging, experimentation, and demonstration.

### Tab 1: Steam Process & Users
* **Process Monitoring:** Check whether the Steam client is running.
* **Login Users:** Parse `loginusers.vdf` from default or custom paths and inspect account metadata.

### Tab 2: JSON Config Management
* **File Operations:** Create, load, and edit configuration files.
* **Single & Batch Updates:** Test dot-notation updates and multi-key batch writes.

### Tab 3: Steam Shortcuts & Official Games
* **Target Selection:** Set Steam user IDs and custom Steam paths.
* **Interactive Dialogs:** Read and write shortcut records and inspect installed game manifests.

### Tab 4: UMU / Proton Launcher Integration
* **Launcher Testing:** Run Windows executables via `umu-run` with custom Proton, `WINEPREFIX`, and launch arguments.

### Tab 5: SteamGridDB Integration & Preview
* **API Testing:** Search games by name or ID and apply filters for dimensions and file format.
* **Live Artwork Preview:** View downloaded SteamGridDB assets in the GUI.

---

## Core API Usage & Code Examples

### 1. Parsing Steam Login Users

```python
from SteamForgeLib import SteamForgeLib

# Default system Steam config path
try:
    accounts = SteamForgeLib.parse_steam_login_users()
    print(f"Found {len(accounts)} account(s).")
    for acc in accounts:
        print(acc["AccountName"], acc["SteamID64"], acc["SteamID32"])
except Exception as e:
    print(f"Failed to parse login users: {e}")

# Custom VDF path
custom_vdf = "/mnt/backup/Steam/config/loginusers.vdf"
try:
    accounts = SteamForgeLib.parse_steam_login_users(vdf_path=custom_vdf)
    print(accounts)
except Exception as e:
    print(f"Custom VDF parse failed: {e}")
```

### 2. JSON Configuration Management & Dot-Notation Updates

```python
from SteamForgeLib import SteamForgeLib

config_file = "my_app_config.json"

initial_data = {
    "settings": {
        "graphics": {
            "resolution": "1920x1080",
            "fullscreen": True,
        },
        "volume": 75,
    }
}

SteamForgeLib.create_config(config_file, initial_data=initial_data, overwrite=True)
SteamForgeLib.update_config_value(config_file, "settings.graphics.resolution", "2560x1440")
SteamForgeLib.update_config_values(config_file, {
    "settings.volume": 90,
    "settings.graphics.fullscreen": False,
    "user.profile.name": "PlayerOne",
})

print(SteamForgeLib.read_config(config_file))
```

### 3. System Process Monitoring

```python
from SteamForgeLib import SteamForgeLib

if SteamForgeLib.is_steam_running():
    print("Steam is running.")
else:
    print("Steam is not running.")
```

### 4. Managing Binary Steam Shortcuts (`shortcuts.vdf`)

```python
from SteamForgeLib import SteamForgeLib

steam_id_32 = 12345678

try:
    shortcuts = SteamForgeLib.read_shortcuts(steam_id_32)
    print(f"Loaded {len(shortcuts)} shortcut(s).")
except Exception as e:
    print(f"Shortcuts read failed: {e}")

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
    "tags": {"Favorites": 1},
}

SteamForgeLib.add_shortcut(steam_id_32, new_shortcut)
```

You can also point directly to a custom `shortcuts.vdf` path:

```python
SteamForgeLib.read_shortcuts(steam_id_32, vdf_path="/path/to/custom/shortcuts.vdf")
```

### 5. Scanning Installed Official Steam Games

```python
from SteamForgeLib import SteamForgeLib

try:
    libraries = SteamForgeLib.get_all_steam_library_folders()
    print("Libraries:", libraries)
except Exception as e:
    print(f"Failed to detect libraries: {e}")

try:
    installed_games = SteamForgeLib.get_installed_steam_games()
    for game in installed_games:
        size_mb = round(game["SizeOnDisk"] / (1024 * 1024), 2)
        print(f"[{game['AppID']}] {game['Name']} - {size_mb} MB")
except Exception as e:
    print(f"Failed to scan installed games: {e}")
```

### 6. UMU / Proton Launcher Integration

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
        log_output=True,
    )
    print(f"Launched with PID: {process.pid}")
except Exception as e:
    print(f"Launch failed: {e}")
```

### 7. Steam Protocol Launching

```python
from SteamForgeLib import SteamForgeLib

app_id = 730
try:
    SteamForgeLib.launch_steam_game(app_id)
    print(f"Triggering launch for AppID: {app_id}")
except Exception as e:
    print(f"Failed to launch game: {e}")
```

### 8. Local Artwork Discovery

```python
from SteamForgeLib import SteamForgeLib

art = SteamForgeLib.get_local_artwork(730)
print(art)
```

This searches the local Steam cache directories for artwork such as:

- `library_600x900.jpg`
- `library_hero.jpg`
- `header.jpg`
- `logo.png`
- `icon.jpg`

### 9. SteamGridDB Integration with Advanced Filters

```python
from SteamForgeLib import SteamForgeLib

API_KEY = "your_steamgriddb_api_key_here"

try:
    images = SteamForgeLib.get_sgdb_images_by_name(
        api_key=API_KEY,
        game_name="Hades",
        image_type="icons",
        sizes=["512x512"],
        filetypes=["png", "ico"],
    )
    print(f"Retrieved {len(images)} image(s).")
    for img in images:
        print(img["id"], img["width"], img["height"], img["url"])
except Exception as e:
    print(f"SteamGridDB query failed: {e}")
```

### 10. Error Handling

`SteamForgeLib` implements a custom exception hierarchy derived from `SteamForgeError`:

* `VDFParseError`: Issues parsing or reading VDF files.
* `ConfigError`: Problems reading or writing JSON config data.
* `ProcessMonitorError`: Process table or `psutil` access failures.
* `UMUError`: `umu-run` launch and wrapper issues.
* `ShortcutError`: Shortcut file corruption, indexing, or permission problems.
* `SteamGridDBError`: HTTP issues, invalid JSON, or missing content from SteamGridDB.

---

## API Reference Summary

| Method | Return Type | Description |
| --- | --- | --- |
| `SteamForgeLib.get_default_steam_path()` | `str` | Resolves the default Steam installation path for the host OS. |
| `SteamForgeLib.parse_steam_login_users(vdf_path=None)` | `list[dict]` | Parses `loginusers.vdf` and extracts account fields with ID64 / ID32 values. |
| `SteamForgeLib.create_config(file_path, initial_data=None, overwrite=False)` | `str` | Creates a new JSON config file and returns its path. |
| `SteamForgeLib.read_config(file_path)` | `dict` | Reads a JSON config file. |
| `SteamForgeLib.write_config(file_path, data, indent=4)` | `None` | Writes a JSON config atomically. |
| `SteamForgeLib.update_config_value(file_path, key_path, value)` | `None` | Updates a nested key using dot notation. |
| `SteamForgeLib.update_config_values(file_path, updates)` | `None` | Applies several nested updates in one batch. |
| `SteamForgeLib.is_steam_running()` | `bool` | Detects whether Steam is running on the host system. |
| `SteamForgeLib.launch_steam_game(app_id)` | `None` | Launches a Steam game via `steam://rungameid/<app_id>`. |
| `SteamForgeLib.launch_with_umu(target_exe, ...)` | `subprocess.Popen` | Launches a Windows executable using `umu-run` with Proton and `WINEPREFIX` support. |
| `SteamForgeLib.get_local_artwork(app_id, custom_steam_path=None)` | `dict` | Locates local cached artwork for a game. |
| `SteamForgeLib.get_shortcuts_path(steam_id_32, base_steam_path=None)` | `str` | Returns the shortcut path for a Steam user ID. |
| `SteamForgeLib.read_shortcuts(steam_id_32, vdf_path=None)` | `dict` | Reads a binary `shortcuts.vdf` file. |
| `SteamForgeLib.write_shortcuts(steam_id_32, shortcuts_dict, vdf_path=None)` | `None` | Writes a binary `shortcuts.vdf` file. |
| `SteamForgeLib.add_shortcut(steam_id_32, shortcut_data, vdf_path=None)` | `None` | Appends a shortcut entry. |
| `SteamForgeLib.edit_shortcut(steam_id_32, index, updates, vdf_path=None)` | `None` | Modifies a shortcut by index. |
| `SteamForgeLib.remove_shortcut(steam_id_32, index, vdf_path=None)` | `None` | Removes a shortcut and re-indexes the remaining items. |
| `SteamForgeLib.get_all_steam_library_folders(base_steam_path=None)` | `list[str]` | Finds the Steam library folders from `libraryfolders.vdf`. |
| `SteamForgeLib.get_installed_steam_games(base_steam_path=None)` | `list[dict]` | Scans `steamapps` and returns official installed games. |
| `SteamForgeLib.search_sgdb_game(api_key, game_name)` | `dict` | Autocomplete search for a game on SteamGridDB. |
| `SteamForgeLib.get_sgdb_images_by_id(api_key, game_id, image_type='grids', sizes=None, filetypes=None)` | `list[dict]` | Fetches artwork by game ID with filtering. |
| `SteamForgeLib.get_sgdb_images_by_name(api_key, game_name, image_type='grids', sizes=None, filetypes=None)` | `list[dict]` | Fetches artwork by name with filtering. |

---

## Notes

- The core library is lightweight and intended for headless usage in scripts and tools.
- The included GUI is a testing and demonstration tool, not a runtime dependency.
- The project is designed to work with default Steam paths, custom VDF locations, and multi-library setups.

