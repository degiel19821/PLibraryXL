# SteamForgeLib

SteamForgeLib is a lightweight Python library for reading and managing Steam installation metadata, config files, custom shortcuts, installed game manifests, local artwork cache, and SteamGridDB artwork metadata.

This repo is intentionally small and direct. The main runtime module is `SteamForgeLib.py`, and it exposes a set of classes rather than a single umbrella `SteamForgeLib` object.

## Repository layout

- `SteamForgeLib.py` — core Steam utilities and data access helpers
- `SteamForgeLibGUI.py` — Qt-based feature tester / demo GUI
- `run_gui.sh` — convenience launcher for the GUI
- `uninstall.sh` — local helper script

## Install

Core runtime dependencies:

```bash
pip install vdf psutil
```

GUI dependencies:

```bash
pip install PySide6 vdf psutil
python3 SteamForgeLibGUI.py
```

## Import style

The project does not expose `SteamForgeLib = ...` as a single object. Import the module and call the classes directly:

```python
import SteamForgeLib

print(SteamForgeLib.ConfigManager)
print(SteamForgeLib.ProcessManager)
print(SteamForgeLib.ShortcutManager)
```

## File IO utilities

The library includes `FileIOManager.safe_write_replace()`, which writes data to a temp file and atomically replaces the destination. This is used by the config and shortcut writers.

### Safe write example

```python
import os
import SteamForgeLib

path = "example/output/config.json"
os.makedirs(os.path.dirname(path), exist_ok=True)

SteamForgeLib.FileIOManager.safe_write_replace(
    path,
    "w",
    lambda fh: fh.write('{"demo": true}'),
    encoding="utf-8",
)

print(os.path.exists(path))
```

This is useful when you want a write to either fully complete or fail without leaving a partially written file behind.

## JSON configuration management

### Create a config

```python
import SteamForgeLib

config_path = "my_config.json"

SteamForgeLib.ConfigManager.create(
    config_path,
    initial_data={
        "settings": {
            "graphics": {
                "resolution": "1920x1080",
                "fullscreen": True,
            },
            "volume": 80,
        },
        "user": {
            "name": "PlayerOne",
        },
    },
    overwrite=True,
)
```

### Read a config

```python
import SteamForgeLib

config = SteamForgeLib.ConfigManager.read("my_config.json")
print(config)
```

### Write a config

```python
import SteamForgeLib

config = {
    "settings": {
        "graphics": {
            "resolution": "2560x1440",
            "fullscreen": False,
        },
        "volume": 90,
    }
}

SteamForgeLib.ConfigManager.write("my_config.json", config)
```

### Update nested values using dot paths

```python
import SteamForgeLib

updates = {
    "settings.graphics.resolution": "3840x2160",
    "settings.graphics.fullscreen": True,
    "user.name": "NewName",
    "settings.volume": 95,
}

SteamForgeLib.ConfigManager.update_values("my_config.json", updates)
print(SteamForgeLib.ConfigManager.read("my_config.json"))
```

This method splits keys on `.` and creates intermediate dictionaries as needed.

## Steam environment and installation detection

### Detect the default Steam install path

```python
import SteamForgeLib

steam_path = SteamForgeLib.SteamEnvironment.get_default_path()
print(steam_path)
```

The method checks a list of common Steam paths on Linux/macOS/Windows, and returns the first existing one.

### Parse loginusers.vdf

```python
import SteamForgeLib

try:
    accounts = SteamForgeLib.SteamEnvironment.parse_login_users()
    for acc in accounts:
        print(acc)
except SteamForgeLib.VDFParseError as e:
    print("Could not parse loginusers.vdf:", e)
```

### Parse from a custom VDF path

```python
import SteamForgeLib

custom_vdf = "/mnt/steam_backup/config/loginusers.vdf"

try:
    accounts = SteamForgeLib.SteamEnvironment.parse_login_users(custom_vdf)
    print(len(accounts), "account(s) found")
except SteamForgeLib.VDFParseError as e:
    print(e)
```

