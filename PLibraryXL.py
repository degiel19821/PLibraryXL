#!/usr/bin/env python3
import os
import json
import vdf

class PLibraryXL:
    """
    PLibraryXL combines Steam loginusers.vdf parsing and JSON configuration management
    into a single, clean object-oriented Python library.
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