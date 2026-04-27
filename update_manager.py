import sys
import json
import requests
import tempfile
import subprocess
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QProgressDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QCoreApplication

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/ImageType/main/version.json"

def compare_versions(v1: str, v2: str) -> int:
    p1 = [int(x) for x in v1.split('.')]
    p2 = [int(x) for x in v2.split('.')]
    p1.extend([0] * (len(p2) - len(p1)))
    p2.extend([0] * (len(p1) - len(p2)))
    if p1 > p2: return 1
    if p1 < p2: return -1
    return 0

class VersionChecker(QThread):
    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        try:
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            latest_version = data.get("version")
            if latest_version and compare_versions(latest_version, self.current_version) > 0:
                self.update_available.emit(data)
            else:
                self.no_update.emit()
        except requests.exceptions.RequestException as e:
            self.error.emit(str(e))
        except (json.JSONDecodeError, KeyError) as e:
            self.error.emit(f"Data error: {str(e)}")

class Downloader(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            temp_dir = Path(tempfile.gettempdir())
            filename = self.url.split('/')[-1] or "update.exe"
            save_path = temp_dir / filename

            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)

            self.finished.emit(str(save_path))
        except Exception as e:
            self.error.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, new_version: str, whats_new: str, tr: Callable, parent=None):
        super().__init__(parent)
        self.tr_func = tr
        self.setWindowTitle(tr("dialog_title_update_available"))
        self.setMinimumSize(450, 350)
        self.setAccessibleName(tr("dialog_title_update_available") + " Dialog")

        layout = QVBoxLayout(self)

        title_label = QLabel(f"<b>{tr('dialog_title_update_available')} - v{new_version}</b>")
        title_label.setAccessibleName(f"New version {new_version} available")
        layout.addWidget(title_label)

        whats_new_label = QLabel(f"<b>{tr('whats_new_title')}:</b>")
        layout.addWidget(whats_new_label)

        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlainText(whats_new)
        self.text_area.setAccessibleName(tr("whats_new_title"))
        layout.addWidget(self.text_area)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_skip = QPushButton("Skip This Version")
        self.btn_skip.setText(tr("button_skip_version") if tr("button_skip_version") != "button_skip_version" else "Skip This Version")
        self.btn_skip.setAccessibleName("Skip this version")
        
        self.btn_remind = QPushButton("Remind Me Later")
        self.btn_remind.setText(tr("button_remind_later") if tr("button_remind_later") != "button_remind_later" else "Remind Me Later")
        self.btn_remind.setAccessibleName("Remind me later")

        self.btn_update = QPushButton("Update Now")
        self.btn_update.setText(tr("button_update_now") if tr("button_update_now") != "button_update_now" else "Update Now")
        self.btn_update.setAccessibleName("Update now")
        self.btn_update.setStyleSheet("font-weight: bold;")

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_remind)
        btn_layout.addWidget(self.btn_update)
        layout.addLayout(btn_layout)

        self.btn_skip.clicked.connect(self.reject_skip)
        self.btn_remind.clicked.connect(self.reject_remind)
        self.btn_update.clicked.connect(self.accept_update)

        self.action = "remind"

    def reject_skip(self):
        self.action = "skip"
        self.reject()

    def reject_remind(self):
        self.action = "remind"
        self.reject()

    def accept_update(self):
        self.action = "update"
        self.accept()

class UpdateManager(QObject):
    def __init__(self, parent_widget, tr_func: Callable, load_config: Callable, save_config: Callable, current_version: str):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.tr = tr_func
        self.load_config = load_config
        self.save_config = save_config
        self.current_version = current_version
        self.silent = False
        self.progress_dialog = None
        self.checker_thread = None
        self.downloader_thread = None

    def check_for_updates(self, silent: bool = True):
        self.silent = silent

        if not silent:
            self.progress_dialog = QProgressDialog(
                self.tr("checking_updates") if self.tr("checking_updates") != "checking_updates" else "Checking for updates...",
                "", 0, 0, self.parent_widget
            )
            self.progress_dialog.setWindowTitle(self.tr("dialog_title_about"))
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.setModal(True)
            self.progress_dialog.show()

        self.checker_thread = VersionChecker(self.current_version, self)
        self.checker_thread.update_available.connect(self._on_update_available)
        self.checker_thread.no_update.connect(self._on_no_update)
        self.checker_thread.error.connect(self._on_error)
        self.checker_thread.finished.connect(self._cleanup_checker)
        self.checker_thread.start()

    def _cleanup_checker(self):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _on_update_available(self, data: dict):
        new_version = data.get("version", "")
        
        if self.silent:
            config = self.load_config()
            if config.get("skipped_version") == new_version:
                return

        whats_new_data = data.get("whats_new", {})
        config = self.load_config()
        lang = config.get("language", "en")
        
        if isinstance(whats_new_data, dict):
            whats_new = whats_new_data.get(lang, self.tr("msg_no_new_features"))
        else:
            whats_new = str(whats_new_data)

        dialog = UpdateDialog(new_version, whats_new, self.tr, self.parent_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.action == "update":
                self._start_download(data.get("direct_download_url"))
        else:
            if dialog.action == "skip":
                config["skipped_version"] = new_version
                self.save_config(config)

    def _on_no_update(self):
        if not self.silent:
            QMessageBox.information(self.parent_widget, self.tr("dialog_title_no_update"), self.tr("msg_no_update"))

    def _on_error(self, error_msg: str):
        if not self.silent:
            QMessageBox.critical(self.parent_widget, self.tr("dialog_title_error"), self.tr("msg_network_error", error_msg))

    def _start_download(self, url: str):
        if not url:
            QMessageBox.critical(self.parent_widget, self.tr("dialog_title_error"), "Download URL is empty.")
            return

        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self.parent_widget)
        self.progress_dialog.setWindowTitle("Downloading Update")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        
        self.downloader_thread = Downloader(url, self)
        self.progress_dialog.canceled.connect(self.downloader_thread.terminate)
        
        self.downloader_thread.progress.connect(self.progress_dialog.setValue)
        self.downloader_thread.finished.connect(self._on_download_finished)
        self.downloader_thread.error.connect(self._on_download_error)
        self.downloader_thread.start()
        self.progress_dialog.show()

    def _on_download_finished(self, file_path: str):
        if self.progress_dialog:
            self.progress_dialog.close()

        try:
            subprocess.Popen([file_path, "/VERYSILENT", "/SUPPRESSMSGBOXES"])
            QCoreApplication.quit()
        except Exception as e:
            QMessageBox.critical(self.parent_widget, self.tr("dialog_title_error"), f"Failed to launch installer:\n{e}")

    def _on_download_error(self, error_msg: str):
        if self.progress_dialog:
            self.progress_dialog.close()
        
        reply = QMessageBox.critical(
            self.parent_widget, 
            self.tr("dialog_title_error"), 
            f"Download failed:\n{error_msg}\n\nDo you want to retry?",
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Retry:
            self._start_download(self.downloader_thread.url)
