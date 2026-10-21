#!/usr/bin/env python3
import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QHeaderView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer

from PLibraryXL import PLibraryXL

class ShortcutDialog(QDialog):
    def __init__(self, parent=None, shortcut_data=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcut Details")
        self.resize(500, 350)
        
        layout = QFormLayout(self)
        
        self.txt_appname = QLineEdit()
        self.txt_exe = QLineEdit()
        self.txt_startdir = QLineEdit()
        self.txt_launchoptions = QLineEdit()
        
        if shortcut_data:
            self.txt_appname.setText(str(shortcut_data.get("appname", "")))
            self.txt_exe.setText(str(shortcut_data.get("exe", "")))
            self.txt_startdir.setText(str(shortcut_data.get("StartDir", "")))
            self.txt_launchoptions.setText(str(shortcut_data.get("LaunchOptions", "")))
        else:
            self.txt_startdir.setText('"/usr/bin"')
            
        layout.addRow("App Name:", self.txt_appname)
        layout.addRow("Executable (exe):", self.txt_exe)
        layout.addRow("Start Directory:", self.txt_startdir)
        layout.addRow("Launch Options:", self.txt_launchoptions)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def get_data(self) -> dict:
        return {
            "appname": self.txt_appname.text(),
            "exe": self.txt_exe.text(),
            "StartDir": self.txt_startdir.text(),
            "icon": "",
            "ShortcutPath": "",
            "LaunchOptions": self.txt_launchoptions.text(),
            "IsHidden": 0,
            "AllowDesktopConfig": 1,
            "AllowOverlay": 1,
            "OpenVR": 0,
            "Devkit": 0,
            "DevkitGameID": "",
            "DevkitOverrideAppID": 0,
            "LastPlayTime": 0,
            "FlatpakAppID": "",
            "tags": {}
        }


class PLibraryXLTestGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLibraryXL Feature Tester & GUI")
        self.resize(1050, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.init_process_login_tab()
        self.init_config_tab()
        self.init_shortcuts_tab()

        log_group = QGroupBox("Execution Logs & Output")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(130)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        self.log("PLibraryXL GUI initialized successfully.")

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

        update_group = QGroupBox("Config Updates (Dot Notation)")
        update_layout = QFormLayout(update_group)
        
        self.txt_key_path = QLineEdit("settings.graphics.resolution")
        self.txt_key_value = QLineEdit("1920x1080")
        btn_update_single = QPushButton("Update Single Key")
        btn_update_single.clicked.connect(self.update_single_config)

        update_layout.addRow("Key Path:", self.txt_key_path)
        update_layout.addRow("Value:", self.txt_key_value)
        update_layout.addRow(btn_update_single)

        file_layout.addWidget(update_group)

        self.txt_config_editor = QTextEdit()
        self.txt_config_editor.setPlaceholderText("JSON content will appear here...")
        file_layout.addWidget(QLabel("JSON Content Viewer / Editor:"))
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

    def update_single_config(self):
        path = self.txt_config_path.text()
        key_path = self.txt_key_path.text()
        val_str = self.txt_key_value.text()

        val = val_str
        if val_str.lower() == "true":
            val = True
        elif val_str.lower() == "false":
            val = False
        else:
            try:
                if "." in val_str:
                    val = float(val_str)
                else:
                    val = int(val_str)
            except ValueError:
                pass

        success, error = PLibraryXL.update_config_value(path, key_path, val)
        if not success:
            QMessageBox.critical(self, "Error", error)
            self.log(f"Failed to update config key: {error}")
            return
        self.log(f"Successfully updated '{key_path}' = {val} in {path}")
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

        sc_group = QGroupBox("Shortcuts List & Management")
        sc_layout = QVBoxLayout(sc_group)

        self.table_shortcuts = QTableWidget()
        self.table_shortcuts.setColumnCount(5)
        self.table_shortcuts.setHorizontalHeaderLabels(["Index", "App Name", "Exe", "Start Dir", "Launch Options"])
        self.table_shortcuts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        self.log(f"Successfully loaded {count} shortcuts.")
        self.table_shortcuts.setRowCount(count)
        
        self.loaded_shortcuts_dict = shortcuts

        row = 0
        for idx_str, sc_data in shortcuts.items():
            item_idx = QTableWidgetItem(str(idx_str))
            item_idx.setData(Qt.UserRole, sc_data)
            
            self.table_shortcuts.setItem(row, 0, item_idx)
            self.table_shortcuts.setItem(row, 1, QTableWidgetItem(str(sc_data.get("appname", ""))))
            self.table_shortcuts.setItem(row, 2, QTableWidgetItem(str(sc_data.get("exe", ""))))
            self.table_shortcuts.setItem(row, 3, QTableWidgetItem(str(sc_data.get("StartDir", ""))))
            self.table_shortcuts.setItem(row, 4, QTableWidgetItem(str(sc_data.get("LaunchOptions", ""))))
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
            
            self.log("Successfully added new custom shortcut.")
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

            self.log(f"Successfully updated shortcut at index {idx}.")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PLibraryXLTestGUI()
    window.show()
    sys.exit(app.exec())