# Steam Login Users Parser

`parse_steam_login_users.py` is a lightweight Python utility designed to parse Steam's `loginusers.vdf` configuration file. It extracts stored user account details—such as Steam IDs (both 64-bit and 32-bit), account names, persona names, and login preferences—and presents them in a clean, readable format or as JSON.

---

## Features

- **VDF Parsing:** Safely reads and parses Steam's Valve Data Format (VDF) configuration files.
- **Dual Identifiers:** Automatically calculates both `SteamID64` and `SteamID32` for each account.
- **Flexible Output:** Prints formatted text output or structured JSON for easy scripting integration.
- **Dual-Mode Usage:** Use it directly as a command-line terminal tool or import it as a Python library into your own projects.

---

## Prerequisites

This script relies on the `vdf` Python package. Install it via pip before running the script:

```bash
pip install vdf
```

---

## Usage in the Terminal

You can run the script directly from your terminal. By default, it looks for Steam's standard path on a Steam Deck (`/home/deck/.local/share/Steam/config/loginusers.vdf`).

### Basic Usage
Print all discovered accounts in a human-readable format:
```bash
python parse_steam_login_users.py
```

### Custom Path Usage
If your Steam configuration is located in a different directory (e.g., standard Linux desktop or custom path), specify it with the `-p` or `--path` flag:
```bash
python parse_steam_login_users.py -p /path/to/your/loginusers.vdf
```

### JSON Output
To output the results as JSON (useful for automation or parsing with tools like `jq`), use the `--json` flag:
```bash
python parse_steam_login_users.py --json
```

---

## Usage as a Library

You can import `parse_steam_login_users` into your own Python scripts and handle the parsed account data programmatically.

### Example Code

```python
from parse_steam_login_users import parse_steam_login_users

# Call the function (optionally pass a custom path)
success, accounts, count, error = parse_steam_login_users()

if not success:
    print(f"Failed to parse accounts: {error}")
else:
    print(f"Successfully loaded {count} account(s):\n")
    for account in accounts:
        print(f"User: {account['AccountName']} (Persona: {account['PersonaName']})")
        print(f"SteamID64: {account['SteamID64']}")
        print(f"SteamID32: {account['SteamID32']}")
        print(f"Auto-login enabled: {account['AutoLogin']}")
        print("-" * 30)
```

### Return Signature

The `parse_steam_login_users(vdf_path)` function returns a 4-item tuple:
1. `success` (`bool`): `True` if parsing succeeded, `False` otherwise.
2. `accounts` (`list`): A list of dictionaries containing account attributes (`SteamID64`, `SteamID32`, `AccountName`, `PersonaName`, `RememberPassword`, `AutoLogin`, `Timestamp`).
3. `count` (`int`): The total number of accounts found.
4. `error_message` (`str | None`): An error description string if `success` is `False`, otherwise `None`.