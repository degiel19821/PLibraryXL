#!/usr/init/env python3
import os
import sys
import json
import argparse

def create_config(file_path: str, initial_data: dict, overwrite: bool = False):
    """
    Creates a configuration file using externally provided initial_data.
    Returns a tuple: (success: bool, absolute_path: str | None, error_message: str | None)
    """
    abs_path = os.path.abspath(file_path)

    if os.path.exists(abs_path) and not overwrite:
        return False, abs_path, f"Config file already exists at: {abs_path} (use --overwrite to replace)"
    
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

def read_config(file_path: str):
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

def write_config(file_path: str, data: dict, indent: int = 4):
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

def update_config_value(file_path: str, key_path: str, value):
    """Updates a value in an existing config. Supports dot notation for nested keys."""
    success, config, error = read_config(file_path)
    if not success:
        return False, f"Cannot update config: {error}"

    keys = key_path.split(".")
    curr = config
    for key in keys[:-1]:
        if key not in curr or not isinstance(curr[key], dict):
            curr[key] = {}
        curr = curr[key]

    curr[keys[-1]] = value
    return write_config(file_path, config)

def main():
    parser = argparse.ArgumentParser(description="Read, write, and update JSON configuration files with external defaults.")
    subparsers = parser.add_subparsers(subparser_title="command", dest="command", required=True, help="Command to run")

    # Create config
    p_create = subparsers.add_parser("create", help="Create a configuration file with external default data")
    p_create.add_argument("-f", "--file", required=True, help="Path to config file")
    p_create.add_argument("-d", "--data", required=True, help="Default config data as a JSON string or path to a JSON template file")
    p_create.add_argument("--overwrite", action="store_true", help="Overwrite existing file if it already exists")

    # Read (supports --json)
    p_read = subparsers.add_parser("read", help="Read and print the config file")
    p_read.add_argument("-f", "--file", required=True, help="Path to config file")
    p_read.add_argument("--json", action="store_true", help="Output read data in JSON format")

    # Set / Update value
    p_set = subparsers.add_parser("set", help="Set or update a configuration key")
    p_set.add_argument("-f", "--file", required=True, help="Path to config file")
    p_set.add_argument("-k", "--key", required=True, help="Key to update (supports dot notation)")
    p_set.add_argument("-v", "--value", required=True, help="Value to set")

    args = parser.parse_args()

    if args.command == "create":
        initial_data = None
        if os.path.exists(args.data):
            try:
                with open(args.data, "r", encoding="utf-8") as tf:
                    initial_data = json.load(tf)
            except Exception as e:
                print(f"Error reading template file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            try:
                initial_data = json.loads(args.data)
            except json.JSONDecodeError as e:
                print(f"Error parsing data JSON string: {e}", file=sys.stderr)
                sys.exit(1)

        success, abs_path, err = create_config(args.file, initial_data=initial_data, overwrite=args.overwrite)
        if not success:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Successfully created config file at: {abs_path}")

    elif args.command == "read":
        success, data, err = read_config(args.file)
        if not success:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps({"success": True, "file": os.path.abspath(args.file), "data": data}, indent=4))
        else:
            print(json.dumps(data, indent=4))

    elif args.command == "set":
        val_str = args.value
        if val_str.lower() == "true":
            parsed_val = True
        elif val_str.lower() == "false":
            parsed_val = False
        else:
            try:
                if "." in val_str:
                    parsed_val = float(val_str)
                else:
                    parsed_val = int(val_str)
            except ValueError:
                parsed_val = val_str

        success, err = update_config_value(args.file, args.key, parsed_val)
        if not success:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Successfully updated '{args.key}' = {parsed_val} in {args.file}")

if __name__ == "__main__":
    main()
