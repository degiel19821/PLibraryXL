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

logger = logging.getLogger(__name__)

class SteamForgeError(Exception): pass
class VDFParseError(SteamForgeError): pass
class ConfigError(SteamForgeError): pass
class ProcessMonitorError(SteamForgeError): pass
class UMUError(SteamForgeError): pass
class ShortcutError(SteamForgeError): pass
class SteamGridDBError(SteamForgeError): pass


class FileIOManager:
    """Handles safe, atomic file operations."""
    
    @staticmethod
    def safe_write_replace(dest_path: str, mode: str, write_callback: Callable[[Any], None], encoding: Optional[str] = None) -> None:
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


class ConfigManager:
    """Manages JSON configuration reading and writing."""
    
    @classmethod
    def create(cls, file_path: str, initial_data: Optional[Dict[str, Any]] = None, overwrite: bool = False) -> str:
        abs_path = os.path.abspath(file_path)
        if os.path.exists(abs_path) and not overwrite:
            logger.warning(f"Config creation skipped: {abs_path} already exists.")
            raise ConfigError(f"Config file already exists at: {abs_path}")
        
        initial_data = initial_data or {}
        try:
            FileIOManager.safe_write_replace(abs_path, "w", lambda tf: json.dump(initial_data, tf, indent=4, ensure_ascii=False), encoding="utf-8")
            return abs_path
        except Exception as e:
            raise ConfigError(f"Error creating config file: {str(e)}")

    @classmethod
    def read(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise ConfigError(f"Config file not found: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON format: {str(e)}")
        except PermissionError as e:
            raise ConfigError(f"Permission denied: {str(e)}")

    @classmethod
    def write(cls, file_path: str, data: Dict[str, Any], indent: int = 4) -> None:
        try:
            FileIOManager.safe_write_replace(file_path, "w", lambda tf: json.dump(data, tf, indent=indent, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            raise ConfigError(f"Error writing config: {str(e)}")

    @classmethod
    def update_values(cls, file_path: str, updates: Dict[str, Any]) -> None:
        config = cls.read(file_path)
        for key_path, value in updates.items():
            keys = key_path.split(".")
            curr = config
            for key in keys[:-1]:
                if key not in curr or not isinstance(curr[key], dict):
                    curr[key] = {}
                curr = curr[key]
            curr[keys[-1]] = value
        cls.write(file_path, config)


class SteamEnvironment:
    """Handles Steam installation paths and VDF library parsing."""
    
    @staticmethod
    def _safe_bool(value: Any) -> bool:
        if isinstance(value, bool): return value
        if value is None: return False
        try: return bool(int(value))
        except (ValueError, TypeError): return False

    @staticmethod
    def get_default_path() -> str:
        paths = [
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/Library/Application Support/Steam"),
            "C:\\Program Files (x86)\\Steam",
            "C:\\Program Files\\Steam"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return os.path.expanduser("~/.local/share/Steam")

    @classmethod
    def parse_login_users(cls, vdf_path: Optional[str] = None) -> List[Dict[str, Any]]:
        vdf_path = vdf_path or os.path.join(cls.get_default_path(), "config", "loginusers.vdf")
        if not os.path.exists(vdf_path):
            raise VDFParseError(f"loginusers.vdf missing at: {vdf_path}")

        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)
        except Exception as e:
            raise VDFParseError(f"Invalid VDF format: {str(e)}")

        accounts = []
        for steam_id_str, details in data.get("users", {}).items():
            try: steam_id_64 = int(steam_id_str)
            except ValueError: continue
            
            if not isinstance(details, dict): details = {}
            accounts.append({
                "SteamID64": steam_id_64,
                "SteamID32": steam_id_64 & 0xFFFFFFFF,
                "AccountName": details.get("AccountName", "Unknown"),
                "PersonaName": details.get("PersonaName", "Unknown"),
                "RememberPassword": cls._safe_bool(details.get("RememberPassword")),
                "AutoLogin": cls._safe_bool(details.get("AutoLogin")),
                "Timestamp": details.get("timestamp")
            })
        return accounts

    @classmethod
    def get_library_folders(cls, base_steam_path: Optional[str] = None) -> List[str]:
        base_steam_path = base_steam_path or cls.get_default_path()
        vdf_path = os.path.join(base_steam_path, "config", "libraryfolders.vdf")
        libraries = [base_steam_path]
        
        if not os.path.exists(vdf_path):
            return libraries
            
        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                data = vdf.load(f)
            folders_dict = data.get("libraryfolders", data)
            if isinstance(folders_dict, dict):
                for val in folders_dict.values():
                    if isinstance(val, dict) and os.path.exists(path := val.get("path", "")):
                        if path not in libraries: libraries.append(path)
        except Exception:
            pass
        return libraries

    @classmethod
    def get_installed_games(cls, base_steam_path: Optional[str] = None) -> List[Dict[str, Any]]:
        games = []
        seen_appids = set()
        
        for lib_path in cls.get_library_folders(base_steam_path):
            steamapps_dir = os.path.join(lib_path, "steamapps")
            if not os.path.exists(steamapps_dir):
                continue
                
            for filename in os.listdir(steamapps_dir):
                if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                    acf_path = os.path.join(steamapps_dir, filename)
                    try:
                        with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                            app_state = vdf.load(f).get("AppState", {})
                        
                        appid = app_state.get("appid")
                        name = app_state.get("name")
                        
                        if appid and name and appid not in seen_appids:
                            seen_appids.add(appid)
                            games.append({
                                "AppID": str(appid),
                                "Name": str(name),
                                "InstallDir": str(app_state.get("installdir", "")),
                                "ManifestPath": acf_path,
                                "LibraryPath": lib_path
                            })
                    except Exception as e:
                        logger.error(f"Error parsing VDF at {acf_path}: {e}")
        return sorted(games, key=lambda x: x["Name"].lower())


class ProcessManager:
    """Manages application launching and process monitoring."""

    @staticmethod
    def is_steam_running() -> bool:
        steam_names = {"steam", "steam.exe"}
        try:
            for proc in psutil.process_iter(attrs=["name"]):
                try:
                    if proc.info.get("name", "").lower() in steam_names: return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        except psutil.Error as e:
            raise ProcessMonitorError(f"Failed to read process table: {str(e)}")

    @staticmethod
    def launch_steam_game(app_id: str | int) -> None:
        import platform
        url = f"steam://rungameid/{app_id}"
        system = platform.system()
        try:
            if system == "Linux": subprocess.Popen(["xdg-open", url])
            elif system == "Windows": os.startfile(url)
            elif system == "Darwin": subprocess.Popen(["open", url])
            else: raise SteamForgeError(f"Unsupported OS: {system}")
        except Exception as e:
            raise SteamForgeError(f"Failed to launch AppID {app_id}: {str(e)}")

    @staticmethod
    def launch_with_umu(target_exe: str, umu_run_path: str = "umu-run", proton_version: str = "", game_id: str = "0", prefix_path: str = "", launch_options: Optional[List[str]] = None, log_output: bool = True) -> subprocess.Popen:
        exe_path = os.path.abspath(target_exe)
        if not os.path.isfile(exe_path):
            raise UMUError(f"Target path is not a file: {target_exe}")

        env = os.environ.copy()
        if game_id: env["GAMEID"] = str(game_id)
        if proton_version: env["PROTONPATH"] = str(proton_version)
        if prefix_path: env["WINEPREFIX"] = str(prefix_path)
            
        cmd = [umu_run_path, exe_path] + [str(opt) for opt in (launch_options or [])]
        try:
            return subprocess.Popen(
                cmd, env=env, 
                stdout=subprocess.PIPE if log_output else None,
                stderr=subprocess.PIPE if log_output else None,
                start_new_session=True
            )
        except OSError as e:
            raise UMUError(f"OS error launching with umu: {str(e)}")


class ShortcutManager:
    """Manages parsing and writing of Steam's binary shortcuts.vdf."""

    @staticmethod
    def get_path(steam_id_32: int, base_steam_path: Optional[str] = None) -> str:
        base_steam_path = base_steam_path or SteamEnvironment.get_default_path()
        return os.path.join(base_steam_path, "userdata", str(steam_id_32), "config", "shortcuts.vdf")

    @classmethod
    def read(cls, steam_id_32: int, vdf_path: Optional[str] = None) -> Dict[str, Any]:
        path = vdf_path or cls.get_path(steam_id_32)
        if not os.path.exists(path):
            raise ShortcutError(f"shortcuts.vdf not found at: {path}")

        try:
            with open(path, "rb") as f:
                return vdf.binary_load(f).get("shortcuts", {})
        except Exception as e:
            raise ShortcutError(f"Error reading shortcuts.vdf: {str(e)}")

    @classmethod
    def write(cls, steam_id_32: int, shortcuts_dict: Dict[str, Any], vdf_path: Optional[str] = None) -> None:
        path = vdf_path or cls.get_path(steam_id_32)
        try:
            FileIOManager.safe_write_replace(path, "wb", lambda tf: vdf.binary_dump({"shortcuts": shortcuts_dict}, tf))
        except Exception as e:
            raise ShortcutError(f"Error writing shortcuts file: {str(e)}")

    @classmethod
    def add(cls, steam_id_32: int, shortcut_data: Dict[str, Any], vdf_path: Optional[str] = None) -> None:
        try: shortcuts = cls.read(steam_id_32, vdf_path)
        except ShortcutError: shortcuts = {}
        
        existing_indices = [int(k) for k in shortcuts.keys() if k.isdigit()]
        next_index = str(max(existing_indices) + 1) if existing_indices else "0"
        shortcuts[next_index] = shortcut_data
        cls.write(steam_id_32, shortcuts, vdf_path)


class LocalArtworkManager:
    """Scans and retrieves local Steam library artwork."""

    @staticmethod
    def get_artwork(app_id: str | int, custom_steam_path: Optional[str] = None) -> Dict[str, str]:
        steam_dir = pathlib.Path(custom_steam_path or SteamEnvironment.get_default_path())
        cache_dir = steam_dir / "appcache" / "librarycache"
        if not cache_dir.exists(): return {}
            
        found_artworks = {}
        app_id_str = str(app_id)
        
        patterns = {
            "grid": f"{app_id_str}_library_600x900.jpg",
            "header": f"{app_id_str}_header.jpg",
            "hero": f"{app_id_str}_library_hero.jpg",
            "logo": f"{app_id_str}_logo.png",
            "icon": f"{app_id_str}_icon.jpg"
        }

        for path in cache_dir.rglob(f"{app_id_str}_*"):
            if not path.is_file(): continue
            filename = path.name.lower()
            for art_type, pattern_name in patterns.items():
                if filename == pattern_name.lower():
                    found_artworks[art_type] = str(path)
                        
        return found_artworks


class SteamGridDBClient:
    """Handles external API integrations with SteamGridDB."""

    @classmethod
    def search_game(cls, api_key: str, game_name: str) -> Dict[str, Any]:
        url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(game_name)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "SteamForgeLib/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("success") and data.get("data"): return data["data"][0]
                raise SteamGridDBError("No games found.")
        except Exception as e:
            raise SteamGridDBError(f"API Error: {str(e)}")

    @classmethod
    def get_images_by_id(cls, api_key: str, game_id: int, image_type: str = "grids") -> List[Dict[str, Any]]:
        url = f"https://www.steamgriddb.com/api/v2/{image_type}/game/{game_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "SteamForgeLib/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8")).get("data", [])
        except Exception as e:
            raise SteamGridDBError(f"API Error: {str(e)}")