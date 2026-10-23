# SteamForgeLib

SteamForgeLib is a small Python toolkit for reading and interacting with Steam installation metadata, config files, shortcut entries, and SteamGridDB artwork data.

The repository currently contains:

- `SteamForgeLib.py` — core library classes for Steam-related utilities
- `SteamForgeLibGUI.py` — Qt-based demo/test GUI for exercising the library
- `run_gui.sh` — helper script to launch the GUI
- `uninstall.sh` — helper script for local cleanup

## Current project structure

The core library is organized around a set of classes, not a single umbrella wrapper class:

- `FileIOManager` — atomic file writes
- `ConfigManager` — JSON config creation, read/write, and nested key updates
- `SteamEnvironment` — Steam path detection and VDF parsing
- `ProcessManager` — Steam process detection and launch helpers
- `ShortcutManager` — reading/writing `shortcuts.vdf`
- `LocalArtworkManager` — local app artwork lookup
- `SteamGridDBClient` — SteamGridDB API access

Custom exception types are also defined:

- `SteamForgeError`
- `VDFParseError`
- `ConfigError`
- `ProcessMonitorError`
- `UMUError`
- `ShortcutError`
- `SteamGridDBError`

## Installation

Core runtime dependencies:

```bash
pip install vdf psutil
```

If you want to run the GUI demo:

```bash
pip install PySide6 vdf psutil
python3 SteamForgeLibGUI.py
```

## Usage

Import the module and access the classes directly:

```python
import SteamForgeLib

# Resolve the default Steam install path
path = SteamForgeLib.SteamEnvironment.get_default_path()
print(path)

# Parse Steam accounts
accounts = SteamForgeLib.SteamEnvironment.parse_login_users()
print(accounts)
```

## Configuration management

```python
import SteamForgeLib

config_path = "example_config.json"

SteamForgeLib.ConfigManager.create(
    config_path,
    initial_data={"settings": {"graphics": {"resolution": "1920x1080"}}},
    overwrite=True,
)

SteamForgeLib.ConfigManager.update_values(
    config_path,
    {
        "settings.graphics.resolution": "2560x1440",
        "settings.volume": 85,
    },
)

print(SteamForgeLib.ConfigManager.read(config_path))
```

## Steam environment and library scanning

```python
import SteamForgeLib

libraries = SteamForgeLib.SteamEnvironment.get_library_folders()
print(libraries)

games = SteamForgeLib.SteamEnvironment.get_installed_games()
for game in games:
    print(game["AppID"], game["Name"])
```

## Steam process and launch helpers

```python
import SteamForgeLib

print(SteamForgeLib.ProcessManager.is_steam_running())

# Launch a Steam game by AppID
SteamForgeLib.ProcessManager.launch_steam_game(730)
```

UMU launch example:

```python
import SteamForgeLib

proc = SteamForgeLib.ProcessManager.launch_with_umu(
    target_exe="/path/to/game.exe",
    umu_run_path="umu-run",
    proton_version="/path/to/proton",
    game_id="123456",
    prefix_path="/path/to/wineprefix",
    launch_options=["-dx11", "-windowed"],
    log_output=True,
)
print(proc.pid)
```

## Shortcuts support

```python
import SteamForgeLib

steam_id_32 = 12345678
shortcut_path = SteamForgeLib.ShortcutManager.get_path(steam_id_32)
print(shortcut_path)

# Read all shortcut entries for this user
shortcuts = SteamForgeLib.ShortcutManager.read(steam_id_32)
print(shortcuts)

# Add a new shortcut entry
SteamForgeLib.ShortcutManager.add(
    steam_id_32,
    {
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
    },
)
```

## Local artwork lookup

```python
import SteamForgeLib

art = SteamForgeLib.LocalArtworkManager.get_artwork(730)
print(art)
```

This searches Steam's local `appcache/librarycache` directory for cached artwork including:

- `library_600x900.jpg`
- `library_hero.jpg`
- `header.jpg`
- `logo.png`
- `icon.jpg`

## SteamGridDB integration

```python
import SteamForgeLib

api_key = "your_api_key_here"

result = SteamForgeLib.SteamGridDBClient.search_game(api_key, "Hades")
print(result)

images = SteamForgeLib.SteamGridDBClient.get_images_by_id(api_key, 47540, image_type="grids")
print(images[:3])
```

## GUI demo

The repository includes a Qt-based test harness for interactive experimentation:

```bash
python3 SteamForgeLibGUI.py
```

The GUI allows you to:

- check whether Steam is running
- parse `loginusers.vdf`
- create/edit JSON config files
- inspect Steam `shortcuts.vdf`
- scan installed Steam games
- launch games via UMU / Proton
- query SteamGridDB and preview artwork

## Notes

- The core library is intentionally lightweight and does not require the GUI stack.
- `SteamForgeLib.py` is the main runtime module; the GUI is a convenience test/debug tool, not a dependency.
- Most file operations are implemented with atomic writes to reduce corruption risk.

## Quick reference

- `ConfigManager.create(path, initial_data=None, overwrite=False)`
- `ConfigManager.read(path)`
- `ConfigManager.write(path, data, indent=4)`
- `ConfigManager.update_values(path, updates)`
- `SteamEnvironment.get_default_path()`
- `SteamEnvironment.parse_login_users(vdf_path=None)`
- `SteamEnvironment.get_library_folders(base_steam_path=None)`
- `SteamEnvironment.get_installed_games(base_steam_path=None)`
- `ProcessManager.is_steam_running()`
- `ProcessManager.launch_steam_game(app_id)`
- `ProcessManager.launch_with_umu(...)`
- `ShortcutManager.get_path(steam_id_32, base_steam_path=None)`
- `ShortcutManager.read(steam_id_32, vdf_path=None)`
- `ShortcutManager.write(steam_id_32, shortcuts_dict, vdf_path=None)`
- `ShortcutManager.add(steam_id_32, shortcut_data, vdf_path=None)`
- `LocalArtworkManager.get_artwork(app_id, custom_steam_path=None)`
- `SteamGridDBClient.search_game(api_key, game_name)`
- `SteamGridDBClient.get_images_by_id(api_key, game_id, image_type="grids")`