### Collect Steam library folders

```python
import SteamForgeLib

libraries = SteamForgeLib.SteamEnvironment.get_library_folders()
for lib in libraries:
    print(lib)
```

This reads `config/libraryfolders.vdf` when present and returns the base path plus any extra library folders.

### Scan installed games from `steamapps`

```python
import SteamForgeLib

games = SteamForgeLib.SteamEnvironment.get_installed_games()
for game in games:
    print({
        "AppID": game["AppID"],
        "Name": game["Name"],
        "InstallDir": game["InstallDir"],
        "LibraryPath": game["LibraryPath"],
    })
```

This scans all Steam library folders and parses `appmanifest_*.acf` files to build a list of installed official games.

## Process monitoring and launching

### Check whether Steam is running

```python
import SteamForgeLib

print(SteamForgeLib.ProcessManager.is_steam_running())
```

### Launch a Steam game by AppID

```python
import SteamForgeLib

SteamForgeLib.ProcessManager.launch_steam_game(730)
```

This opens the native Steam protocol launcher:

```text
steam://rungameid/730
```

### Launch a Windows executable with UMU

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

print("PID:", proc.pid)
```

The method creates a subprocess with environment variables like:

- `GAMEID`
- `PROTONPATH`
- `WINEPREFIX`

and passes the target executable plus any launch arguments.

### Failure example

```python
import SteamForgeLib

try:
    SteamForgeLib.ProcessManager.launch_with_umu("/path/not/real.exe")
except SteamForgeLib.UMUError as e:
    print("Launch failed:", e)
```

## Shortcuts management

Steam shortcuts are handled in `shortcuts.vdf`, which is a binary VDF structure.

### Get the default shortcuts.vdf path for a Steam user

```python
import SteamForgeLib

user_id_32 = 12345678
path = SteamForgeLib.ShortcutManager.get_path(user_id_32)
print(path)
```

This resolves to something like:

```text
~/.local/share/Steam/userdata/12345678/config/shortcuts.vdf
```

### Read all shortcuts

```python
import SteamForgeLib

steam_id_32 = 12345678

try:
    shortcuts = SteamForgeLib.ShortcutManager.read(steam_id_32)
    print(type(shortcuts))
    for idx, entry in shortcuts.items():
        print(idx, entry)
except SteamForgeLib.ShortcutError as e:
    print(e)
```

### Read from a custom shortcut file path

```python
import SteamForgeLib

custom_path = "/tmp/custom_shortcuts.vdf"

shortcuts = SteamForgeLib.ShortcutManager.read(12345678, vdf_path=custom_path)
print(shortcuts)
```

### Write a complete shortcut dictionary

```python
import SteamForgeLib

