#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse
import vdf
import psutil

class PLibraryXL:
    """
    PLibraryXL combines Steam loginusers.vdf parsing, JSON configuration management,
    binary Steam shortcuts management, SteamGridDB API integration, and process 
    monitoring into a single, clean object-oriented Python library.
    """

    @staticmethod
    def _safe_bool(value) -> bool:
        """Safely coerces VDF values (strings, ints, or booleans) into a boolean."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            return False

    @classmethod
    def parse_steam_login_users(cls, vdf_path: str = "/home/deck/.local/share/Steam/config/loginusers.vdf"):
        """
        Reads and parses the Steam loginusers.vdf file.
        Returns a tuple: (success: bool, accounts: list, count: int, error_message: str | None)
        """
        if not os.path.exists(vdf_path):
            return False, [], 0, f"loginusers.vdf could not be found at: {vdf_path}"

        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)

            accounts = []
            users_dict = data.get("users", {})
            
            for steam_id_str, details in users_dict.items():
                try:
                    steam_id_64 = int(steam_id_str)
                except ValueError:
                    continue

                steam_id_32 = steam_id_64 & 0xFFFFFFFF

                account_info = {
                    "SteamID64": steam_id_64,
                    "SteamID32": steam_id_32,
                    "AccountName": details.get("AccountName", "Unknown"),
                    "PersonaName": details.get("PersonaName", "Unknown"),
                    "RememberPassword": cls._safe_bool(details.get("RememberPassword")),
                    "AutoLogin": cls._safe_bool(details.get("AutoLogin")),
                    "Timestamp": details.get("timestamp")
                }
                accounts.append(account_info)

            return True, accounts, len(accounts), None

        except PermissionError:
            return False, [], 0, f"Permission denied when trying to read: {vdf_path}"
        except Exception as e:
            return False, [], 0, f"An unexpected error occurred while parsing VDF: {str(e)}"

    @classmethod
    def create_config(cls, file_path: str, initial_data: dict = None, overwrite: bool = False):
        """
        Creates a configuration file using externally provided initial_data.
        Returns a tuple: (success: bool, absolute_path: str | None, error_message: str | None)
        """
        abs_path = os.path.abspath(file_path)

        if os.path.exists(abs_path) and not overwrite:
            return False, abs_path, f"Config file already exists at: {abs_path} (set overwrite=True to replace)"
        
        if initial_data is None:
            initial_data = {}

        try:
            dir_name = os.path.dirname(abs_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
                
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
            return True, abs_path, None
        except Exception as e:
            return False, abs_path, f"Error creating config file: {str(e)}"

    @classmethod
    def read_config(cls, file_path: str):
        """Reads and parses a JSON config file."""
        if not os.path.exists(file_path):
            return False, {}, f"Config file not found: {file_path}"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return True, data, None
        except json.JSONDecodeError as e:
            return False, {}, f"Invalid JSON format: {str(e)}"
        except Exception as e:
            return False, {}, f"Error reading config: {str(e)}"

    @classmethod
    def write_config(cls, file_path: str, data: dict, indent: int = 4):
        """Writes configuration data back to the JSON file."""
        try:
            abs_path = os.path.abspath(file_path)
            dir_name = os.path.dirname(abs_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
                
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True, None
        except Exception as e:
            return False, f"Error writing config: {str(e)}"

    @classmethod
    def update_config_value(cls, file_path: str, key_path: str, value):
        """Updates a single value in an existing config. Supports dot notation for nested keys."""
        success, config, error = cls.read_config(file_path)
        if not success:
            return False, f"Cannot update config: {error}"

        keys = key_path.split(".")
        curr = config
        for key in keys[:-1]:
            if key not in curr or not isinstance(curr[key], dict):
                curr[key] = {}
            curr = curr[key]

        curr[keys[-1]] = value
        return cls.write_config(file_path, config)

    @classmethod
    def update_config_values(cls, file_path: str, updates: dict):
        """
        Updates multiple values at once in an existing config file.
        Accepts a dictionary mapping dot-notation key paths to their new values.
        Returns a tuple: (success: bool, error_message: str | None)
        """
        success, config, error = cls.read_config(file_path)
        if not success:
            return False, f"Cannot update config: {error}"

        try:
            for key_path, value in updates.items():
                keys = key_path.split(".")
                curr = config
                for key in keys[:-1]:
                    if key not in curr or not isinstance(curr[key], dict):
                        curr[key] = {}
                    curr = curr[key]
                curr[keys[-1]] = value
            
            return cls.write_config(file_path, config)
        except Exception as e:
            return False, f"Error updating multiple config values: {str(e)}"

    @staticmethod
    def is_steam_running() -> bool:
        """
        Reliably checks if the main Steam client is currently running on the system
        by inspecting active OS processes using `psutil`.
        """
        steam_process_names = {"steam", "steam.exe"}
        try:
            for proc in psutil.process_iter(attrs=["name"]):
                try:
                    name = proc.info.get("name")
                    if name and name.lower() in steam_process_names:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        except Exception:
            return False

    # ==========================================
    # STEAM SHORTCUTS MANAGEMENT (shortcuts.vdf)
    # ==========================================

    @staticmethod
    def get_shortcuts_path(steam_id_32: int, base_steam_path: str = "/home/deck/.local/share/Steam") -> str:
        """Returns the absolute path to a user's shortcuts.vdf file based on their 32-bit Steam ID."""
        return os.path.join(base_steam_path, "userdata", str(steam_id_32), "config", "shortcuts.vdf")

    @classmethod
    def read_shortcuts(cls, steam_id_32: int, vdf_path: str = None):
        """
        Reads and parses the binary shortcuts.vdf file for a specific 32-bit Steam user ID.
        Returns a tuple: (success: bool, shortcuts: dict, count: int, error_message: str | None)
        """
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        if not os.path.exists(path):
            return False, {}, 0, f"shortcuts.vdf not found for user ID {steam_id_32} at: {path}"

        try:
            with open(path, "rb") as f:
                data = vdf.binary_load(f)
            
            shortcuts = data.get("shortcuts", {})
            return True, shortcuts, len(shortcuts), None
        except PermissionError:
            return False, {}, 0, f"Permission denied when trying to read shortcuts at: {path}"
        except Exception as e:
            return False, {}, 0, f"An unexpected error occurred while parsing shortcuts.vdf: {str(e)}"

    @classmethod
    def write_shortcuts(cls, steam_id_32: int, shortcuts_dict: dict, vdf_path: str = None):
        """Writes configuration data back to the binary shortcuts.vdf file."""
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        try:
            dir_name = os.path.dirname(path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            
            payload = {"shortcuts": shortcuts_dict}
            with open(path, "wb") as f:
                vdf.binary_dump(payload, f)
            return True, None
        except Exception as e:
            return False, f"Error writing shortcuts file: {str(e)}"

    @classmethod
    def add_shortcut(cls, steam_id_32: int, shortcut_data: dict, vdf_path: str = None):
        """
        Adds a new non-Steam shortcut for the specified 32-bit Steam user.
        Returns a tuple: (success: bool, error_message: str | None)
        """
        success, shortcuts, _, error = cls.read_shortcuts(steam_id_32, vdf_path)
        if not success and "not found" not in str(error):
            return False, f"Failed to read existing shortcuts: {error}"
        
        if not success:
            shortcuts = {}

        existing_indices = [int(k) for k in shortcuts.keys() if k.isdigit()]
        next_index = str(max(existing_indices) + 1) if existing_indices else "0"

        shortcuts[next_index] = shortcut_data
        return cls.write_shortcuts(steam_id_32, shortcuts, vdf_path)

    @classmethod
    def edit_shortcut(cls, steam_id_32: int, index: int, updates: dict, vdf_path: str = None):
        """
        Edits an existing shortcut by its numeric index.
        Returns a tuple: (success: bool, error_message: str | None)
        """
        success, shortcuts, _, error = cls.read_shortcuts(steam_id_32, vdf_path)
        if not success:
            return False, f"Cannot edit shortcut: {error}"

        idx_str = str(index)
        if idx_str not in shortcuts:
            return False, f"Shortcut with index {index} does not exist."

        shortcuts[idx_str].update(updates)
        return cls.write_shortcuts(steam_id_32, shortcuts, vdf_path)

    @classmethod
    def remove_shortcut(cls, steam_id_32: int, index: int, vdf_path: str = None):
        """
        Removes a shortcut by its numeric index and automatically re-indexes 
        the remaining entries sequentially as Steam expects.
        Returns a tuple: (success: bool, error_message: str | None)
        """
        success, shortcuts, _, error = cls.read_shortcuts(steam_id_32, vdf_path)
        if not success:
            return False, f"Cannot remove shortcut: {error}"

        idx_str = str(index)
        if idx_str not in shortcuts:
            return False, f"Shortcut with index {index} does not exist."

        sorted_keys = sorted([k for k in shortcuts.keys() if k.isdigit()], key=int)
        new_shortcuts = {}
        new_idx = 0

        for k in sorted_keys:
            if k == idx_str:
                continue
            new_shortcuts[str(new_idx)] = shortcuts[k]
            new_idx += 1

        return cls.write_shortcuts(steam_id_32, new_shortcuts, vdf_path)

    # ==========================================
    # STEAMGRIDDB API INTEGRATION
    # ==========================================

    @classmethod
    def search_sgdb_game(cls, api_key: str, game_name: str):
        """
        Searches SteamGridDB for a game by name.
        Returns a tuple: (success: bool, game_data: dict | None, error_message: str | None)
        """
        encoded_name = urllib.parse.quote(game_name)
        url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{encoded_name}"
        
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "PLibraryXL/1.0"})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    return True, data["data"][0], None
                return False, None, "No games found matching that name."
        except Exception as e:
            return False, None, f"SteamGridDB search error: {str(e)}"

    @classmethod
    def get_sgdb_images_by_id(cls, api_key: str, game_id: int, image_type: str = "grids"):
        """
        Retrieves images for a specific SteamGridDB game ID.
        image_type can be: 'grids', 'heroes', 'logos', or 'icons'.
        Returns a tuple: (success: bool, images: list, error_message: str | None)
        """
        url = f"https://www.steamgriddb.com/api/v2/{image_type}/game/{game_id}"
        
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "PLibraryXL/1.0"})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("success"):
                    return True, data.get("data", []), None
                return False, [], f"Failed to retrieve {image_type}."
        except Exception as e:
            return False, [], f"SteamGridDB image retrieval error: {str(e)}"

    @classmethod
    def get_sgdb_images_by_name(cls, api_key: str, game_name: str, image_type: str = "grids"):
        """
        Convenience method that resolves a game name to an ID and fetches its images.
        Returns a tuple: (success: bool, images: list, error_message: str | None)
        """
        success, game_data, error = cls.search_sgdb_game(api_key, game_name)
        if not success:
            return False, [], f"Game resolution failed: {error}"

        game_id = game_data.get("id")
        if not game_id:
            return False, [], "Invalid game data returned from search."

        return cls.get_sgdb_images_by_id(api_key, game_id, image_type)
