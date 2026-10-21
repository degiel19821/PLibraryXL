# Config Manager

A robust, lightweight Python utility and Command-Line Interface (CLI) for reading, creating, and updating JSON configuration files with support for nested keys (via dot notation).

---

## Features

* **Create Configurations**: Initialize a new JSON configuration file using external template files or JSON strings.
* **Read Configurations**: View your configuration data as formatted JSON, with optional `--json` wrapper output.
* **Update & Set Values**: Easily update top-level or deeply nested configuration keys using dot notation (e.g., `graphics.resolution`).
* **Smart Type Parsing**: Automatically converts CLI string values into booleans (`true`/`false`), integers, floats, or strings.
* **Safe Operations**: Includes automatic directory creation, absolute path resolution, and comprehensive error handling.

---

## Terminal Usage (CLI)

### 1. Create a Configuration File
You must provide initial configuration data externally using the `-d` / `--data` argument (either as a raw JSON string or a path to a template `.json` file).

* **Using a raw JSON string:**
  ```bash
  python3 config_manager.py create --file config.json --data '{"app_name": "SteamTool", "version": "1.0", "debug_mode": false}'
  ```

* **Using an external template file (`template.json`):**
  ```bash
  python3 config_manager.py create --file config.json --data template.json
  ```

* **Force overwrite if the file already exists:**
  ```bash
  python3 config_manager.py create --file config.json --data '{"app": "Tool"}' --overwrite
  ```

### 2. Read Configuration Data
* **Standard output:**
  ```bash
  python3 config_manager.py read --file config.json
  ```

* **With structured `--json` wrapper output:**
  ```bash
  python3 config_manager.py read --file config.json --json
  ```

### 3. Update / Set Configuration Values
Supports dot notation for modifying nested dictionaries.

* **Update a top-level key:**
  ```bash
  python3 config_manager.py set --file config.json --key "debug_mode" --value true
  ```

* **Update a nested key:**
  ```bash
  python3 config_manager.py set --file config.json --key "graphics.resolution" --value "2560x1440"
  ```

---

## Library Usage (Python Integration)

Import the functions directly into your own Python scripts:

```python
from config_manager import create_config, read_config, update_config_value

# 1. Define configuration defaults externally
initial_settings = {
    "app_name": "ExpeditionUtility",
    "version": "1.0.0",
    "settings": {
        "theme": "dark",
        "volume": 80
    }
}

# 2. Create the configuration file
success, abs_path, error = create_config(
    file_path="config.json",
    initial_data=initial_settings,
    overwrite=True
)

if success:
    print(f"Config created at: {abs_path}")

# 3. Read configuration data
success, data, error = read_config("config.json")
if success:
    print("Current config:", data)

# 4. Update configuration values (automatically saves changes)
update_config_value("config.json", "settings.volume", 95)
```
