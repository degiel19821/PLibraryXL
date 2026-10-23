#!/usr/bin/env python3
import os
import subprocess
import json
import urllib.request
import urllib.parse
import urllib.error
import tempfile
import pathlib
import vdf
import psutil
import logging
from typing import List, Dict, Optional, Any, Callable

# Configure module logger
logger = logging.getLogger(__name__)

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
    def _safe_bool(value: Any) -> bool:
        """Safely coerces VDF values (strings, ints, or booleans) into a boolean."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _safe_write_replace(dest_path: str, mode: str, write_callback: Callable[[Any], None], encoding: Optional[str] = None) -> None:
        """Helper to write to a temp file and atomically replace the destination."""
        abs_path = os.path.abspath(dest_path)
        dir_name = os.path.dirname(abs_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode, dir=dir_name, delete=False, encoding=encoding) as temp_file:
                write_callback(temp_file)
                temp_path = temp_file.name
                
            os.replace(temp_path, abs_path)
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                try: 
                    os.remove(temp_path)
                except Exception: 
                    pass
            logger.error(f"Failed atomic write to {abs_path}: {e}")
            raise

    @staticmethod
    def get_default_steam_path() -> str:
        possible_paths = [
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/Library/Application Support/Steam"),
            "C:\\Program Files (x86)\\Steam",
            "C:\\Program Files\\Steam"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return os.path.expanduser("~/.local/share/Steam")

    @classmethod
    def parse_steam_login_users(cls, vdf_path: Optional[str] = None) -> List[Dict[str, Any]]:
        if vdf_path is None:
            vdf_path = os.path.join(cls.get_default_steam_path(), "config", "loginusers.vdf")

        if not os.path.exists(vdf_path):
            logger.error(f"loginusers.vdf missing at {vdf_path}")
            raise VDFParseError(f"loginusers.vdf could not be found at: {vdf_path}")

        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)
        except PermissionError:
            logger.error(f"Permission denied reading {vdf_path}")
            raise VDFParseError(f"Permission denied when trying to read: {vdf_path}")
        except (SyntaxError, ValueError, AttributeError) as e:
            logger.error(f"Corrupted VDF format in {vdf_path}: {e}")
            raise VDFParseError(f"Corrupted or invalid VDF format: {str(e)}")

        accounts = []
        users_dict = data.get("users", {})
        if not isinstance(users_dict, dict):
            return accounts
        
        for steam_id_str, details in users_dict.items():
            try:
                steam_id_64 = int(steam_id_str)
            except (ValueError, TypeError):
                continue

            steam_id_32 = steam_id_64 & 0xFFFFFFFF

            if not isinstance(details, dict):
                details = {}

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
    def create_config(cls, file_path: str, initial_data: Optional[Dict[str, Any]] = None, overwrite: bool = False) -> str:
        abs_path = os.path.abspath(file_path)

        if os.path.exists(abs_path) and not overwrite:
            logger.warning(f"Config creation skipped: {abs_path} already exists.")
            raise ConfigError(f"Config file already exists at: {abs_path} (set overwrite=True to replace)")
        
        if initial_data is None:
            initial_data = {}

        def _write(tf):
            json.dump(initial_data, tf, indent=4, ensure_ascii=False)
            
        try:
            cls._safe_write_replace(abs_path, "w", _write, encoding="utf-8")
            return abs_path
        except Exception as e:
            raise ConfigError(f"Error creating config file: {str(e)}")

    @classmethod
    def read_config(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            logger.error(f"Config file not found: {file_path}")
            raise ConfigError(f"Config file not found: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            raise ConfigError(f"Invalid JSON format: {str(e)}")
        except PermissionError as e:
            logger.error(f"Permission denied reading config {file_path}: {e}")
            raise ConfigError(f"Permission denied: {str(e)}")

    @classmethod
    def write_config(cls, file_path: str, data: Dict[str, Any], indent: int = 4) -> None:
        def _write(tf):
            json.dump(data, tf, indent=indent, ensure_ascii=False)
            
        try:
            cls._safe_write_replace(file_path, "w", _write, encoding="utf-8")
        except Exception as e:
            raise ConfigError(f"Error writing config: {str(e)}")

    @classmethod
    def update_config_value(cls, file_path: str, key_path: str, value: Any) -> None:
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
    def update_config_values(cls, file_path: str, updates: Dict[str, Any]) -> None:
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

    @classmethod
    def launch_with_umu(
        cls,
        target_exe: str,
        umu_run_path: str = "umu-run",
        proton_version: str = "",
        game_id: str = "0",
        prefix_path: str = "",
        launch_options: Optional[List[str]] = None,
        log_output: bool = True
    ) -> subprocess.Popen:
        if launch_options is None:
            sanitized_options = []
        else:
            sanitized_options = [str(opt) for opt in launch_options]
            
        exe_path = os.path.abspath(target_exe)
        if not os.path.exists(exe_path):
            logger.error(f"UMU Target missing: {target_exe}")
            raise UMUError(f"Target executable not found: {target_exe}")
        if not os.path.isfile(exe_path):
            logger.error(f"UMU Target is not a file: {target_exe}")
            raise UMUError(f"Target path is not a file: {target_exe}")

        if prefix_path:
            prefix_dir = os.path.dirname(os.path.abspath(prefix_path))
            if prefix_dir and not os.path.exists(prefix_dir):
                logger.error(f"UMU WINEPREFIX parent dir missing: {prefix_dir}")
                raise UMUError(f"Parent directory for WINEPREFIX does not exist: {prefix_dir}")

        env = os.environ.copy()
        if game_id:
            env["GAMEID"] = str(game_id)
        if proton_version:
            env["PROTONPATH"] = str(proton_version)
        if prefix_path:
            env["WINEPREFIX"] = str(prefix_path)
            
        cmd = [umu_run_path, exe_path] + sanitized_options
        
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
            logger.error(f"UMU binary not found: {umu_run_path}")
            raise UMUError(f"The umu-run binary ('{umu_run_path}') could not be found.")
        except PermissionError:
            logger.error(f"UMU permission denied: {umu_run_path}")
            raise UMUError(f"Permission denied when attempting to execute: {umu_run_path}")
        except OSError as e:
            logger.error(f"UMU OS Error: {e}")
            raise UMUError(f"OS error launching with umu: {str(e)}")

    @staticmethod
    def launch_steam_game(app_id: str | int) -> None:
        import platform
        app_id_str = str(app_id)
        url = f"steam://rungameid/{app_id_str}"
        
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.Popen(["xdg-open", url])
            elif system == "Windows":
                os.startfile(url)
            elif system == "Darwin":
                subprocess.Popen(["open", url])
            else:
                logger.error(f"Unsupported OS for Steam Protocol Launch: {system}")
                raise SteamForgeError(f"Unsupported operating system for protocol launch: {system}")
        except Exception as e:
            logger.error(f"Failed to launch Steam game {app_id_str}: {e}")
            raise SteamForgeError(f"Failed to launch Steam game AppID {app_id_str}: {str(e)}")

    @staticmethod
    def get_local_artwork(app_id: str | int, custom_steam_path: Optional[str] = None) -> Dict[str, str]:
        if custom_steam_path:
            steam_dir = pathlib.Path(custom_steam_path)
        else:
            steam_dir = pathlib.Path(SteamForgeLib.get_default_steam_path())
            
        cache_dir = steam_dir / "appcache" / "librarycache"
        if not cache_dir.exists():
            return {}
            
        found_artworks = {}
        app_id_str = str(app_id)
        
        patterns_with_id = [
            ("grid", f"{app_id_str}_library_600x900.jpg"),
            ("grid_2x", f"{app_id_str}_library_600x900_2x.jpg"),
            ("header", f"{app_id_str}_header.jpg"),
            ("library_header", f"{app_id_str}_library_header.jpg"),
            ("hero", f"{app_id_str}_library_hero.jpg"),
            ("hero_blur", f"{app_id_str}_library_hero_blur.jpg"),
            ("logo", f"{app_id_str}_logo.png"),
            ("icon", f"{app_id_str}_icon.jpg")
        ]
        
        clean_filenames = {
            "grid": "library_600x900.jpg",
            "grid_2x": "library_600x900_2x.jpg",
            "header": "header.jpg",
            "library_header": "library_header.jpg",
            "hero": "library_hero.jpg",
            "hero_blur": "library_hero_blur.jpg",
            "logo": "logo.png",
            "icon": "icon.jpg"
        }

        for path in cache_dir.rglob("*"):
            if not path.is_file():
                continue
            filename = path.name.lower()
            
            for art_type, pattern_name in patterns_with_id:
                if filename == pattern_name.lower():
                    found_artworks[art_type] = str(path)
                    
            if app_id_str in str(path):
                for art_type, clean_name in clean_filenames.items():
                    if filename == clean_name.lower():
                        found_artworks[art_type] = str(path)
                        
        return found_artworks

    @staticmethod
    def is_steam_running() -> bool:
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
            logger.error(f"Process Monitor error: {e}")
            raise ProcessMonitorError(f"Failed to read OS process table: {str(e)}")

    @staticmethod
    def get_shortcuts_path(steam_id_32: int, base_steam_path: Optional[str] = None) -> str:
        if base_steam_path is None:
            base_steam_path = SteamForgeLib.get_default_steam_path()
        return os.path.join(base_steam_path, "userdata", str(steam_id_32), "config", "shortcuts.vdf")

    @classmethod
    def read_shortcuts(cls, steam_id_32: int, vdf_path: Optional[str] = None) -> Dict[str, Any]:
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        if not os.path.exists(path):
            logger.warning(f"shortcuts.vdf not found for ID {steam_id_32} at {path}")
            raise ShortcutError(f"shortcuts.vdf not found for user ID {steam_id_32} at: {path}")

        try:
            with open(path, "rb") as f:
                data = vdf.binary_load(f)
            return data.get("shortcuts", {})
        except PermissionError:
            logger.error(f"Permission denied reading shortcuts at {path}")
            raise ShortcutError(f"Permission denied when trying to read shortcuts at: {path}")
        except (SyntaxError, ValueError, AttributeError) as e:
            logger.error(f"Corrupted binary shortcuts.vdf: {e}")
            raise ShortcutError(f"Corrupted binary shortcuts.vdf format: {str(e)}")

    @classmethod
    def write_shortcuts(cls, steam_id_32: int, shortcuts_dict: Dict[str, Any], vdf_path: Optional[str] = None) -> None:
        path = vdf_path or cls.get_shortcuts_path(steam_id_32)
        
        def _write(tf):
            vdf.binary_dump({"shortcuts": shortcuts_dict}, tf)
            
        try:
            cls._safe_write_replace(path, "wb", _write)
        except Exception as e:
            raise ShortcutError(f"Error writing shortcuts file: {str(e)}")

    @classmethod
    def add_shortcut(cls, steam_id_32: int, shortcut_data: Dict[str, Any], vdf_path: Optional[str] = None) -> None:
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
    def edit_shortcut(cls, steam_id_32: int, index: int, updates: Dict[str, Any], vdf_path: Optional[str] = None) -> None:
        if index < 0:
            raise ShortcutError(f"Shortcut index cannot be negative: {index}")

        shortcuts = cls.read_shortcuts(steam_id_32, vdf_path)
        idx_str = str(index)
        if idx_str not in shortcuts:
            raise ShortcutError(f"Shortcut with index {index} does not exist.")

        shortcuts[idx_str].update(updates)
        cls.write_shortcuts(steam_id_32, shortcuts, vdf_path)

    @classmethod
    def remove_shortcut(cls, steam_id_32: int, index: int, vdf_path: Optional[str] = None) -> None:
        if index < 0:
            raise ShortcutError(f"Shortcut index cannot be negative: {index}")

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

    @classmethod
    def search_sgdb_game(cls, api_key: str, game_name: str) -> Dict[str, Any]:
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
            logger.error(f"SGDB API HTTP Error: {e.code} - {e.reason}")
            raise SteamGridDBError(f"SteamGridDB API returned HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            logger.error(f"SGDB Network Error: {e.reason}")
            raise SteamGridDBError(f"Network error connecting to SteamGridDB: {e.reason}")
        except json.JSONDecodeError as e:
            logger.error(f"SGDB JSON Error: {e}")
            raise SteamGridDBError(f"Invalid JSON response from SteamGridDB: {str(e)}")

    @classmethod
    def get_sgdb_images_by_id(cls, api_key: str, game_id: int, image_type: str = "grids", 
                              sizes: Optional[List[str]] = None, filetypes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        url = f"https://www.steamgriddb.com/api/v2/{image_type}/game/{game_id}"
        
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "SteamForgeLib/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not data.get("success"):
                    raise SteamGridDBError(f"Failed to retrieve {image_type}.")
                
                images = data.get("data", [])
                if not isinstance(images, list):
                    images = []
                
                norm_sizes = {str(s).strip().lower() for s in sizes} if sizes else None
                norm_filetypes = {str(f).strip().lower().lstrip('.') for f in filetypes} if filetypes else None
                
                filtered_images = []
                for img in images:
                    if not isinstance(img, dict):
                        continue
                    if norm_sizes:
                        img_width = str(img.get("width", ""))
                        img_height = str(img.get("height", ""))
                        dim_str = f"{img_width}x{img_height}"
                        if dim_str not in norm_sizes and img_width not in norm_sizes and img_height not in norm_sizes:
                            continue
                            
                    if norm_filetypes:
                        img_url = img.get("url", "")
                        if not isinstance(img_url, str):
                            img_url = ""
                        ext = img_url.split("?")[0].split(".")[-1].lower()
                        if ext not in norm_filetypes:
                            continue
                            
                    filtered_images.append(img)
                    
                return filtered_images
        except urllib.error.HTTPError as e:
            logger.error(f"SGDB API HTTP Error: {e.code} - {e.reason}")
            raise SteamGridDBError(f"SteamGridDB API returned HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            logger.error(f"SGDB Network Error: {e.reason}")
            raise SteamGridDBError(f"Network error connecting to SteamGridDB: {e.reason}")
        except json.JSONDecodeError as e:
            logger.error(f"SGDB JSON Error: {e}")
            raise SteamGridDBError(f"Invalid JSON response from SteamGridDB: {str(e)}")

    @classmethod
    def get_sgdb_images_by_name(cls, api_key: str, game_name: str, image_type: str = "grids",
                                sizes: Optional[List[str]] = None, filetypes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        game_data = cls.search_sgdb_game(api_key, game_name)
        game_id = game_data.get("id")
        if not game_id:
            raise SteamGridDBError("Invalid game data returned from search.")
        return cls.get_sgdb_images_by_id(api_key, game_id, image_type, sizes=sizes, filetypes=filetypes)

    @classmethod
    def get_all_steam_library_folders(cls, base_steam_path: Optional[str] = None) -> List[str]:
        if base_steam_path is None:
            base_steam_path = cls.get_default_steam_path()
            
        libraryfolders_vdf = os.path.join(base_steam_path, "config", "libraryfolders.vdf")
        libraries = [base_steam_path]
        
        if not os.path.exists(libraryfolders_vdf):
            return libraries
            
        try:
            with open(libraryfolders_vdf, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)
                
            folders_dict = data.get("libraryfolders", data)
            if isinstance(folders_dict, dict):
                for key, val in folders_dict.items():
                    if isinstance(val, dict):
                        path = val.get("path")
                        if path and isinstance(path, str) and os.path.exists(path):
                            if path not in libraries:
                                libraries.append(path)
        except Exception as e:
            logger.warning(f"Error parsing libraryfolders.vdf: {e}")
            pass
            
        return libraries

    @classmethod
    def get_installed_steam_games(cls, base_steam_path: Optional[str] = None) -> List[Dict[str, Any]]:
        if base_steam_path is None:
            base_steam_path = cls.get_default_steam_path()
            
        library_paths = cls.get_all_steam_library_folders(base_steam_path)
        games = []
        seen_appids = set()

        for lib_path in library_paths:
            steamapps_dir = os.path.join(lib_path, "steamapps")
            if not os.path.exists(steamapps_dir):
                continue
                
            try:
                for filename in os.listdir(steamapps_dir):
                    if filename.startswith("appmanifest_") and filename.endswith(".acf"):
    
                        acf_path = os.path.join(steamapps_dir, filename)
                        try:
                            with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                                data = vdf.load(f)
                            
                            app_state = data.get("AppState", {})
                            if not isinstance(app_state, dict):
                                app_state = {}
                                
                            appid = app_state.get("appid")
                            name = app_state.get("name")
                            install_dir = app_state.get("installdir")
                            size_on_disk = app_state.get("SizeOnDict") or app_state.get("SizeOnDisk")
                            
                            if appid and name and appid not in seen_appids:
                                seen_appids.add(appid)
                                games.append({
                                    "AppID": str(appid),
                                    "Name": str(name),
                                    "InstallDir": str(install_dir) if install_dir else "",
                                    "SizeOnDisk": int(size_on_disk) if size_on_disk and str(size_on_disk).isdigit() else 0,
                                    "ManifestPath": acf_path,
                                    "LibraryPath": lib_path
                                })
                        except Exception as e:
                            logger.error(f"Failed parsing VDF at {acf_path}: {e}")
                            raise VDFParseError(f"Error parsing VDF at {acf_path}: {e}")
            except Exception as e:
                logger.error(f"Error scanning steamapps directory {steamapps_dir}: {e}")
                raise ConfigError(f"Error scanning steamapps directory {steamapps_dir}: {e}")

        games.sort(key=lambda x: x["Name"].lower())
        return games