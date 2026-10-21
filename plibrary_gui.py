#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QSplitter
)
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QPixmap, QImage

from plibrary_xl import PLibraryXL

class ShortcutDialog(QDialog):
    def __init__(self, parent=None, shortcut_data=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcut Details (All Fields)")
        self.resize(550, 650)
        
        layout = QFormLayout(self)
        
        self.txt_appname = QLineEdit()
        self.txt_exe = QLineEdit()
        self.txt_startdir = QLineEdit()
        self.txt_icon = QLineEdit()
        self.txt_shortcutpath = QLineEdit()
        self.txt_launchoptions = QLineEdit()
        
        self.chk_ishidden = QCheckBox("Hidden")
        self.chk_allowdesktopconfig = QCheckBox("Allow Desktop Config")
        self.chk_allowoverlay = QCheckBox("Allow Overlay")
        self.chk_openvr = QCheckBox("OpenVR")
        self.chk_devkit = QCheckBox("Devkit")
        
        self.txt_devkitgameid = QLineEdit()
        self.spin_devkitoverrideappid = QSpinBox()
        self.spin_devkitoverrideappid.setRange(0, 999999999)
        
        self.spin_lastplaytime = QSpinBox()
        self.spin_lastplaytime.setRange(0, 999999999)
        
        self.txt_flatpakappid = QLineEdit()
        self.txt_tags = QTextEdit()
        self.txt_tags.setMaximumHeight(70)
        self.txt_tags.setPlaceholderText("JSON dict or comma-separated tags...")

        if shortcut_data:
            self.txt_appname.setText(str(shortcut_data.get("appname", "")))
            self.txt_exe.setText(str(shortcut_data.get("exe", "")))
            self.txt_startdir.setText(str(shortcut_data.get("StartDir", "")))
            self.txt_icon.setText(str(shortcut_data.get("icon", "")))
            self.txt_shortcutpath.setText(str(shortcut_data.get("ShortcutPath", "")))
            self.txt_launchoptions.setText(str(shortcut_data.get("LaunchOptions", "")))
            
            self.chk_ishidden.setChecked(bool(shortcut_data.get("IsHidden", 0)))
            self.chk_allowdesktopconfig.setChecked(bool(shortcut_data.get("AllowDesktopConfig", 1)))
            self.chk_allowoverlay.setChecked(bool(shortcut_data.get("AllowOverlay", 1)))
            self.chk_openvr.setChecked(bool(shortcut_data.get("OpenVR", 0)))
            self.chk_devkit.setChecked(bool(shortcut_data.get("Devkit", 0)))
            
            self.txt_devkitgameid.setText(str(shortcut_data.get("DevkitGameID", "")))
            self.spin_devkitoverrideappid.setValue(int(shortcut_data.get("DevkitOverrideAppID", 0)))
            self.spin_lastplaytime.setValue(int(shortcut_data.get("LastPlayTime", 0)))
            self.txt_flatpakappid.setText(str(shortcut_data.get("FlatpakAppID", "")))
            
            tags_val = shortcut_data.get("tags", {})
            if isinstance(tags_val, dict):
                self.txt_tags.setPlainText(json.dumps(tags_val, indent=2))
            else:
                self.txt_tags.setPlainText(str(tags_val))
        else:
            self.txt_startdir.setText('"/usr/bin"')
            self.chk_allowdesktopconfig.setChecked(True)
            self.chk_allowoverlay.setChecked(True)
            self.txt_tags.setPlainText("{}")

        layout.addRow("App Name:", self.txt_appname)
        layout.addRow("Executable (exe):", self.txt_exe)
        layout.addRow("Start Directory:", self.txt_startdir)
        layout.addRow("Icon Path:", self.txt_icon)
        layout.addRow("Shortcut Path:", self.txt_shortcutpath)
        layout.addRow("Launch Options:", self.txt_launchoptions)
        
        flags_layout = QHBoxLayout()
        flags_layout.addWidget(self.chk_ishidden)
        flags_layout.addWidget(self.chk_allowdesktopconfig)
        flags_layout.addWidget(self.chk_allowoverlay)
        layout.addRow("Flags:", flags_layout)

        vr_devkit_layout = QHBoxLayout()
        vr_devkit_layout.addWidget(self.chk_openvr)
        vr_devkit_layout.addWidget(self.chk_devkit)
        layout.addRow("VR / Devkit:", vr_devkit_layout)

        layout.addRow("Devkit Game ID:", self.txt_devkitgameid)
        layout.addRow("Devkit Override App ID:", self.spin_devkitoverrideappid)
        layout.addRow("Last Play Time:", self.spin_lastplaytime)
        layout.addRow("Flatpak App ID:", self.txt_flatpakappid)
        layout.addRow("Tags (JSON):", self.txt_tags)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def get_data(self) -> dict:
        try:
            tags_data = json.loads(self.txt_tags.toPlainText())
            if not isinstance(tags_data, dict):
                tags_data = {}
        except Exception:
            tags_data = {}

        return {
            "appname": self.txt_appname.text(),
            "exe": self.txt_exe.text(),
            "StartDir": self.txt_startdir.text(),
            "icon": self.txt_icon.text(),
            "ShortcutPath": self.txt_shortcutpath.text(),
            "LaunchOptions": self.txt_launchoptions.text(),
            "IsHidden": 1 if self.chk_ishidden.isChecked() else 0,
            "AllowDesktopConfig": 1 if self.chk_allowdesktopconfig.isChecked() else 0,
            "AllowOverlay": 1 if self.chk_allowoverlay.isChecked() else 0,
            "OpenVR": 1 if self.chk_openvr.isChecked() else 0,
            "Devkit": 1 if self.chk_devkit.isChecked() else 0,
            "DevkitGameID": self.txt_devkitgameid.text(),
            "DevkitOverrideAppID": self.spin_devkitoverrideappid.value(),
            "LastPlayTime": self.spin_lastplaytime.value(),
            "FlatpakAppID": self.txt_flatpakappid.text(),
            "tags": tags_data
        }


class PLibraryXLTestGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLibraryXL Feature Tester & GUI")
        self.resize(1350, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.init_process_login_tab()
        self.init_config_tab()
        self.init_shortcuts_tab()
        self.init_sgdb_tab()

        log_group = QGroupBox("Execution Logs & Output")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(130)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        self.log("PLibraryXL GUI initialized successfully with full shortcut fields support.")

    def log(self, message: str):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    # ==========================================
    # TAB 1: Process & Login Users
    # ==========================================
    def init_process_login_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        status_group = QGroupBox("Steam Process Monitoring")
        status_layout = QHBoxLayout(status_group)
        self.lbl_steam_status = QLabel("Steam Status: Unknown")
        btn_check_steam = QPushButton("Check if Steam is Running")
        btn_check_steam.clicked.connect(self.check_steam_status)
        status_layout.addWidget(self.lbl_steam_status)
        status_layout.addWidget(btn_check_steam)
        layout.addWidget(status_group)

        vdf_group = QGroupBox("Parse Steam loginusers.vdf")
        vdf_layout = QVBoxLayout(vdf_group)
        
        form_layout = QFormLayout()
        self.txt_vdf_path = QLineEdit(os.path.expanduser("~/.local/share/Steam/config/loginusers.vdf"))
        btn_browse_vdf = QPushButton("Browse...")
        btn_browse_vdf.clicked.connect(self.browse_vdf_path)
        
        vdf_path_layout = QHBoxLayout()
        vdf_path_layout.addWidget(self.txt_vdf_path)
        vdf_path_layout.addWidget(btn_browse_vdf)
        form_layout.addRow("VDF Path:", vdf_path_layout)
        vdf_layout.addLayout(form_layout)

        btn_parse_vdf = QPushButton("Parse Login Users")
        btn_parse_vdf.clicked.connect(self.parse_login_users)
        vdf_layout.addWidget(btn_parse_vdf)

        self.table_accounts = QTableWidget()
        self.table_accounts.setColumnCount(7)
        self.table_accounts.setHorizontalHeaderLabels([
            "SteamID64", "SteamID32", "Account Name", "Persona Name", 
            "Remember Password", "Auto Login", "Timestamp"
        ])
        self.table_accounts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vdf_layout.addWidget(self.table_accounts)

        layout.addWidget(vdf_group)
        self.tabs.addTab(tab, "Steam Process & Users")

    def check_steam_status(self):
        running = PLibraryXL.is_steam_running()
        status_str = "Running" if running else "Not Running"
        self.lbl_steam_status.setText(f"Steam Status: <b>{status_str}</b>")
        self.log(f"Checked Steam status: {status_str}")

    def browse_vdf_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select loginusers.vdf", "", "VDF Files (*.vdf);;All Files (*)")
        if path:
            self.txt_vdf_path.setText(path)

    def parse_login_users(self):
        path = self.txt_vdf_path.text()
        self.log(f"Parsing loginusers.vdf from: {path}")
        success, accounts, count, error = PLibraryXL.parse_steam_login_users(path)
        
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Error parsing loginusers.vdf: {error}")
            return

        self.log(f"Successfully parsed {count} accounts.")
        self.table_accounts.setRowCount(count)
        for row, acc in enumerate(accounts):
            self.table_accounts.setItem(row, 0, QTableWidgetItem(str(acc.get("SteamID64"))))
            self.table_accounts.setItem(row, 1, QTableWidgetItem(str(acc.get("SteamID32"))))
            self.table_accounts.setItem(row, 2, QTableWidgetItem(str(acc.get("AccountName"))))
            self.table_accounts.setItem(row, 3, QTableWidgetItem(str(acc.get("PersonaName"))))
            self.table_accounts.setItem(row, 4, QTableWidgetItem(str(acc.get("RememberPassword"))))
            self.table_accounts.setItem(row, 5, QTableWidgetItem(str(acc.get("AutoLogin"))))
            self.table_accounts.setItem(row, 6, QTableWidgetItem(str(acc.get("Timestamp"))))

    # ==========================================
    # TAB 2: JSON Config Management
    # ==========================================
    def init_config_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        file_group = QGroupBox("Configuration File & Operations")
        file_layout = QVBoxLayout(file_group)

        f_layout = QFormLayout()
        self.txt_config_path = QLineEdit("test_config.json")
        btn_browse_config = QPushButton("Browse...")
        btn_browse_config.clicked.connect(self.browse_config_path)
        cfg_path_layout = QHBoxLayout()
        cfg_path_layout.addWidget(self.txt_config_path)
        cfg_path_layout.addWidget(btn_browse_config)
        f_layout.addRow("Config File:", cfg_path_layout)
        file_layout.addLayout(f_layout)

        btn_layout = QHBoxLayout()
        btn_create_cfg = QPushButton("Create Config")
        btn_create_cfg.clicked.connect(self.create_config)
        btn_read_cfg = QPushButton("Read Config")
        btn_read_cfg.clicked.connect(self.read_config)
        btn_save_cfg = QPushButton("Save/Write Config")
        btn_save_cfg.clicked.connect(self.write_config)

        btn_layout.addWidget(btn_create_cfg)
        btn_layout.addWidget(btn_read_cfg)
        btn_layout.addWidget(btn_save_cfg)
        file_layout.addLayout(btn_layout)

        update_layout_container = QHBoxLayout()

        single_update_group = QGroupBox("Single Update (Dot Notation)")
        single_form = QFormLayout(single_update_group)
        self.txt_key_path = QLineEdit("settings.graphics.resolution")
        self.txt_key_value = QLineEdit("1920x1080")
        btn_update_single = QPushButton("Update Single Key")
        btn_update_single.clicked.connect(self.update_single_config)
        single_form.addRow("Key Path:", self.txt_key_path)
        single_form.addRow("Value:", self.txt_key_value)
        single_form.addRow(btn_update_single)
        update_layout_container.addWidget(single_update_group)

        bulk_update_group = QGroupBox("Batch Update (JSON Updates Dict)")
        bulk_form = QFormLayout(bulk_update_group)
        
        self.txt_bulk_updates = QTextEdit()
        self.txt_bulk_updates.setPlainText(json.dumps({
            "settings.volume": 95,
            "settings.graphics.fullscreen": False
        }, indent=4))
        self.txt_bulk_updates.setMaximumHeight(85)
        
        btn_update_bulk = QPushButton("Update Multiple Keys")
        btn_update_bulk.clicked.connect(self.update_bulk_config)
        bulk_form.addRow("Updates JSON:", self.txt_bulk_updates)
        bulk_form.addRow(btn_update_bulk)
        update_layout_container.addWidget(bulk_update_group)

        file_layout.addLayout(update_layout_container)

        file_layout.addWidget(QLabel("JSON Content Viewer / Editor:"))
        self.txt_config_editor = QTextEdit()
        self.txt_config_editor.setPlaceholderText("JSON content will appear here...")
        file_layout.addWidget(self.txt_config_editor)

        layout.addWidget(file_group)
        self.tabs.addTab(tab, "JSON Config")

    def browse_config_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select JSON Config File", "", "JSON Files (*.json);;All Files (*)")
        if path:
            self.txt_config_path.setText(path)

    def create_config(self):
        path = self.txt_config_path.text()
        initial = {"settings": {"graphics": {"resolution": "1920x1080", "fullscreen": True}, "volume": 80}}
        success, abs_path, error = PLibraryXL.create_config(path, initial_data=initial, overwrite=True)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to create config: {error}")
            return
        self.log(f"Created config at: {abs_path}")
        self.read_config()

    def read_config(self):
        path = self.txt_config_path.text()
        success, data, error = PLibraryXL.read_config(path)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to read config: {error}")
            return
        self.txt_config_editor.setPlainText(json.dumps(data, indent=4))
        self.log(f"Successfully read config from: {path}")

    def write_config(self):
        path = self.txt_config_path.text()
        content = self.txt_config_editor.toPlainText()
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON format: {str(e)}")
            return

        success, error = PLibraryXL.write_config(path, data)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to write config: {error}")
            return
        self.log(f"Successfully wrote config to: {path}")
        QMessageBox.information(self, "Success", "Configuration successfully saved.")

    def parse_value_type(self, val_str: str):
        if val_str.lower() == "true":
            return True
        elif val_str.lower() == "false":
            return False
        try:
            if "." in val_str:
                return float(val_str)
            else:
                return int(val_str)
        except ValueError:
            return val_str

    def update_single_config(self):
        path = self.txt_config_path.text()
        key_path = self.txt_key_path.text()
        val = self.parse_value_type(self.txt_key_value.text())

        success, error = PLibraryXL.update_config_value(path, key_path, val)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to update config key: {error}")
            return
        self.log(f"Successfully updated '{key_path}' = {val} in {path}")
        self.read_config()

    def update_bulk_config(self):
        path = self.txt_config_path.text()
        content = self.txt_bulk_updates.toPlainText()
        try:
            updates_raw = json.loads(content)
            if not isinstance(updates_raw, dict):
                raise ValueError("Updates must be a dictionary of key-value pairs.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid updates JSON: {str(e)}")
            return

        updates = {k: self.parse_value_type(str(v)) if not isinstance(v, (bool, int, float)) else v for k, v in updates_raw.items()}

        success, error = PLibraryXL.update_config_values(path, updates)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to perform batch config update: {error}")
            return

        self.log(f"Successfully performed batch update on {path}")
        QMessageBox.information(self, "Success", "Batch configuration updates applied successfully.")
        self.read_config()

    # ==========================================
    # TAB 3: Steam Shortcuts Management
    # ==========================================
    def init_shortcuts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        path_group = QGroupBox("Shortcuts VDF Target")
        path_layout = QFormLayout(path_group)

        self.txt_steam_id_32 = QLineEdit("12345678")
        self.txt_base_steam_path = QLineEdit(os.path.expanduser("~/.local/share/Steam"))
        
        btn_read_shortcuts = QPushButton("Load Shortcuts")
        btn_read_shortcuts.clicked.connect(self.load_shortcuts)

        path_layout.addRow("SteamID32:", self.txt_steam_id_32)
        path_layout.addRow("Base Steam Path:", self.txt_base_steam_path)
        path_layout.addRow(btn_read_shortcuts)
        layout.addWidget(path_group)

        sc_group = QGroupBox("Shortcuts List & Management (All Fields)")
        sc_layout = QVBoxLayout(sc_group)

        self.table_shortcuts = QTableWidget()
        self.table_shortcuts.setColumnCount(13)
        self.table_shortcuts.setHorizontalHeaderLabels([
            "Index", "App Name", "Exe", "Start Dir", "Icon", "Shortcut Path", 
            "Launch Options", "Hidden", "Desktop Config", "Overlay", "OpenVR", "Last Play", "Tags"
        ])
        self.table_shortcuts.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        sc_layout.addWidget(self.table_shortcuts)

        act_layout = QHBoxLayout()
        btn_add_sc = QPushButton("Add Custom Shortcut...")
        btn_add_sc.clicked.connect(self.add_shortcut_dialog)
        
        btn_edit_sc = QPushButton("Update / Edit Selected Shortcut...")
        btn_edit_sc.clicked.connect(self.edit_shortcut_dialog)

        btn_remove_sc = QPushButton("Remove Selected Shortcut")
        btn_remove_sc.clicked.connect(self.remove_shortcut_selected)

        act_layout.addWidget(btn_add_sc)
        act_layout.addWidget(btn_edit_sc)
        act_layout.addWidget(btn_remove_sc)
        sc_layout.addLayout(act_layout)

        layout.addWidget(sc_group)
        self.tabs.addTab(tab, "Steam Shortcuts")

    def get_steam_id_32(self) -> int:
        try:
            return int(self.txt_steam_id_32.text())
        except ValueError:
            return 0

    def load_shortcuts(self):
        steam_id_32 = self.get_steam_id_32()
        base_path = self.txt_base_steam_path.text()
        vdf_path = PLibraryXL.get_shortcuts_path(steam_id_32, base_path)
        
        self.log(f"Reading shortcuts from: {vdf_path}")
        success, shortcuts, count, error = PLibraryXL.read_shortcuts(steam_id_32, vdf_path)
        
        if not success:
            QMessageBox.warning(self, "Notice / Error", error)
            self.log(f"Shortcuts read notice: {error}")
            self.table_shortcuts.setRowCount(0)
            return

        self.log(f"Successfully loaded {count} shortcuts with all fields.")
        self.table_shortcuts.setRowCount(count)

        row = 0
        for idx_str, sc_data in shortcuts.items():
            item_idx = QTableWidgetItem(str(idx_str))
            item_idx.setData(Qt.UserRole, sc_data)
            
            self.table_shortcuts.setItem(row, 0, item_idx)
            self.table_shortcuts.setItem(row, 1, QTableWidgetItem(str(sc_data.get("appname", ""))))
            self.table_shortcuts.setItem(row, 2, QTableWidgetItem(str(sc_data.get("exe", ""))))
            self.table_shortcuts.setItem(row, 3, QTableWidgetItem(str(sc_data.get("StartDir", ""))))
            self.table_shortcuts.setItem(row, 4, QTableWidgetItem(str(sc_data.get("icon", ""))))
            self.table_shortcuts.setItem(row, 5, QTableWidgetItem(str(sc_data.get("ShortcutPath", ""))))
            self.table_shortcuts.setItem(row, 6, QTableWidgetItem(str(sc_data.get("LaunchOptions", ""))))
            self.table_shortcuts.setItem(row, 7, QTableWidgetItem(str(sc_data.get("IsHidden", 0))))
            self.table_shortcuts.setItem(row, 8, QTableWidgetItem(str(sc_data.get("AllowDesktopConfig", 1))))
            self.table_shortcuts.setItem(row, 9, QTableWidgetItem(str(sc_data.get("AllowOverlay", 1))))
            self.table_shortcuts.setItem(row, 10, QTableWidgetItem(str(sc_data.get("OpenVR", 0))))
            self.table_shortcuts.setItem(row, 11, QTableWidgetItem(str(sc_data.get("LastPlayTime", 0))))
            
            tags_val = sc_data.get("tags", {})
            tags_str = json.dumps(tags_val) if isinstance(tags_val, dict) else str(tags_val)
            self.table_shortcuts.setItem(row, 12, QTableWidgetItem(tags_str))
            row += 1

    def add_shortcut_dialog(self):
        steam_id_32 = self.get_steam_id_32()
        base_path = self.txt_base_steam_path.text()
        vdf_path = PLibraryXL.get_shortcuts_path(steam_id_32, base_path)

        dialog = ShortcutDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_sc = dialog.get_data()
            success, error = PLibraryXL.add_shortcut(steam_id_32, new_sc, vdf_path)
            if not success:
                QMessageBox.critical(self, "Error", error)
                self.log(f"Failed to add shortcut: {error}")
                return
            
            self.log("Successfully added new custom shortcut with all fields.")
            QMessageBox.information(self, "Success", "Custom shortcut added successfully.")
            self.load_shortcuts()

    def edit_shortcut_dialog(self):
        selected_rows = self.table_shortcuts.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a shortcut row to edit/update.")
            return

        row = selected_rows[0].row()
        index_item = self.table_shortcuts.item(row, 0)
        if not index_item:
            return

        idx = int(index_item.text())
        existing_data = index_item.data(Qt.UserRole) or {}

        steam_id_32 = self.get_steam_id_32()
        base_path = self.txt_base_steam_path.text()
        vdf_path = PLibraryXL.get_shortcuts_path(steam_id_32, base_path)

        dialog = ShortcutDialog(self, shortcut_data=existing_data)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_data()
            success, error = PLibraryXL.edit_shortcut(steam_id_32, idx, updated_data, vdf_path)
            if not success:
                QMessageBox.critical(self, "Error", error)
                self.log(f"Failed to edit shortcut: {error}")
                return

            self.log(f"Successfully updated shortcut at index {idx} with all fields.")
            QMessageBox.information(self, "Success", f"Shortcut index {idx} updated successfully.")
            self.load_shortcuts()

    def remove_shortcut_selected(self):
        selected_rows = self.table_shortcuts.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a shortcut row to remove.")
            return

        row = selected_rows[0].row()
        index_item = self.table_shortcuts.item(row, 0)
        if not index_item:
            return

        idx = int(index_item.text())
        steam_id_32 = self.get_steam_id_32()
        base_path = self.txt_base_steam_path.text()
        vdf_path = PLibraryXL.get_shortcuts_path(steam_id_32, base_path)

        success, error = PLibraryXL.remove_shortcut(steam_id_32, idx, vdf_path)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to remove shortcut: {error}")
            return

        self.log(f"Successfully removed shortcut at index {idx}.")
        QMessageBox.information(self, "Success", f"Shortcut index {idx} removed successfully.")
        self.load_shortcuts()

    # ==========================================
    # TAB 4: SteamGridDB Integration & Preview
    # ==========================================
    def init_sgdb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        api_group = QGroupBox("SteamGridDB API Settings & Query")
        api_form = QFormLayout(api_group)

        self.txt_sgdb_key = QLineEdit()
        self.txt_sgdb_key.setPlaceholderText("Enter your SteamGridDB API key here...")
        self.txt_sgdb_key.setEchoMode(QLineEdit.Password)

        query_type_layout = QHBoxLayout()
        self.combo_query_mode = QComboBox()
        self.combo_query_mode.addItems(["Search by Game Name", "Fetch by Game ID"])
        self.combo_query_mode.currentIndexChanged.connect(self.on_sgdb_query_mode_changed)

        self.txt_sgdb_query = QLineEdit()
        self.txt_sgdb_query.setPlaceholderText("e.g. Skyrim, Portal 2...")

        query_type_layout.addWidget(self.combo_query_mode, stretch=1)
        query_type_layout.addWidget(self.txt_sgdb_query, stretch=3)

        options_layout = QHBoxLayout()
        self.combo_image_type = QComboBox()
        self.combo_image_type.addItems(["grids", "heroes", "logos", "icons"])

        btn_search_sgdb = QPushButton("Fetch Images")
        btn_search_sgdb.clicked.connect(self.fetch_sgdb_images)

        options_layout.addWidget(QLabel("Image Type:"))
        options_layout.addWidget(self.combo_image_type, stretch=1)
        options_layout.addWidget(btn_search_sgdb, stretch=2)

        api_form.addRow("API Key:", self.txt_sgdb_key)
        api_form.addRow("Query Mode:", query_type_layout)
        api_form.addRow("Actions:", options_layout)
        layout.addWidget(api_group)

        # Splitter between Table and Image Preview
        splitter = QSplitter(Qt.Horizontal)

        results_group = QGroupBox("Retrieved Images Results")
        results_layout = QVBoxLayout(results_group)

        self.table_sgdb = QTableWidget()
        self.table_sgdb.setColumnCount(5)
        self.table_sgdb.setHorizontalHeaderLabels(["ID", "Type / Style", "Dimensions", "Author", "Image URL"])
        self.table_sgdb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sgdb.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_sgdb.setSelectionMode(QTableWidget.SingleSelection)
        self.table_sgdb.itemSelectionChanged.connect(self.preview_selected_sgdb_image)
        results_layout.addWidget(self.table_sgdb)
        splitter.addWidget(results_group)

        preview_group = QGroupBox("Artwork Image Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.lbl_image_preview = QLabel("Select an image row to preview")
        self.lbl_image_preview.setAlignment(Qt.AlignCenter)
        self.lbl_image_preview.setMinimumSize(300, 300)
        self.lbl_image_preview.setStyleSheet("background-color: #1e1e1e; color: #aaaaaa; border-radius: 6px;")
        preview_layout.addWidget(self.lbl_image_preview)
        splitter.addWidget(preview_group)

        splitter.setSizes([750, 350])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "SteamGridDB")

    def on_sgdb_query_mode_changed(self, index):
        if index == 0:
            self.txt_sgdb_query.setPlaceholderText("e.g. Skyrim, Portal 2...")
        else:
            self.txt_sgdb_query.setPlaceholderText("e.g. 650, 317 (Numeric Game ID)...")

    def fetch_sgdb_images(self):
        api_key = self.txt_sgdb_key.text().strip()
        query_text = self.txt_sgdb_query.text().strip()
        image_type = self.combo_image_type.currentText()
        mode = self.combo_query_mode.currentIndex()

        if not api_key:
            QMessageBox.warning(self, "API Key Required", "Please enter your SteamGridDB API key.")
            return
        if not query_text:
            QMessageBox.warning(self, "Query Required", "Please enter a game name or game ID.")
            return

        if mode == 0:
            self.log(f"Querying SteamGridDB by name for '{query_text}' ({image_type})...")
            success, images, error = PLibraryXL.get_sgdb_images_by_name(api_key, query_text, image_type)
        else:
            try:
                game_id = int(query_text)
            except ValueError:
                QMessageBox.critical(self, "Invalid ID", "Game ID must be a valid integer number (e.g. 650).")
                return

            self.log(f"Querying SteamGridDB directly by ID {game_id} ({image_type})...")
            success, images, error = PLibraryXL.get_sgdb_images_by_id(api_key, game_id, image_type)

        if not success:
            QMessageBox.critical(self, "SteamGridDB Error", error)
            self.log(f"SteamGridDB error: {error}")
            self.table_sgdb.setRowCount(0)
            self.lbl_image_preview.setText("No image preview available")
            return

        self.log(f"Successfully retrieved {len(images)} {image_type} items.")
        self.table_sgdb.setRowCount(len(images))

        for row, img in enumerate(images):
            img_id = str(img.get("id", ""))
            style = str(img.get("style", "N/A"))
            dims = f"{img.get('width', '?')}x{img.get('height', '?')}"
            author_data = img.get("author", {})
            author_name = author_data.get("name", "Unknown") if isinstance(author_data, dict) else "Unknown"
            url = str(img.get("url", ""))

            self.table_sgdb.setItem(row, 0, QTableWidgetItem(img_id))
            self.table_sgdb.setItem(row, 1, QTableWidgetItem(style))
            self.table_sgdb.setItem(row, 2, QTableWidgetItem(dims))
            self.table_sgdb.setItem(row, 3, QTableWidgetItem(author_name))
            self.table_sgdb.setItem(row, 4, QTableWidgetItem(url))

    def preview_selected_sgdb_image(self):
        selected_rows = self.table_sgdb.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        url_item = self.table_sgdb.item(row, 4)
        if not url_item:
            return

        img_url = url_item.text().strip()
        if not img_url:
            return

        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": "PLibraryXL/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                img_data = response.read()

            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(img_data))
            
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.lbl_image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_image_preview.setPixmap(scaled)
                self.log(f"Loaded image preview for ID {self.table_sgdb.item(row, 0).text()}")
            else:
                self.lbl_image_preview.setText("Failed to decode image format")
        except Exception as e:
            self.lbl_image_preview.setText("Error downloading preview")
            self.log(f"Image preview download error: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PLibraryXLTestGUI()
    window.show()
    sys.exit(app.exec())
