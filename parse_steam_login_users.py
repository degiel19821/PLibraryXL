#!/usr/bin/env python3
import os
import sys
import argparse
import json
import vdf

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

def parse_steam_login_users(vdf_path="/home/deck/.local/share/Steam/config/loginusers.vdf"):
    """
    Reads and parses the Steam loginusers.vdf file.
    Returns a tuple: (success: bool, accounts: list, count: int, error_message: str | None)
    """
    if not os.path.exists(vdf_path):
        return False, [], 0, f"loginusers.vdf could not be found at: {vdf_path}"

    try:
        # Open and parse using the vdf package
        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
            data = vdf.load(f)

        accounts = []

        # Iterate through accounts stored under the "users" key
        users_dict = data.get("users", {})
        for steam_id_str, details in users_dict.items():
            try:
                steam_id_64 = int(steam_id_str)
            except ValueError:
                # Skip invalid non-numeric steam IDs if the file is malformed
                continue

            # Derive the 32-bit Account ID (SteamID32)
            steam_id_32 = steam_id_64 & 0xFFFFFFFF

            account_info = {
                "SteamID64": steam_id_64,
                "SteamID32": steam_id_32,
                "AccountName": details.get("AccountName", "Unknown"),
                "PersonaName": details.get("PersonaName", "Unknown"),
                "RememberPassword": _safe_bool(details.get("RememberPassword")),
                "AutoLogin": _safe_bool(details.get("AutoLogin")),
                "Timestamp": details.get("timestamp")
            }
            accounts.append(account_info)

        return True, accounts, len(accounts), None

    except PermissionError:
        return False, [], 0, f"Permission denied when trying to read: {vdf_path}"
    except Exception as e:
        return False, [], 0, f"An unexpected error occurred while parsing VDF: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Parse Steam loginusers.vdf file and list saved accounts.")
    parser.add_argument(
        "-p", "--path",
        default="/home/deck/.local/share/Steam/config/loginusers.vdf",
        help="Path to the loginusers.vdf file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the parsed accounts in JSON format"
    )
    
    args = parser.parse_args()

    success, accounts, count, error = parse_steam_login_users(args.path)

    if not success:
        error_output = {"success": False, "error": error}
        if args.json:
            print(json.dumps(error_output, indent=4))
        else:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = {
            "success": True,
            "count": count,
            "accounts": accounts
        }
        print(json.dumps(output, indent=4))
    else:
        print(f"Successfully found {count} account(s):\n")
        for acc in accounts:
            print(f"Account Name:  {acc['AccountName']}")
            print(f"Persona Name:  {acc['PersonaName']}")
            print(f"SteamID64:     {acc['SteamID64']}")
            print(f"SteamID32:     {acc['SteamID32']}")
            print(f"Remember Pass: {acc['RememberPassword']}")
            print(f"Auto Login:    {acc['AutoLogin']}")
            print("-" * 40)

if __name__ == "__main__":
    main()