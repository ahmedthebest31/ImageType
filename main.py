import sys
import requests
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog, QMessageBox, QCheckBox,
    QDialog, QVBoxLayout, QHBoxLayout, QMenuBar, QSizePolicy, QMenu, QInputDialog
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent, QGuiApplication, QDesktopServices, QActionGroup
from PySide6.QtCore import Qt, QUrl, QSize
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

APP_VERSION = "1.6"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/ImageType/main/version.json"
GITHUB_RELEASES_URL = "https://github.com/ahmedthebest31/ImageType/releases"
CONFIG_FILE = "config.json"
LANGUAGES_DIR = "languages"
FONTS_DIR = "fonts"
TEMPLATES_DIR = "templates"
TRANSLATIONS = {}
CURRENT_LANG = "ar_eg"

# Ensure templates directory exists
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

def load_config():
    """Loads configuration from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"language": "ar_eg"}

def save_config(config):
    """Saves configuration to file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_translations():
    """Loads all translation files from the languages directory."""
    global TRANSLATIONS
    if not os.path.exists(LANGUAGES_DIR):
        QMessageBox.critical(None, "Error", "Languages directory not found!")
        return
    for filename in os.listdir(LANGUAGES_DIR):
        if filename.endswith(".json"):
            lang_code = filename.split(".")[0]
            with open(os.path.join(LANGUAGES_DIR, filename), "r", encoding="utf-8") as f:
                TRANSLATIONS[lang_code] = json.load(f)

