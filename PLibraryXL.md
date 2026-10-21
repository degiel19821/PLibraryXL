# PLibraryXL

`PLibraryXL` is a robust, lightweight, object-oriented Python library that combines Steam `loginusers.vdf` parsing, JSON configuration management, binary Steam shortcuts management (`shortcuts.vdf`), system process monitoring via `psutil`, and SteamGridDB API integration into a single, cohesive class. It is designed to be easily imported into any Python project without requiring any command-line interface (CLI) boilerplate.

---

## Features

- **Steam VDF Parsing:** Safely reads and parses Steam's `loginusers.vdf` configuration files, automatically deriving both `SteamID64` and `SteamID32`.
- **JSON Configuration Management:** Create, read, write, and update configuration files seamlessly with full support for nested keys via dot notation.
- **Batch Config Updates:** Update multiple top-level or nested configuration values simultaneously in a single read-and-write pass.
- **Binary Steam Shortcuts Management:** Read, write, add, edit, and remove non-Steam game shortcuts (`shortcuts.vdf`) with automatic sequential re-indexing.
- **Process Monitoring:** Reliably verify whether the main Steam client is currently active on the system using `psutil`.
- **SteamGridDB API Integration:** Search games and fetch custom assets (`grids`, `heroes`, `logos`, `icons`) directly from SteamGridDB using an API key.
- **Pure Library Design:** Completely independent of command-line arguments or `argparse`, making it purely modular for programmatic integration.

---

## Installation & Prerequisites

This library relies on the `vdf` and `psutil` packages. Install them via pip:

```bash
pip install vdf psutil
```

Place `plibrary_xl.py` in your project directory and import it as needed.

---

## API Reference & Usage

### 1. Parsing Steam Login Users

```python
from plibrary_xl import PLibraryXL

# Call the method (optionally pass a custom path to loginusers.vdf)
success, accounts, count, error = PLibraryXL.parse_steam_login_users()

if not success:
    print(f"Failed to parse accounts: {error}")
else:
    print(f"Successfully loaded {count} account(s):\n")
    for account in accounts:
        print(f"User: {account['AccountName']} (Persona: {account['PersonaName']})")
        print(f"SteamID64: {account['SteamID64']}")
        print(f"SteamID32: {account['SteamID32']}")
        print(f"Auto-login: {account['AutoLogin']}")
        print("-" * 30)
```

**Return Signature:**
The `parse_steam_login_users(vdf_path)` class method returns a 4-item tuple:
1. `success` (`bool`): `True` if parsing succeeded, `False` otherwise.
2. `accounts` (`list`): A list of dictionaries containing account attributes (`SteamID64`, `SteamID32`, `AccountName`, `PersonaName`, `RememberPassword`, `AutoLogin`, `Timestamp`).
3. `count` (`int`): The total number of accounts found.
4. `error_message` (`str | None`): An error description string if `success` is `False`, otherwise `None`.

---

### 2. Creating Configurations

```python
from plibrary_xl import PLibraryXL

initial_settings = {
    "app_name": "SteamTool",
    "version": "1.0.0",
    "settings": {
        "theme": "dark",
        "volume": 80
    }
}

success, abs_path, error = PLibraryXL.create_config(
    file_path="config.json",
    initial_data=initial_settings,
    overwrite=True
)

if success:
    print(f"Config created at: {abs_path}")
```

---

### 3. Reading & Writing Configurations

```python
from plibrary_xl import PLibraryXL

# Read config
success, data, error = PLibraryXL.read_config("config.json")
if success:
    print("Current configuration:", data)

# Write custom config dictionary directly
success, error = PLibraryXL.write_config("config.json", data)
```

---

### 4. Updating a Single Value (with Dot Notation)

```python
from plibrary_xl import PLibraryXL

# Updates a nested key using dot notation and automatically saves changes
success, error = PLibraryXL.update_config_value("config.json", "settings.volume", 95)
```

---

### 5. Updating Multiple Values at Once

```python
from plibrary_xl import PLibraryXL

# Update multiple top-level and nested keys in a single operation
success, error = PLibraryXL.update_config_values("config.json", {
    "version": "1.1.0",
    "settings.theme": "light",
    "settings.volume": 90,
    "settings.notifications": True  # Automatically creates missing nested dictionaries
})

if success:
    print("Successfully updated multiple values!")
else:
    print(f"Failed to update: {error}")
```

---

### 6. Process Monitoring

```python
from plibrary_xl import PLibraryXL

# Check if the Steam client is currently running
if PLibraryXL.is_steam_running():
    print("Steam client is currently running.")
else:
    print("Steam client is not running.")
```

---

### 7. Binary Steam Shortcuts Management (`shortcuts.vdf`)

#### Reading Shortcuts
```python
from plibrary_xl import PLibraryXL

steam_id_32 = 12345678  # Replace with actual 32-bit Steam ID
success, shortcuts, count, error = PLibraryXL.read_shortcuts(steam_id_32)

if success:
    print(f"Found {count} non-Steam shortcut(s):")
    for idx, shortcut in shortcuts.items():
        print(f"[{idx}] {shortcut.get('appname')} - {shortcut.get('exe')}")
```

#### Adding a Shortcut
```python
from plibrary_xl import PLibraryXL

new_shortcut = {
    "appname": "My Custom Game",
    "exe": "/path/to/game/executable",
    "StartDir": "/path/to/game/",
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
    "tags": {}
}

success, error = PLibraryXL.add_shortcut(12345678, new_shortcut)
if success:
    print("Shortcut added successfully!")
```

#### Editing a Shortcut
```python
from plibrary_xl import PLibraryXL

# Edit shortcut at index 0
success, error = PLibraryXL.edit_shortcut(12345678, index=0, updates={
    "LaunchOptions": "-fullscreen"
})
```

#### Removing a Shortcut
```python
from plibrary_xl import PLibraryXL

# Removes the shortcut and automatically re-indexes remaining entries
success, error = PLibraryXL.remove_shortcut(12345678, index=1)
if success:
    print("Shortcut removed and list re-indexed.")
```

---

### 8. SteamGridDB API Integration

#### Searching for a Game
```python
from plibrary_xl import PLibraryXL

api_key = "YOUR_STEAMGRIDDB_API_KEY"
success, game_data, error = PLibraryXL.search_sgdb_game(api_key, "Cyberpunk 2077")

if success:
    print(f"Found Game: {game_data.get('name')} (ID: {game_data.get('id')})")
else:
    print(f"Search failed: {error}")
```

#### Retrieving Images by Game ID
```python
from plibrary_xl import PLibraryXL

api_key = "YOUR_STEAMGRIDDB_API_KEY"
game_id = 123455  # Example SteamGridDB game ID
# image_type can be: 'grids', 'heroes', 'logos', or 'icons'
success, images, error = PLibraryXL.get_sgdb_images_by_id(api_key, game_id, image_type="grids")

if success:
    print(f"Retrieved {len(images)} grid image(s).")
    for img in images[:3]:
        print(f"Image URL: {img.get('url')}")
else:
    print(f"Image retrieval failed: {error}")
```

#### Retrieving Images by Game Name (Convenience Method)
```python
from plibrary_xl import PLibraryXL

api_key = "YOUR_STEAMGRIDDB_API_KEY"
success, images, error = PLibraryXL.get_sgdb_images_by_name(api_key, "Hades", image_type="logos")

if success:
    print(f"Retrieved {len(images)} logo image(s) for Hades.")
else:
    print(f"Failed: {error}")
```
