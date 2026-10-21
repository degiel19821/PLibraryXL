# PLibraryXL

`PLibraryXL` is a robust, lightweight, object-oriented Python library that combines Steam `loginusers.vdf` parsing and JSON configuration management into a single, cohesive class. It is designed to be easily imported into any Python project without requiring any command-line interface (CLI) boilerplate.

---

## Features

- **Steam VDF Parsing:** Safely reads and parses Steam's `loginusers.vdf` configuration files.
- **Dual Identifiers:** Automatically calculates both `SteamID64` and `SteamID32` for each discovered account.
- **JSON Configuration Management:** Create, read, write, and update configuration files seamlessly.
- **Nested Key Support:** Modify deeply nested configuration keys using dot notation (e.g., `settings.theme`).
- **Batch Updates:** Update multiple top-level or nested configuration values simultaneously in a single read-and-write pass.
- **Pure Library Design:** Completely independent of command-line arguments or `argparse`, making it purely modular for programmatic integration.

---

## Installation & Prerequisites

This library relies on the `vdf` package for parsing Steam configuration files. Install it via pip:

```bash
pip install vdf
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

### 3. Reading Configurations

```python
from plibrary_xl import PLibraryXL

success, data, error = PLibraryXL.read_config("config.json")
if success:
    print("Current configuration:", data)
else:
    print(f"Error reading config: {error}")
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
