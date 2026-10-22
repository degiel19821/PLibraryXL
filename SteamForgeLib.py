#!/usr/bin/env python3
import os
import subprocess
import json
import urllib.request
import urllib.parse
import urllib.error
import tempfile
import vdf
import psutil

class SteamForgeError(Exception):
    """Base exception for SteamForgeLib."""
    pass

class VDFParseError(SteamForgeError):
    """Raised when there is an issue parsing VDF files."""
    pass

class ConfigError(SteamForgeError):
    """Raised when there is an issue reading or writing configurations."""
    pass

class ProcessMonitorError(SteamForgeError):
    """Raised when process monitoring fails."""
    pass

class UMUError(SteamForgeError):
    """Raised when launching with UMU fails."""
    pass

class ShortcutError(SteamForgeError):
    """Raised when managing shortcuts fails."""
    pass

class SteamGridDBError(SteamForgeError):
    """Raised when SteamGridDB API integration fails."""
    pass


class SteamForgeLib:
    """
    SteamForgeLib combines Steam loginusers.vdf parsing, JSON configuration management,
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
    def parse_steam_login_users(cls, vdf_path: str = "/home/deck/.local/share/Steam/config/loginusers.vdf") -> list:
        """
        Reads and parses the Steam loginusers.vdf file.
        Returns a list of accounts. Raises VDFParseError on failure.
        """
        if not os.path.exists(vdf_path):
            raise VDFParseError(f"loginusers.vdf could not be found at: {vdf_path}")

        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)
        except PermissionError:
            raise VDFParseError(f"Permission denied when trying to read: {vdf_path}")
        except (SyntaxError, ValueError, AttributeError) as e:
            raise VDFParseError(f"Corrupted or invalid VDF format: {str(e)}")

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

        return accounts

    @classmethod
    def create_config(cls, file_path: str, initial_data: dict = None, overwrite: bool = False) -> str:
        """
        Creates a configuration file using externally provided initial_data.
        Returns the absolute path. Raises ConfigError on failure.
        """
        abs_path = os.path.abspath(file_path)

        if os.path.exists(abs_path) and not overwrite:
            raise ConfigError(f"Config file already exists at: {abs_path} (set overwrite=True to replace)")
        
        if initial_data is None:
            initial_data = {}

        try:
            dir_name = os.path.dirname(abs_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
                
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as temp_file:
                json.dump(initial_data, temp_file, indent=4, ensure_ascii=False)
                temp_path = temp_file.name
                
            os.replace(temp_path, abs_path)
            return abs_path
        except (PermissionError, OSError) as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            raise ConfigError(f"Error creating config file: {str(e)}")

    @classmethod
    def read_config(cls, file_path: str) -> dict:
        """Reads and parses a JSON config file. Raises ConfigError on failure."""
        if not os.path.exists(file_path):
            raise ConfigError(f"Config file not found: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON format: {str(e)}")
        except PermissionError as e:
            raise ConfigError(f"Permission denied: {str(e)}")

    @classmethod
    def write_config(cls, file_path: str, data: dict, indent: int = 4) -> None:
        """Writes configuration data back to the JSON file atomically."""
        try:
            abs_path = os.path.abspath(file_path)
            dir_name = os.path.dirname(abs_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
                
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as temp_file:
                json.dump(data, temp_file, indent=indent, ensure_ascii=False)
                temp_path = temp_file.name

            os.replace(temp_path, abs_path)
        except (PermissionError, OSError, TypeError) as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            raise ConfigError(f"Error writing config: {str(e)}")

    @classmethod
    def update_config_value(cls, file_path: str, key_path: str, value) -> None:
        """Updates a single value in an existing config. Supports dot notation for nested keys."""
        config = cls.read_config(file_path)

        keys = key_path.split(".")
        curr = config
        for key in keys[:-1]:
            if key not in curr or not isinstance(curr[key], dict):
                curr[key] = {}
            curr = curr[key]

        curr[keys[-1]] = value
        cls.write_config(file_path, config)

    @classmethod
    def update_config_values(cls, file_path: str, updates: dict) -> None:
        """
        Updates multiple values at once in an existing config file.
        Accepts a dictionary mapping dot-notation key paths to their new values.
        """
        config = cls.read_config(file_path)

        for key_path, value in updates.items():
            keys = key_path.split(".")
            curr = config
            for key in keys[:-1]:
                if key not in curr or not isinstance(curr[key], dict):
                    curr[key] = {}
                curr = curr[key]
            curr[keys[-1]] = value
        
        cls.write_config(file_path, config)

    # ==========================================
    # UMU / PROTON LAUNCHER INTEGRATION
    # ==========================================

    @classmethod
    def launch_with_umu(
        cls,
        target_exe: str,
        umu_run_path: str = "umu-run",
        proton_version: str = "",
        game_id: str = "0",
        prefix_path: str = "",
        launch_options: list = None,
        log_output: bool = True
    ) -> subprocess.Popen:
        """
        Directly launches a Windows executable using umu-launcher (umu-run) with custom parameters.
        Raises UMUError on failure.
        """
        if launch_options is None:
            launch_options = []
            
        exe_path = os.path.abspath(target_exe)
        if not os.path.exists(exe_path):
            raise UMUError(f"Target executable not found: {target_exe}")
        if not os.path.isfile(exe_path):
            raise UMUError(f"Target path is not a file: {target_exe}")

        if prefix_path:
            prefix_dir = os.path.dirname(os.path.abspath(prefix_path))
            if prefix_dir and not os.path.exists(prefix_dir):
                raise UMUError(f"Parent directory for WINEPREFIX does not exist: {prefix_dir}")

        env = os.environ.copy()
        if game_id:
            env["GAMEID"] = str(game_id)
        if proton_version:
            env["PROTONPATH"] = str(proton_version)
        if prefix_path:
            env["WINEPREFIX"] = str(prefix_path)
            
        cmd = [umu_run_path, exe_path] + launch_options
        
        try:
            stdout_dest = subprocess.PIPE if log_output else None
            stderr_dest = subprocess.PIPE if log_output else None

            process = subprocess.Popen(
                cmd, 
                env=env,
                stdout=stdout_dest,
                stderr=stderr_dest,
                start_new_session=True
            )
            return process

        except FileNotFoundError:
            raise UMUError(f"The umu-run binary ('{umu_run_path}') could not be found. Ensure it is installed and in your PATH.")
        except PermissionError:
            raise UMUError(f"Permission denied when attempting to execute: {umu_run_path}")
        except OSError as e:
            raise UMUError(f"OS error launching with umu: {str(e)}")

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
        except psutil.Error as e:
            raise ProcessMonitorError(f"Failed to read OS process table: {str(e)}")

    # ==========================================
    # STEAM SHORTCUTS MANAGEMENT (shortcuts.vdf)
    # ==========================================

    @staticmethod
    def get_shortcuts_path(steam_id_32: int, base_steam_path: str = "/home/deck/.local/share/Steam") -> str:
        """Returns the absolute path to a user's shortcuts.vdf file based on their 32-bit Steam ID."""
        return os.path.join(base_steam_path, "userdata", str(steam_id_32), "config", "shortcuts.vdf")

    @classmethod
    def read_shortcuts(cls, steam_id_32: int, vdf_path: str = None) -> dict:
        """
        Reads and parses the binary shortcuts.vdf file for a specific 32-bit Steam user ID.
        Raises ShortcutError on failure.
        """
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        if not os.path.exists(path):
            raise ShortcutError(f"shortcuts.vdf not found for user ID {steam_id_32} at: {path}")

        try:
            with open(path, "rb") as f:
                data = vdf.binary_load(f)
            
            return data.get("shortcuts", {})
        except PermissionError:
            raise ShortcutError(f"Permission denied when trying to read shortcuts at: {path}")
        except (SyntaxError, ValueError, AttributeError) as e:
            raise ShortcutError(f"Corrupted binary shortcuts.vdf format: {str(e)}")

    @classmethod
    def write_shortcuts(cls, steam_id_32: int, shortcuts_dict: dict, vdf_path: str = None) -> None:
        """Writes configuration data back to the binary shortcuts.vdf file atomically."""
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        try:
            dir_name = os.path.dirname(path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            
            payload = {"shortcuts": shortcuts_dict}
            
            with tempfile.NamedTemporaryFile("wb", dir=dir_name, delete=False) as temp_file:
                vdf.binary_dump(payload, temp_file)
                temp_path = temp_file.name

            os.replace(temp_path, path)
        except (PermissionError, OSError, ValueError) as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            raise ShortcutError(f"Error writing shortcuts file: {str(e)}")

    @classmethod
    def add_shortcut(cls, steam_id_32: int, shortcut_data: dict, vdf_path: str = None) -> None:
        """
        Adds a new non-Steam shortcut for the specified 32-bit Steam user.
        """
        try:
            shortcuts = cls.read_shortcuts(steam_id_32, vdf_path)
        except ShortcutError as e:
            if "not found" in str(e):
                shortcuts = {}
            else:
                raise
        
        existing_indices = [int(k) for k in shortcuts.keys() if k.isdigit()]
        next_index = str(max(existing_indices) + 1) if existing_indices else "0"

        shortcuts[next_index] = shortcut_data
        cls.write_shortcuts(steam_id_32, shortcuts, vdf_path)

    @classmethod
    def edit_shortcut(cls, steam_id_32: int, index: int, updates: dict, vdf_path: str = None) -> None:
        """
        Edits an existing shortcut by its numeric index.
        """
        shortcuts = cls.read_shortcuts(steam_id_32, vdf_path)

        idx_str = str(index)
        if idx_str not in shortcuts:
            raise ShortcutError(f"Shortcut with index {index} does not exist.")

        shortcuts[idx_str].update(updates)
        cls.write_shortcuts(steam_id_32, shortcuts, vdf_path)

    @classmethod
    def remove_shortcut(cls, steam_id_32: int, index: int, vdf_path: str = None) -> None:
        """
        Removes a shortcut by its numeric index and automatically re-indexes 
        the remaining entries sequentially as Steam expects.
        """
        shortcuts = cls.read_shortcuts(steam_id_32, vdf_path)

        idx_str = str(index)
        if idx_str not in shortcuts:
            raise ShortcutError(f"Shortcut with index {index} does not exist.")

        sorted_keys = sorted([k for k in shortcuts.keys() if k.isdigit()], key=int)
        new_shortcuts = {}
        new_idx = 0

        for k in sorted_keys:
            if k == idx_str:
                continue
            new_shortcuts[str(new_idx)] = shortcuts[k]
            new_idx += 1

        cls.write_shortcuts(steam_id_32, new_shortcuts, vdf_path)

    # ==========================================
    # STEAMGRIDDB API INTEGRATION
    # ==========================================

    @classmethod
    def search_sgdb_game(cls, api_key: str, game_name: str) -> dict:
        """
        Searches SteamGridDB for a game by name.
        Raises SteamGridDBError on failure.
        """
        encoded_name = urllib.parse.quote(game_name)
        url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{encoded_name}"
        
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "SteamForgeLib/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    return data["data"][0]
                raise SteamGridDBError("No games found matching that name.")
        except urllib.error.HTTPError as e:
            raise SteamGridDBError(f"SteamGridDB API returned HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise SteamGridDBError(f"Network error connecting to SteamGridDB: {e.reason}")
        except json.JSONDecodeError as e:
            raise SteamGridDBError(f"Invalid JSON response from SteamGridDB: {str(e)}")

    @classmethod
    def get_sgdb_images_by_id(cls, api_key: str, game_id: int, image_type: str = "grids", 
                              sizes: list = None, filetypes: list = None) -> list:
        """
        Retrieves images for a specific SteamGridDB game ID with optional filtering 
        by dimensions/sizes (e.g., ["600x900", "342x482"]) and filetypes (e.g., ["png", "jpg", "ico"]).
        
        image_type can be: 'grids', 'heroes', 'logos', or 'icons'.
        Raises SteamGridDBError on failure.
        """
        url = f"https://www.steamgriddb.com/api/v2/{image_type}/game/{game_id}"
        
        # Standardized User-Agent header fix applied (SteamForgeLib.1.0 -> SteamForgeLib/1.0)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "SteamForgeLib/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not data.get("success"):
                    raise SteamGridDBError(f"Failed to retrieve {image_type}.")
                
                images = data.get("data", [])
                
                norm_sizes = {str(s).strip().lower() for s in sizes} if sizes else None
                norm_filetypes = {str(f).strip().lower().lstrip('.') for f in filetypes} if filetypes else None
                
                filtered_images = []
                for img in images:
                    if norm_sizes:
                        img_width = str(img.get("width", ""))
                        img_height = str(img.get("height", ""))
                        dim_str = f"{img_width}x{img_height}"
                        if dim_str not in norm_sizes and img_width not in norm_sizes and img_height not in norm_sizes:
                            continue
                            
                    if norm_filetypes:
                        img_url = img.get("url", "").lower()
                        ext = img_url.split("?")[0].split(".")[-1]
                        if ext not in norm_filetypes:
                            continue
                            
                    filtered_images.append(img)
                    
                return filtered_images
        except urllib.error.HTTPError as e:
            raise SteamGridDBError(f"SteamGridDB API returned HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise SteamGridDBError(f"Network error connecting to SteamGridDB: {e.reason}")
        except json.JSONDecodeError as e:
            raise SteamGridDBError(f"Invalid JSON response from SteamGridDB: {str(e)}")

    @classmethod
    def get_sgdb_images_by_name(cls, api_key: str, game_name: str, image_type: str = "grids",
                                sizes: list = None, filetypes: list = None) -> list:
        """
        Convenience method that resolves a game name to an ID and fetches its images 
        with optional filtering by sizes and filetypes.
        """
        game_data = cls.search_sgdb_game(api_key, game_name)

        game_id = game_data.get("id")
        if not game_id:
            raise SteamGridDBError("Invalid game data returned from search.")

        return cls.get_sgdb_images_by_id(api_key, game_id, image_type, sizes=sizes, filetypes=filetypes)