def tr(key, *args):
    """Translates a given key based on the current language."""
    text = TRANSLATIONS.get(CURRENT_LANG, {}).get(key, key)
    return text.format(*args)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog_title_about"))
        self.setFixedSize(400, 300)
        self.setAccessibleName(tr("dialog_title_about") + " Dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        name_label = QLabel(f"<b>{tr('about_dialog_name')}</b>")
        name_label.setAccessibleName(tr("about_dialog_name"))
        layout.addWidget(name_label)

        version_label = QLabel(f"<b>{tr('about_dialog_version', APP_VERSION)}</b>")
        version_label.setAccessibleName(tr('about_dialog_version', APP_VERSION))
        layout.addWidget(version_label)

        description_text = tr("about_dialog_description_text")
        description_label = QLabel(f"<b>{tr('about_dialog_description_text')}</b><br>{description_text}")
        description_label.setWordWrap(True)
        description_label.setAccessibleName(tr("about_dialog_description_text"))
        layout.addWidget(description_label)

        developer_label = QLabel(f"<b>{tr('about_dialog_developer')}</b>")
        developer_label.setAccessibleName(tr("about_dialog_developer"))
        layout.addWidget(developer_label)

        email_label = QLabel(f"<b>{tr('about_dialog_email')}</b>")
        email_label.setAccessibleName(tr("about_dialog_email"))
        layout.addWidget(email_label)

        github_button = QPushButton(tr('about_dialog_github'))
        github_button.setAccessibleName(tr("about_dialog_github") + " Button")
        github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/ahmedthebest31/ImageType")))
        layout.addWidget(github_button)

        linkedin_button = QPushButton(tr('about_dialog_linkedin'))
        linkedin_button.setAccessibleName(tr("about_dialog_linkedin") + " Button")
        linkedin_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.linkedin.com/in/ahmedthebest")))
        layout.addWidget(linkedin_button)

        close_button = QPushButton(tr("about_dialog_close_button"))
        close_button.setAccessibleName(tr("about_dialog_close_button") + " Button")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch()

class AccessiblePlainTextEdit(QPlainTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Backtab:
            self.parentWidget().focusPreviousChild()
            event.accept()
        elif event.key() == Qt.Key.Key_Tab:
            self.parentWidget().focusNextChild()
            event.accept()
        else:
            super().keyPressEvent(event)

class ImageTextEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_image = None
        self.current_image_path = ""
        self.generated_image = None
        
        self.font_paths = {
            "regular": os.path.join(FONTS_DIR, "Amiri-Regular.ttf"),
            "bold": os.path.join(FONTS_DIR, "Amiri-Bold.ttf"),
            "italic": os.path.join(FONTS_DIR, "Amiri-Italic.ttf"),
            "bold_italic": os.path.join(FONTS_DIR, "Amiri-BoldItalic.ttf"),
            "quran": os.path.join(FONTS_DIR, "AmiriQuran.ttf")
        }
        
        global CURRENT_LANG
        config = load_config()
        CURRENT_LANG = config.get("language", "ar_eg")

        self.setWindowTitle(tr("app_title"))
        self.resize(1000, 700)
        self.setup_ui()
        self.retranslate_ui()
        self.connect_signals()
        self.load_templates_to_menu()
    
    def setup_menubar(self):
        menubar = self.menuBar()
        menubar.clear()

        file_menu = menubar.addMenu(tr("menu_file"))
        file_menu.setAccessibleName(tr("menu_file") + " Menu")
        
        new_template_action = file_menu.addAction(tr("menu_file_new_template"))
        new_template_action.triggered.connect(self.new_template)

        save_template_action = file_menu.addAction(tr("menu_file_save_template"))
        save_template_action.triggered.connect(self.save_template)

        file_menu.addSeparator()
        
        exit_action = file_menu.addAction(tr("menu_file_exit"))
        exit_action.triggered.connect(self.close)

        settings_menu = menubar.addMenu(tr("menu_settings"))
        settings_menu.setAccessibleName(tr("menu_settings") + " Menu")
        
        self.templates_menu = settings_menu.addMenu(tr("menu_settings_templates"))
        self.templates_menu.setAccessibleName(tr("menu_settings_templates") + " Menu")

        self.language_menu = settings_menu.addMenu(tr("menu_settings_language"))
        self.language_menu.setAccessibleName(tr("menu_settings_language") + " Menu")
        
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for lang_code, translations in TRANSLATIONS.items():
            lang_name = translations.get("lang_name", lang_code)
            action = self.language_menu.addAction(lang_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, lang=lang_code: self.change_language(lang))
            lang_group.addAction(action)
            if lang_code == CURRENT_LANG:
                action.setChecked(True)

        help_menu = menubar.addMenu(tr("menu_help"))
        help_menu.setAccessibleName(tr("menu_help") + " Menu")

        about_action = help_menu.addAction(tr("about_action"))
        about_action.triggered.connect(self.show_about_dialog)

        check_for_updates_action = help_menu.addAction(tr("check_for_updates_action"))
        check_for_updates_action.triggered.connect(self.check_for_updates)

    def new_template(self):
        """Resets all UI elements to their default state."""
        self.text_input.setPlainText("")
        self.fit_to_width_checkbox.setChecked(False)
        self.bold_checkbox.setChecked(False)
        self.italic_checkbox.setChecked(False)
        self.quran_checkbox.setChecked(False)
        self.text_color_combo.setCurrentIndex(0)
        self.text_position_combo.setCurrentIndex(0)
        self.image_dimensions_combo.setCurrentIndex(0)
        self.background_type_combo.setCurrentIndex(0)
        self.background_color_combo.setCurrentIndex(0)
        self.loaded_image = None
        self.current_image_path = ""
        self.image_preview.setText(tr("image_preview_placeholder"))
        QMessageBox.information(self, tr("dialog_title_success"), tr("msg_template_reset"))

    def save_template(self):
        """Saves current settings as a new template file."""
        name, ok = QInputDialog.getText(self, tr("dialog_title_save_template"), tr("msg_enter_template_name"))
        if ok and name:
            file_name = f"{name.replace(' ', '_').lower()}.json"
            template_path = os.path.join(TEMPLATES_DIR, file_name)
            
            template_data = {
                "name": name,
                "background_type": self.background_type_combo.currentText(),
                "background_color": self.background_color_combo.currentText(),
                "text_color": self.text_color_combo.currentText(),
                "image_dimensions": self.image_dimensions_combo.currentText(),
                "fit_to_width": self.fit_to_width_checkbox.isChecked(),
                "bold": self.bold_checkbox.isChecked(),
                "italic": self.italic_checkbox.isChecked(),
                "quran": self.quran_checkbox.isChecked(),
                "text_position": self.text_position_combo.currentText(),
                "image_path": self.current_image_path if self.loaded_image else ""
            }
            
            try:
                with open(template_path, "w", encoding="utf-8") as f:
                    json.dump(template_data, f, indent=4)
                QMessageBox.information(self, tr("dialog_title_success"), tr("msg_template_saved", name))
                self.load_templates_to_menu()
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_template_save_error", e))

    def load_templates_to_menu(self):
        """Loads available templates and adds them to the Templates menu."""
        self.templates_menu.clear()
        
        try:
            template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]
            if not template_files:
                self.templates_menu.addAction(tr("msg_no_templates_found")).setEnabled(False)
                return

            for filename in template_files:
                with open(os.path.join(TEMPLATES_DIR, filename), "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                    template_name = template_data.get("name", filename.replace(".json", ""))
                    action = self.templates_menu.addAction(template_name)
                    action.triggered.connect(lambda checked, data=template_data: self.apply_template(data))
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_template_load_error", e))

    def apply_template(self, template_data):
        """Applies a selected template's settings to the UI."""
        try:
            self.text_input.setPlainText(template_data.get("sample_text", ""))
            self.fit_to_width_checkbox.setChecked(template_data.get("fit_to_width", False))
            self.bold_checkbox.setChecked(template_data.get("bold", False))
            self.italic_checkbox.setChecked(template_data.get("italic", False))
            self.quran_checkbox.setChecked(template_data.get("quran", False))

            self.background_type_combo.setCurrentText(template_data.get("background_type", tr("background_type_transparent")))
            self.background_color_combo.setCurrentText(template_data.get("background_color", tr("color_white")))
            self.text_color_combo.setCurrentText(template_data.get("text_color", tr("color_black")))
            self.image_dimensions_combo.setCurrentText(template_data.get("image_dimensions", tr("image_dimensions_standard")))
            self.text_position_combo.setCurrentText(template_data.get("text_position", tr("text_position_center")))

            image_path = template_data.get("image_path")
            if image_path and os.path.exists(image_path):
                self.loaded_image = Image.open(image_path)
                self.current_image_path = image_path
            else:
                self.loaded_image = None
                self.current_image_path = ""
                if image_path:
                    QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_template_image_not_found"))
                
            self.update_preview_live()
            
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_apply_template_error", e))
    
    def setup_ui(self):
        self.setup_menubar()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        self.text_input = AccessiblePlainTextEdit()
        self.text_input.setPlaceholderText(tr("text_input_placeholder"))
        self.text_input.setAccessibleName(tr("text_input_placeholder"))
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        self.load_image_button = QPushButton(tr("load_image_button"))
        self.load_image_button.clicked.connect(self.load_image)
        self.load_image_button.setAccessibleName(tr("load_image_button") + " Button")
        grid_layout.addWidget(self.load_image_button, 1, 0)

        self.fit_to_width_checkbox = QCheckBox(tr("fit_to_width_checkbox"))
        self.fit_to_width_checkbox.setAccessibleName(tr("fit_to_width_checkbox") + " Checkbox")
        grid_layout.addWidget(self.fit_to_width_checkbox, 1, 1)
        
        text_style_layout = QHBoxLayout()
        self.text_style_label = QLabel(tr("text_style_label"))
        self.bold_checkbox = QCheckBox(tr("text_style_bold"))
        self.italic_checkbox = QCheckBox(tr("text_style_italic"))
        self.quran_checkbox = QCheckBox(tr("text_style_quran"))
        
        text_style_layout.addWidget(self.text_style_label)
        text_style_layout.addWidget(self.bold_checkbox)
        text_style_layout.addWidget(self.italic_checkbox)
        text_style_layout.addWidget(self.quran_checkbox)
        text_style_layout.addStretch()

        grid_layout.addLayout(text_style_layout, 2, 0)

        self.text_color_combo = QComboBox()
        self.text_color_combo.setAccessibleName(tr("text_color_combo_label"))
        self.retranslate_colors()
        grid_layout.addWidget(self.text_color_combo, 2, 1)

        self.text_position_combo = QComboBox()
        self.text_position_combo.setAccessibleName(tr("text_position_combo_label"))
        self.text_position_combo.addItems([
            tr("text_position_top_left"), tr("text_position_top_center"), tr("text_position_top_right"),
            tr("text_position_middle_left"), tr("text_position_center"), tr("text_position_middle_right"),
            tr("text_position_bottom_left"), tr("text_position_bottom_center"), tr("text_position_bottom_right")
        ])
        grid_layout.addWidget(self.text_position_combo, 3, 0, 1, 2)

        self.image_dimensions_combo = QComboBox()
        self.image_dimensions_combo.setAccessibleName(tr("image_dimensions_combo_label"))
        self.image_dimensions_combo.addItems([
            tr("image_dimensions_standard"),
            tr("image_dimensions_square"),
            tr("image_dimensions_portrait")
        ])
        grid_layout.addWidget(self.image_dimensions_combo, 4, 0)

        self.background_type_combo = QComboBox()
        self.background_type_combo.setAccessibleName(tr("background_type_combo_label"))
        self.background_type_combo.addItems([tr("background_type_existing"), tr("background_type_transparent"), tr("background_type_solid_color")])
        grid_layout.addWidget(self.background_type_combo, 4, 1)

        self.background_color_label = QLabel(tr("background_color_label"))
        self.background_color_combo = QComboBox()
        self.background_color_combo.setAccessibleName(tr("background_color_label"))
        self.retranslate_background_colors()
        grid_layout.addWidget(self.background_color_label, 5, 0)
        grid_layout.addWidget(self.background_color_combo, 5, 1)
        self.background_color_label.hide()
        self.background_color_combo.hide()

        self.image_quality_combo = QComboBox()
        self.image_quality_combo.setAccessibleName(tr("image_quality_combo_label"))
        self.image_quality_combo.addItems([tr("image_quality_high"), tr("image_quality_medium"), tr("image_quality_low")])
        grid_layout.addWidget(self.image_quality_combo, 6, 0)

        self.copy_button = QPushButton(tr("copy_button"))
        self.copy_button.setAccessibleName(tr("copy_button") + " Button")
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        grid_layout.addWidget(self.copy_button, 6, 1)

        self.generate_image_button = QPushButton(tr("generate_and_save_button"))
        self.generate_image_button.clicked.connect(self.generate_and_save_image)
        self.generate_image_button.setAccessibleName(tr("generate_and_save_button") + " Button")
        grid_layout.addWidget(self.generate_image_button, 7, 0, 1, 2)

        self.image_preview = QLabel(tr("image_preview_placeholder"))
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setAccessibleName(tr("image_preview_placeholder"))
        grid_layout.addWidget(self.image_preview, 0, 2, 8, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

        self.toggle_position_combo()

    def connect_signals(self):
        self.text_input.textChanged.connect(self.update_preview_live)
        self.load_image_button.clicked.connect(self.update_preview_live)
        self.fit_to_width_checkbox.stateChanged.connect(self.toggle_position_combo)
        self.fit_to_width_checkbox.stateChanged.connect(self.update_preview_live)
        
        self.bold_checkbox.stateChanged.connect(self.toggle_quran_checkbox)
        self.bold_checkbox.stateChanged.connect(self.update_preview_live)
        self.italic_checkbox.stateChanged.connect(self.toggle_quran_checkbox)
        self.italic_checkbox.stateChanged.connect(self.update_preview_live)
        self.quran_checkbox.stateChanged.connect(self.toggle_style_checkboxes)
        self.quran_checkbox.stateChanged.connect(self.update_preview_live)

        self.text_color_combo.currentTextChanged.connect(self.update_preview_live)
        self.text_position_combo.currentTextChanged.connect(self.update_preview_live)
        self.image_dimensions_combo.currentTextChanged.connect(self.update_preview_live)
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
        self.background_color_combo.currentTextChanged.connect(self.update_preview_live)
        
        self.update_preview_live()

    def update_preview_live(self):
        """Generates and updates the image preview in real-time."""
        self.generated_image = self.create_image_for_preview()
        if self.generated_image:
            self.update_preview(self.generated_image)

    def create_image_for_preview(self):
        """A simplified version of create_image() for live preview."""
        text_to_draw = self.text_input.toPlainText()
        
        background_type = self.background_type_combo.currentText()
        img_dims = self.get_image_dimensions()
        base_image = None

        if background_type == tr("background_type_existing"):
            if self.loaded_image:
                base_image = self.loaded_image.copy().resize(img_dims).convert("RGBA")
            else:
                return Image.new("RGB", img_dims, color="gray")
        elif background_type == tr("background_type_solid_color"):
            bg_color_key = self.background_color_combo.currentData()
            base_image = Image.new("RGB", img_dims, color=bg_color_key)
        else:
            base_image = Image.new("RGBA", img_dims, (255, 255, 255, 0))

        if not text_to_draw:
            return base_image

        return self.add_text_to_image(base_image, text_to_draw)

    def toggle_style_checkboxes(self, state):
        if state == Qt.CheckState.Checked:
            self.bold_checkbox.setChecked(False)
            self.italic_checkbox.setChecked(False)
            self.update_preview_live()

    def toggle_quran_checkbox(self, state):
        if state == Qt.CheckState.Checked:
            self.quran_checkbox.setChecked(False)
            self.update_preview_live()

    def retranslate_colors(self):
        colors = ["black", "white", "red", "blue", "green", "yellow", "orange", "pink"]
        self.text_color_combo.clear()
        for color in colors:
            self.text_color_combo.addItem(tr(f"color_{color}"), color)

    def retranslate_background_colors(self):
        colors = ["white", "black", "gray", "blue", "lightblue", "green", "lightgreen", "yellow", "red", "orange", "pink"]
        self.background_color_combo.clear()
        for color in colors:
            self.background_color_combo.addItem(tr(f"color_{color}"), color)

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def check_for_updates(self):
        try:
            response = requests.get(GITHUB_VERSION_URL)
            response.raise_for_status()
            latest_version_data = response.json()
            latest_version = latest_version_data.get("version")
            whats_new = latest_version_data.get("whats_new", tr("msg_no_new_features"))
            download_url = latest_version_data.get("direct_download_url", GITHUB_RELEASES_URL)

            if latest_version and self.compare_versions(latest_version, APP_VERSION) > 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(tr("dialog_title_update_available"))
                
                info_text = tr("msg_update_info", APP_VERSION, latest_version)
                full_text = f"{info_text}\n\n**{tr('whats_new_title')}:**\n{whats_new}"
                msg_box.setText(full_text)
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setAccessibleName(tr("dialog_title_update_available") + " Message Box")
                
                download_direct_button = msg_box.addButton(tr("button_direct_download"), QMessageBox.ActionRole)
                open_page_button = msg_box.addButton(tr("button_open_download_page"), QMessageBox.ActionRole)
                copy_button = msg_box.addButton(tr("button_copy_notes"), QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)

                msg_box.exec()

                clicked_button = msg_box.clickedButton()
                if clicked_button == download_direct_button:
                    QDesktopServices.openUrl(QUrl(download_url))
                elif clicked_button == open_page_button:
                    QDesktopServices.openUrl(QUrl(GITHUB_RELEASES_URL))
                elif clicked_button == copy_button:
                    clipboard = QGuiApplication.clipboard()
                    clipboard.setText(whats_new)
                    QMessageBox.information(self, tr("dialog_title_success"), tr("msg_notes_copied"))
            else:
                QMessageBox.information(self, tr("dialog_title_no_update"), tr("msg_no_update"))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_network_error", e))
        except json.JSONDecodeError:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_update_parse_error"))
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_unexpected_error", e))

    def compare_versions(self, version1, version2):
        v1_parts = [int(p) for p in version1.split('.')]
        v2_parts = [int(p) for p in version2.split('.')]

        for i in range(max(len(v1_parts), len(v2_parts))):
            part1 = v1_parts[i] if i < len(v1_parts) else 0
            part2 = v2_parts[i] if i < len(v2_parts) else 0
            if part1 > part2:
                return 1
            elif part1 < part2:
                return -1
        return 0

    def change_language(self, lang_code):
        global CURRENT_LANG
        CURRENT_LANG = lang_code
        config = load_config()
        config["language"] = lang_code
        save_config(config)
        self.retranslate_ui()
        QMessageBox.information(self, tr("dialog_title_success"), tr("msg_language_changed"))
        self.connect_signals()
        self.load_templates_to_menu()

    def retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))
        self.text_input.setPlaceholderText(tr("text_input_placeholder"))
        self.load_image_button.setText(tr("load_image_button"))
        self.fit_to_width_checkbox.setText(tr("fit_to_width_checkbox"))
        
        self.text_style_label.setText(tr("text_style_label"))
        self.bold_checkbox.setText(tr("text_style_bold"))
        self.italic_checkbox.setText(tr("text_style_italic"))
        self.quran_checkbox.setText(tr("text_style_quran"))

        self.text_color_combo.setAccessibleName(tr("text_color_combo_label"))
        self.retranslate_colors()

        self.text_position_combo.setAccessibleName(tr("text_position_combo_label"))
        self.text_position_combo.setItemText(0, tr("text_position_top_left"))
        self.text_position_combo.setItemText(1, tr("text_position_top_center"))
        self.text_position_combo.setItemText(2, tr("text_position_top_right"))
        self.text_position_combo.setItemText(3, tr("text_position_middle_left"))
        self.text_position_combo.setItemText(4, tr("text_position_center"))
        self.text_position_combo.setItemText(5, tr("text_position_middle_right"))
        self.text_position_combo.setItemText(6, tr("text_position_bottom_left"))
        self.text_position_combo.setItemText(7, tr("text_position_bottom_center"))
        self.text_position_combo.setItemText(8, tr("text_position_bottom_right"))

        self.image_dimensions_combo.setAccessibleName(tr("image_dimensions_combo_label"))
        self.image_dimensions_combo.setItemText(0, tr("image_dimensions_standard"))
        self.image_dimensions_combo.setItemText(1, tr("image_dimensions_square"))
        self.image_dimensions_combo.setItemText(2, tr("image_dimensions_portrait"))

        self.background_type_combo.setAccessibleName(tr("background_type_combo_label"))
        self.background_type_combo.setItemText(0, tr("background_type_existing"))
        self.background_type_combo.setItemText(1, tr("background_type_transparent"))
        self.background_type_combo.setItemText(2, tr("background_type_solid_color"))

        self.background_color_label.setText(tr("background_color_label"))
        self.background_color_combo.setAccessibleName(tr("background_color_label"))
        self.retranslate_background_colors()
        
        self.image_quality_combo.setAccessibleName(tr("image_quality_combo_label"))
        self.image_quality_combo.setItemText(0, tr("image_quality_high"))
        self.image_quality_combo.setItemText(1, tr("image_quality_medium"))
        self.image_quality_combo.setItemText(2, tr("image_quality_low"))
        
        self.copy_button.setText(tr("copy_button"))
        self.generate_image_button.setText(tr("generate_and_save_button"))
        self.image_preview.setText(tr("image_preview_placeholder"))

        self.setup_menubar()

        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AboutDialog):
                widget.close()
                self.show_about_dialog()

    def toggle_position_combo(self):
        is_checked = self.fit_to_width_checkbox.isChecked()
        self.text_position_combo.setEnabled(not is_checked)
        self.update_preview_live()

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, tr("load_image_button"), "", tr("file_dialog_filter"))
        if file_name:
            try:
                self.loaded_image = Image.open(file_name)
                self.current_image_path = file_name
                self.update_preview(self.loaded_image)
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_could_not_load_image", e))
        self.update_preview_live()

    def update_background_options(self, text):
        if text == tr("background_type_solid_color"):
            self.background_color_label.show()
            self.background_color_combo.show()
        else:
            self.background_color_label.hide()
            self.background_color_combo.hide()
        self.update_preview_live()

    def get_image_dimensions(self):
        dim_text = self.image_dimensions_combo.currentText()
        if tr("image_dimensions_standard") in dim_text:
            return (1200, 675)
        elif tr("image_dimensions_square") in dim_text:
            return (1080, 1080)
        elif tr("image_dimensions_portrait") in dim_text:
            return (1080, 1920)
        return (1200, 675)

    def create_image(self):
        text_to_draw = self.text_input.toPlainText()
        if not text_to_draw:
            QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_enter_text"))
            return None

        background_type = self.background_type_combo.currentText()
        img_dims = self.get_image_dimensions()
        base_image = None

        if background_type == tr("background_type_existing"):
            if self.loaded_image:
                base_image = self.loaded_image.copy().resize(img_dims).convert("RGBA")
            else:
                QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_load_image_first"))
                return None
        elif background_type == tr("background_type_solid_color"):
            bg_color_key = self.background_color_combo.currentData()
            base_image = Image.new("RGB", img_dims, color=bg_color_key)
        else:
            base_image = Image.new("RGBA", img_dims, (255, 255, 255, 0))

        return self.add_text_to_image(base_image, text_to_draw)

    def generate_and_save_image(self):
        self.generated_image = self.create_image()
        if self.generated_image:
            self.update_preview(self.generated_image)
            self.save_image(self.generated_image)

    def copy_image_to_clipboard(self):
        self.generated_image = self.create_image()
        if self.generated_image:
            self.update_preview(self.generated_image)
            qimage = self.pil_to_qimage(self.generated_image)
            clipboard = QGuiApplication.clipboard()
            clipboard.setImage(qimage)
            QMessageBox.information(self, tr("dialog_title_success"), tr("msg_image_copied"))

    def add_text_to_image(self, image, text):
        draw = ImageDraw.Draw(image)
        text_color = self.text_color_combo.currentData()
        
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()
        is_quran = self.quran_checkbox.isChecked()
        
        if is_quran:
            font_path = self.font_paths.get("quran")
        elif is_bold and is_italic:
            font_path = self.font_paths.get("bold_italic")
        elif is_bold:
            font_path = self.font_paths.get("bold")
        elif is_italic:
            font_path = self.font_paths.get("italic")
        else:
            font_path = self.font_paths.get("regular")
        
        if not os.path.exists(font_path):
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_font_not_found", font_path))
            return image

        if self.fit_to_width_checkbox.isChecked():
            lines = text.splitlines()
            formatted_lines = [get_display(arabic_reshaper.reshape(line)) for line in lines]
            
            font_size = 200
            img_width, img_height = image.size
            margin = int(img_width * 0.05)
            target_width = img_width - (2 * margin)
            
            total_text_height = 0
            while font_size > 10:
                current_font = ImageFont.truetype(font_path, font_size)
                
                wrapped_lines = []
                for line in formatted_lines:
                    words = line.split()
                    current_line = ''
                    for word in words:
                        test_line = f"{current_line} {word}".strip()
                        if draw.textlength(test_line, font=current_font) <= target_width:
                            current_line = test_line
                        else:
                            wrapped_lines.append(current_line)
                            current_line = word
                    if current_line:
                        wrapped_lines.append(current_line)
                
                total_text_height = sum(draw.textbbox((0, 0), line, font=current_font, align="right")[3] - draw.textbbox((0, 0), line, font=current_font, align="right")[1] for line in wrapped_lines)
                
                if total_text_height < img_height - (2 * margin):
                    formatted_lines = wrapped_lines
                    font = current_font
                    break
                
                font_size -= 5
                
            y = (img_height - total_text_height) / 2
            stroke_color = "black" if text_color != "black" else "white"
            for line in formatted_lines:
                line_width = draw.textlength(line, font=font)
                x = (img_width - line_width) / 2
                draw.text((x, y), line, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="right")
                y += draw.textbbox((0, 0), line, font=font, align="right")[3] - draw.textbbox((0, 0), line, font=font, align="right")[1]

        else:
            position = self.text_position_combo.currentText()
            self.draw_text_at_position(image, text, text_color, font_path, position)

        return image

    def draw_text_at_position(self, image, text, text_color, font_path, position):
        draw = ImageDraw.Draw(image)
        margin = 20
        font_size = int(image.height / 8)
        font = ImageFont.truetype(font_path, font_size)
        
        lines = text.splitlines()
        reshaped_lines = [get_display(arabic_reshaper.reshape(line)) for line in lines]
        
        total_text_height = sum(draw.textbbox((0,0), line, font=font, align="right")[3] - draw.textbbox((0,0), line, font=font, align="right")[1] for line in reshaped_lines)
        max_line_width = max(draw.textlength(line, font=font) for line in reshaped_lines)

        start_x, start_y = self.calculate_text_position(image.size, (max_line_width, total_text_height), position, margin)

        current_y = start_y
        for line in reshaped_lines:
            line_width = draw.textlength(line, font=font)

            if tr("text_position_left") in position:
                x = start_x
            elif tr("text_position_right") in position:
                x = start_x + (max_line_width - line_width)
            else: # Center
                x = start_x + (max_line_width - line_width) / 2

            stroke_color = "black" if text_color != "black" else "white"
            draw.text((x, current_y), line, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="right")
            current_y += draw.textbbox((0, 0), line, font=font, align="right")[3] - draw.textbbox((0, 0), line, font=font, align="right")[1]

    def calculate_text_position(self, image_size, text_size, position, margin):
        img_width, img_height = image_size
        text_width, text_height = text_size

        if position == tr("text_position_top_left"):
            x, y = img_width - text_width - margin, margin
        elif position == tr("text_position_top_center"):
            x, y = (img_width - text_width) / 2, margin
        elif position == tr("text_position_top_right"):
            x, y = margin, margin
        elif position == tr("text_position_middle_left"):
            x, y = img_width - text_width - margin, (img_height - text_height) / 2
        elif position == tr("text_position_center"):
            x, y = (img_width - text_width) / 2, (img_height - text_height) / 2
        elif position == tr("text_position_middle_right"):
            x, y = margin, (img_height - text_height) / 2
        elif position == tr("text_position_bottom_left"):
            x, y = img_width - text_width - margin, img_height - text_height - margin
        elif position == tr("text_position_bottom_center"):
            x, y = (img_width - text_width) / 2, img_height - text_height - margin
        elif position == tr("text_position_bottom_right"):
            x, y = margin, img_height - text_height - margin
        else: # Default to center
            x, y = (img_width - text_width) / 2, (img_height - text_height) / 2
            
        return int(x), int(y)

    def update_preview(self, image):
        qimage = self.pil_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)
        self.image_preview.setPixmap(pixmap.scaled(
            self.image_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def pil_to_qimage(self, pil_img):
        if pil_img.mode == "RGB":
            pil_img = pil_img.convert("RGBA")

        img_byte_array = io.BytesIO()
        pil_img.save(img_byte_array, format="PNG")
        qimage = QImage()
        qimage.loadFromData(img_byte_array.getvalue())
        return qimage

    def get_save_quality(self):
        quality_text = self.image_quality_combo.currentText()
        if quality_text == tr("image_quality_high"):
            return 95
        elif quality_text == tr("image_quality_medium"):
            return 80
        elif quality_text == tr("image_quality_low"):
            return 65
        return 95

    def save_image(self, image):
        save_path, selected_filter = QFileDialog.getSaveFileName(self, tr("generate_and_save_button"), "generated_image.png", tr("file_dialog_filter"))
        if save_path:
            try:
                file_format = "PNG"
                quality = self.get_save_quality()
                if ".jpg" in save_path.lower():
                    file_format = "JPEG"
                
                if file_format == "JPEG":
                    image = image.convert("RGB")

                image.save(save_path, format=file_format, quality=quality)
                QMessageBox.information(self, tr("dialog_title_success"), tr("msg_image_saved", save_path))
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_could_not_save_image", e))
        
if __name__ == "__main__":
    load_translations()
    app = QApplication(sys.argv)
    window = ImageTextEditorApp()
    window.show()
    sys.exit(app.exec())