shortcut_dict = {
    "0": {
        "appname": "Example Game",
        "exe": '"/usr/games/example-game"',
        "StartDir": '"/usr/games"',
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
}

SteamForgeLib.ShortcutManager.write(12345678, shortcut_dict)
```

### Add a shortcut to an existing file

```python
import SteamForgeLib

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

SteamForgeLib.ShortcutManager.add(12345678, new_shortcut)
```

The `add()` method reads the current shortcuts, chooses the next numeric index, and writes the updated dictionary back.

## Local artwork discovery

### Look for local Steam art cache entries for a game

```python
import SteamForgeLib

art = SteamForgeLib.LocalArtworkManager.get_artwork(730)
print(art)
```

Example output:

```python
{
    "grid": "/home/user/.local/share/Steam/appcache/librarycache/730_library_600x900.jpg",
    "header": "/home/user/.local/share/Steam/appcache/librarycache/730_header.jpg",
    "logo": "/home/user/.local/share/Steam/appcache/librarycache/730_logo.png",
    "icon": "/home/user/.local/share/Steam/appcache/librarycache/730_icon.jpg",
}
```

### Use a custom Steam path

```python
import SteamForgeLib

art = SteamForgeLib.LocalArtworkManager.get_artwork(
    730,
    custom_steam_path="/path/to/custom/steam/installation",
)
print(art)
```

This searches the local Steam cache directory under:

```text
<SteamPath>/appcache/librarycache
```

and matches files such as:

- `730_library_600x900.jpg`
- `730_library_hero.jpg`
- `730_header.jpg`
- `730_logo.png`
- `730_icon.jpg`

## SteamGridDB client

The `SteamGridDBClient` class wraps SteamGridDB API calls.

### Search for a game by name

```python
import SteamForgeLib

api_key = "your_steamgriddb_api_key_here"

try:
    result = SteamForgeLib.SteamGridDBClient.search_game(api_key, "Hades")
    print(result)
except SteamForgeLib.SteamGridDBError as e:
    print(e)
```

This hits the autocomplete endpoint and returns the first matching result.

### Fetch artwork by AppID

```python
import SteamForgeLib

api_key = "your_steamgriddb_api_key_here"

try:
    images = SteamForgeLib.SteamGridDBClient.get_images_by_id(
        api_key,
        47540,
        image_type="grids",
    )
    for img in images[:5]:
        print(img.get("id"), img.get("width"), img.get("height"), img.get("url"))
except SteamForgeLib.SteamGridDBError as e:
    print(e)
```

### Fetch artwork from a game ID and inspect structure

```python
import SteamForgeLib

api_key = "your_steamgriddb_api_key_here"
images = SteamForgeLib.SteamGridDBClient.get_images_by_id(api_key, 730)
print(images[0].keys())
print(images[0])
```

The library expects a SteamGridDB API key and returns the JSON `data` array from the API response.

## GUI demo

The repo also includes a Qt-based demo GUI for testing the library interactively.

```bash
python3 SteamForgeLibGUI.py
```

The GUI includes tabs for:

- Steam process status and account parsing
- JSON config creation and editing
- Steam shortcut management
- UMU / Proton launch testing
- SteamGridDB lookup and preview

## Full method reference

### `FileIOManager.safe_write_replace(dest_path, mode, write_callback, encoding=None)`

Atomic write helper that writes to a temp file then replaces the destination.

### `ConfigManager.create(file_path, initial_data=None, overwrite=False)`

Creates a JSON config file and returns the path.

### `ConfigManager.read(file_path)`

Loads JSON and returns a Python dictionary.

### `ConfigManager.write(file_path, data, indent=4)`

Writes a JSON file. This also uses the atomic replacement helper.

### `ConfigManager.update_values(file_path, updates)`

Applies nested dot-path updates like:

```python
{"settings.graphics.resolution": "1920x1080"}
```

### `SteamEnvironment.get_default_path()`

Gets the first existing Steam installation directory from likely native paths.

### `SteamEnvironment.parse_login_users(vdf_path=None)`

Returns a list of dictionaries with:

- `SteamID64`
- `SteamID32`
- `AccountName`
- `PersonaName`
- `RememberPassword`
- `AutoLogin`
- `Timestamp`

### `SteamEnvironment.get_library_folders(base_steam_path=None)`

Lists all known library roots from `libraryfolders.vdf` plus the base Steam instance.

### `SteamEnvironment.get_installed_games(base_steam_path=None)`

Scans `steamapps` and returns installed games as dictionaries with keys like:

- `AppID`
- `Name`
- `InstallDir`
- `ManifestPath`
- `LibraryPath`

### `ProcessManager.is_steam_running()`

Returns `True` if a Steam process is active.

### `ProcessManager.launch_steam_game(app_id)`

Opens the Steam protocol URL for the app ID.

### `ProcessManager.launch_with_umu(target_exe, umu_run_path="umu-run", proton_version="", game_id="0", prefix_path="", launch_options=None, log_output=True)`

Launches a Windows executable through `umu-run` with environment variables.

### `ShortcutManager.get_path(steam_id_32, base_steam_path=None)`

Builds the path to that user’s `shortcuts.vdf` file.

### `ShortcutManager.read(steam_id_32, vdf_path=None)`

Reads and returns the dictionary stored in `shortcuts.vdf`.

### `ShortcutManager.write(steam_id_32, shortcuts_dict, vdf_path=None)`

Writes a full shortcut dictionary to disk.

### `ShortcutManager.add(steam_id_32, shortcut_data, vdf_path=None)`

Appends a shortcut entry and re-saves the file.

### `LocalArtworkManager.get_artwork(app_id, custom_steam_path=None)`

Returns a dictionary mapping art types to file paths.

### `SteamGridDBClient.search_game(api_key, game_name)`

Performs autocomplete lookup and returns the first result object.

### `SteamGridDBClient.get_images_by_id(api_key, game_id, image_type="grids")`

Fetches the artwork data for a Steam game by numeric ID.

## Exception types

The library defines custom exceptions for clearer failure handling:

```python
import SteamForgeLib

try:
    SteamForgeLib.SteamEnvironment.parse_login_users("/nonexistent/path/loginusers.vdf")
except SteamForgeLib.VDFParseError as e:
    print("VDF parsing issue:", e)
except SteamForgeLib.ConfigError as e:
    print("Config issue:", e)
except SteamForgeLib.UMUError as e:
    print("UMU issue:", e)
except SteamForgeLib.ShortcutError as e:
    print("Shortcut issue:", e)
except SteamForgeLib.SteamGridDBError as e:
    print("SteamGridDB issue:", e)
```

Available exception classes:

- `SteamForgeError`
- `VDFParseError`
- `ConfigError`
- `ProcessMonitorError`
- `UMUError`
- `ShortcutError`
- `SteamGridDBError`

## Practical notes

- The core library is intentionally lightweight and does not require the Qt GUI package.
- The GUI is a testing and debugging tool; it is not required for library usage.
- The code uses atomic file writes to reduce corruption when modifying JSON or VDF files.
- Many methods accept a custom path argument so they can work with non-standard Steam installations.

## Example: end-to-end flow

```python
import SteamForgeLib

# 1) Find Steam install path
steam_root = SteamForgeLib.SteamEnvironment.get_default_path()
print("Steam root:", steam_root)

# 2) Parse accounts
accounts = SteamForgeLib.SteamEnvironment.parse_login_users()
print("Accounts:", accounts)

# 3) Find libraries
libraries = SteamForgeLib.SteamEnvironment.get_library_folders(steam_root)
print("Libraries:", libraries)

# 4) Scan installed games
for game in SteamForgeLib.SteamEnvironment.get_installed_games(steam_root):
    print(game["Name"], game["AppID"])

# 5) Check Steam process status
print("Steam running?", SteamForgeLib.ProcessManager.is_steam_running())

# 6) Read shortcuts for a user
shortcut_data = SteamForgeLib.ShortcutManager.read(12345678)
print("Shortcut entries:", shortcut_data)

# 7) Find cached artwork for a title
art = SteamForgeLib.LocalArtworkManager.get_artwork(730, steam_root)
print("Artwork:", art)
```

This shows the main workflow the library is designed around: locate Steam, inspect user data, scan game manifests, work with shortcuts, and fetch artwork.

## Summary

SteamForgeLib is a small but practical library for scraping and managing Steam data and related files without depending on a large framework. The strongest areas are:

- Steam install discovery
- `loginusers.vdf` parsing
- JSON config management
- `shortcuts.vdf` editing
- game manifest scanning
- launching via Steam or UMU
- artwork discovery and SteamGridDB API access

If you want, I can also rewrite the README into a more polished GitHub style with a stronger intro, screenshots section, and an API summary table.
