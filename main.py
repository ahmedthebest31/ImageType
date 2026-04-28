import sys
import requests
import json
import os
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog, QMessageBox, QCheckBox,
    QDialog, QVBoxLayout, QHBoxLayout, QMenuBar, QSizePolicy, QMenu, QInputDialog, QSpinBox
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent, QGuiApplication, QDesktopServices, QAction, QActionGroup, QFontDatabase
from PySide6.QtCore import Qt, QUrl, QSize, QThread, Signal
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageQt import ImageQt
from typing import Optional, Dict, Any
import io
import arabic_reshaper
from bidi.algorithm import get_display

APP_VERSION = "1.9"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/ImageType/main/version.json"
GITHUB_RELEASES_URL = "https://github.com/ahmedthebest31/ImageType/releases"
GITHUB_URL = "https://github.com/ahmedthebest31/ImageType"
LINKEDIN_URL = "https://www.linkedin.com/in/ahmedthebest"

class PathProvider:
    @staticmethod
    def get_app_dir() -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).resolve().parent

    @staticmethod
    def is_installed() -> bool:
        app_dir = str(PathProvider.get_app_dir()).replace("\\", "/").lower()
        system_folders = ["program files", "appdata", "/usr/bin", "/opt", "/applications"]
        return any(folder in app_dir for folder in system_folders)

    @staticmethod
    def get_user_data_dir() -> Path:
        if PathProvider.is_installed():
            return Path.home() / "Documents" / "AhmedSamy.imageType"
        else:
            return PathProvider.get_app_dir() / "data"

    @classmethod
    def setup_data_dir(cls):
        base_dir = cls.get_user_data_dir()
        base_dir.mkdir(parents=True, exist_ok=True)
        
        folders = ["themes", "languages", "fonts", "templates"]
        app_dir = cls.get_app_dir()

        for folder in folders:
            target_folder = base_dir / folder
            source_folder = app_dir / folder
            
            if not target_folder.exists() and source_folder.exists():
                shutil.copytree(source_folder, target_folder)
            elif source_folder.exists() and folder in ["languages", "themes"]:
                for file_path in source_folder.iterdir():
                    if file_path.is_file():
                        shutil.copy2(file_path, target_folder / file_path.name)
            elif not target_folder.exists():
                target_folder.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_path(cls, path_name: str) -> str:
        return str(cls.get_user_data_dir() / path_name)

PathProvider.setup_data_dir()

CONFIG_FILE = PathProvider.get_path("config.json")
LANGUAGES_DIR = PathProvider.get_path("languages")
FONTS_DIR = PathProvider.get_path("fonts")
TEMPLATES_DIR = PathProvider.get_path("templates")
THEMES_DIR = PathProvider.get_path("themes")
TRANSLATIONS = {}
CURRENT_LANG = "en"

def load_config():
    """Loads configuration from file."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            config.setdefault("language", "en")
            config.setdefault("theme", "dark_theme.qss")
            return config
    return {"language": "en", "theme": "dark_theme.qss"}

def save_config(config):
    """Saves configuration to file."""
    with open(Path(CONFIG_FILE), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_translations():
    """Loads all translation files from the languages directory."""
    global TRANSLATIONS
    lang_dir = Path(LANGUAGES_DIR)
    if not lang_dir.exists():
        QMessageBox.critical(None, "Error", "Languages directory not found!")
        return
    for filepath in lang_dir.iterdir():
        if filepath.is_file() and filepath.suffix == ".json":
            lang_code = filepath.stem
            with open(filepath, "r", encoding="utf-8") as f:
                TRANSLATIONS[lang_code] = json.load(f)

def tr(key, *args):
    """Translates a given key based on the current language."""
    text = TRANSLATIONS.get(CURRENT_LANG, {}).get(key)
    if text is None:
        text = TRANSLATIONS.get("en", {}).get(key, key)
    return text.format(*args)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog_title_about"))
        self.setFixedSize(400, 250)
        self.setAccessibleName(tr("dialog_title_about") + " Dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        name_label = QLabel(f"<b>{tr('about_dialog_name')}</b>")
        name_label.setAccessibleName(tr("about_dialog_name"))
        layout.addWidget(name_label)

        version_label = QLabel(f"<b>{tr('about_dialog_version', APP_VERSION)}</b>")
        version_label.setAccessibleName(tr('about_dialog_version', APP_VERSION))
        layout.addWidget(version_label)

        description_label = QLabel(tr("about_dialog_description_text"))
        description_label.setWordWrap(True)
        description_label.setAccessibleName(tr("about_dialog_description_text"))
        layout.addWidget(description_label)

        developer_label = QLabel(f"{tr('about_dialog_developer')}: Ahmed Samy")
        developer_label.setAccessibleName(tr("about_dialog_developer"))
        layout.addWidget(developer_label)

        email_label = QLabel(f"{tr('about_dialog_email')}: ahmedthebest31@gmail.com")
        email_label.setOpenExternalLinks(True)
        email_label.setAccessibleName(tr("about_dialog_email"))
        layout.addWidget(email_label)

        layout.addStretch()

        close_button = QPushButton(tr("about_dialog_close_button"))
        close_button.setAccessibleName(tr("about_dialog_close_button") + " Button")
        close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

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

class ImageProcessorThread(QThread):
    finished_image = Signal(object, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = {}
        self.action = "preview"
        self.is_cancelled = False

    def setup(self, params: Dict[str, Any], action: str = "preview"):
        self.params = params
        self.action = action
        self.is_cancelled = False

    def run(self):
        processor = self.params.pop("processor", None)
        if not processor:
            return

        try:
            image = processor.create_image(**self.params)
            if self.is_cancelled:
                return

            qimage = None
            if image:
                # Decoupled thread-safe deep copy using ImageQt
                qim = ImageQt(image)
                qimage = qim.copy()
            
            if not self.is_cancelled:
                self.finished_image.emit(image, qimage, self.action)
        except Exception as e:
            print(f"Error in image processing thread: {e}")

class ImageTextEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_image = None
        self.current_image_path = ""
        self.generated_image = None

        self.font_paths = {
            "regular": str(Path(FONTS_DIR) / "Amiri" / "Amiri-Regular.ttf"),
            "bold": str(Path(FONTS_DIR) / "Amiri" / "Amiri-Bold.ttf"),
            "italic": str(Path(FONTS_DIR) / "Amiri" / "Amiri-Italic.ttf"),
            "bold_italic": str(Path(FONTS_DIR) / "Amiri" / "Amiri-BoldItalic.ttf")
        }

        self.processing_thread = ImageProcessorThread(self)
        self.processing_thread.finished_image.connect(self.on_image_processed)

        global CURRENT_LANG
        config = load_config()
        CURRENT_LANG = config.get("language", "en")

        self.apply_theme(config.get("theme", "dark_theme.qss"))

        self.setWindowTitle(tr("app_title"))
        self.resize(1000, 700)
        self.setup_ui()
        self.retranslate_ui()
        self.set_default_settings()
        self.connect_signals()
        self.load_templates_to_menu()
        self.load_themes_to_menu()
        self.update_preview_live()

        from update_manager import UpdateManager
        self.update_manager = UpdateManager(self, tr, load_config, save_config, APP_VERSION)
        self.update_manager.check_for_updates(silent=True)

    def set_default_settings(self):
        self._set_combo_by_data(self.background_type_combo, "solid")
        self._set_combo_by_data(self.background_color_combo, "black")
        self._set_combo_by_data(self.text_color_combo, "white")
        self._set_combo_by_data(self.text_position_combo, "center")
        self.update_background_options()
        self.toggle_position_combo()

    def setup_menubar(self):
        menubar = self.menuBar()
        menubar.clear()

        # File Menu
        file_menu = menubar.addMenu(tr("menu_file"))
        new_template_action = file_menu.addAction(tr("menu_file_new_template"))
        new_template_action.triggered.connect(self.new_template)
        save_template_action = file_menu.addAction(tr("menu_file_save_template"))
        save_template_action.triggered.connect(self.save_template)
        file_menu.addSeparator()
        exit_action = file_menu.addAction(tr("menu_file_exit"))
        exit_action.triggered.connect(self.close)

        # Settings Menu
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self.templates_menu = settings_menu.addMenu(tr("menu_settings_templates"))
        self.themes_menu = settings_menu.addMenu(tr("menu_settings_themes"))
        self.language_menu = settings_menu.addMenu(tr("menu_settings_language"))

        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for lang_code, translations in sorted(TRANSLATIONS.items()):
            lang_name = translations.get("lang_name", lang_code)
            action = self.language_menu.addAction(lang_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, lang=lang_code: self.change_language(lang))
            lang_group.addAction(action)
            if lang_code == CURRENT_LANG:
                action.setChecked(True)

        # Help Menu
        help_menu = menubar.addMenu(tr("menu_help"))
        about_action = help_menu.addAction(tr("about_action"))
        about_action.triggered.connect(self.show_about_dialog)
        check_for_updates_action = help_menu.addAction(tr("check_for_updates_action"))
        check_for_updates_action.triggered.connect(lambda: self.update_manager.check_for_updates(silent=False))
        help_menu.addSeparator()
        github_action = help_menu.addAction(tr("about_dialog_github"))
        github_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        linkedin_action = help_menu.addAction(tr("about_dialog_linkedin"))
        linkedin_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(LINKEDIN_URL)))

    def new_template(self):
        """Resets all UI elements to their default state."""
        self.text_input.setPlainText("")
        self.font_style_combo.setCurrentIndex(0)
        self.fit_to_width_checkbox.setChecked(False)
        self.image_dimensions_combo.setCurrentIndex(0)
        self.enable_shadow_checkbox.setChecked(False)
        self.loaded_image = None
        self.current_image_path = ""
        
        self.set_default_settings()
        self.update_preview_live()
        
        QMessageBox.information(self, tr("dialog_title_success"), tr("msg_template_reset"))

    def save_template(self):
        """Saves current settings as a new template file."""
        name, ok = QInputDialog.getText(self, tr("dialog_title_save_template"), tr("msg_enter_template_name"))
        if ok and name:
            file_name = f"{name.replace(' ', '_').lower()}.json"
            template_path = Path(TEMPLATES_DIR) / file_name

            template_data = {
                "name": name,
                "font_style": self.font_style_combo.currentData(),
                "background_type": self.background_type_combo.currentData(),
                "background_color": self.background_color_combo.currentData(),
                "text_color": self.text_color_combo.currentData(),
                "image_dimensions": self.image_dimensions_combo.currentData(),
                "fit_to_width": self.fit_to_width_checkbox.isChecked(),
                "enable_shadow": self.enable_shadow_checkbox.isChecked(),
                "text_position": self.text_position_combo.currentData(),
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
            templates_dir = Path(TEMPLATES_DIR)
            if not templates_dir.exists():
                return
            template_files = [f.name for f in templates_dir.iterdir() if f.is_file() and f.suffix == ".json"]
            if not template_files:
                no_templates_action = self.templates_menu.addAction(tr("msg_no_templates_found"))
                no_templates_action.setEnabled(False)
                return

            for filename in sorted(template_files):
                try:
                    with open(templates_dir / filename, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                        template_name = template_data.get("name", Path(filename).stem)
                        action = self.templates_menu.addAction(template_name)
                        action.triggered.connect(lambda checked, data=template_data: self.apply_template(data))
                except (json.JSONDecodeError, KeyError):
                    # Silently ignore broken template files
                    continue
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_template_load_error", e))

    def apply_template(self, template_data):
        """Applies a selected template's settings to the UI."""
        try:
            self.text_input.setPlainText(template_data.get("sample_text", ""))

            self._set_combo_by_data(self.font_style_combo, template_data.get("font_style"))
            self.fit_to_width_checkbox.setChecked(template_data.get("fit_to_width", False))
            self._set_combo_by_data(self.background_type_combo, template_data.get("background_type"))
            self._set_combo_by_data(self.background_color_combo, template_data.get("background_color"))
            self._set_combo_by_data(self.text_color_combo, template_data.get("text_color"))
            self._set_combo_by_data(self.image_dimensions_combo, template_data.get("image_dimensions"))
            self.enable_shadow_checkbox.setChecked(template_data.get("enable_shadow", False))
            self._set_combo_by_data(self.text_position_combo, template_data.get("text_position"))

            image_path = template_data.get("image_path")
            if image_path and Path(image_path).exists():
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

    def _set_combo_by_data(self, combo, data):
        """Helper to set a QComboBox's current index by its item data."""
        if data is None: return
        index = combo.findData(data)
        if index != -1:
            combo.setCurrentIndex(index)

    def load_themes_to_menu(self):
        """Loads available themes and adds them to the Themes menu."""
        self.themes_menu.clear()
        config = load_config()
        current_theme = config.get("theme", "dark_theme.qss")

        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        try:
            themes_dir = Path(THEMES_DIR)
            if themes_dir.exists():
                theme_files = [f.name for f in themes_dir.iterdir() if f.is_file() and f.suffix == ".qss"]
                for filename in sorted(theme_files):
                    theme_stem = Path(filename).stem
                    theme_key = f"theme_{theme_stem}"
                    theme_fallback_name = theme_stem.replace("_", " ").title()
                    
                    translated_name = tr(theme_key)
                    if translated_name == theme_key:
                        translated_name = theme_fallback_name

                    action = self.themes_menu.addAction(translated_name)
                    action.setCheckable(True)
                    action.triggered.connect(lambda checked, file=filename: self.change_theme(file))
                    theme_group.addAction(action)
                    if filename == current_theme:
                        action.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), f"Could not load themes: {e}")

    def change_theme(self, theme_file):
        """Applies the selected theme and saves it to the config."""
        self.apply_theme(theme_file)
        config = load_config()
        config["theme"] = theme_file
        save_config(config)

    def apply_theme(self, theme_file):
        """Reads a QSS file and applies it to the application."""
        theme_path = Path(THEMES_DIR) / theme_file
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                style_sheet = f.read()
            QApplication.instance().setStyleSheet(style_sheet)
        except FileNotFoundError:
            print(f"Warning: Theme file not found at {theme_path}. Using default.")
            QApplication.instance().setStyleSheet("")
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), f"Could not apply theme: {e}")

    def setup_ui(self):
        self.setup_menubar()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        # Row 0: Text Input
        self.text_input = AccessiblePlainTextEdit()
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        # Row 1: Fit to Width and Font Size
        self.load_image_button = QPushButton()
        
        row1_layout = QHBoxLayout()
        self.fit_to_width_checkbox = QCheckBox()
        self.font_size_label = QLabel()
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(14, 100)
        self.font_size_spinbox.setValue(24)
        
        row1_layout.addWidget(self.fit_to_width_checkbox)
        row1_layout.addStretch()
        row1_layout.addWidget(self.font_size_label)
        row1_layout.addWidget(self.font_size_spinbox)
        grid_layout.addLayout(row1_layout, 1, 0, 1, 2)

        # Row 2: Font Family and Style
        self.font_family_combo = QComboBox()
        grid_layout.addWidget(self.font_family_combo, 2, 0)
        self.font_style_combo = QComboBox()
        grid_layout.addWidget(self.font_style_combo, 2, 1)

        # Row 3: Text Color and Position
        self.text_color_combo = QComboBox()
        self.enable_shadow_checkbox = QCheckBox()
        row3_left_layout = QHBoxLayout()
        row3_left_layout.addWidget(self.text_color_combo)
        row3_left_layout.addWidget(self.enable_shadow_checkbox)
        grid_layout.addLayout(row3_left_layout, 3, 0)
        self.text_position_combo = QComboBox()
        grid_layout.addWidget(self.text_position_combo, 3, 1)

        # Row 4: Image Dimensions and Background Type
        self.image_dimensions_combo = QComboBox()
        grid_layout.addWidget(self.image_dimensions_combo, 4, 0)
        self.background_type_combo = QComboBox()
        grid_layout.addWidget(self.background_type_combo, 4, 1)

        # Row 5: Load Image Button (conditionally visible)
        grid_layout.addWidget(self.load_image_button, 5, 0, 1, 2)

        # Row 6: Background Color
        self.background_color_label = QLabel()
        self.background_color_combo = QComboBox()
        grid_layout.addWidget(self.background_color_label, 6, 0)
        grid_layout.addWidget(self.background_color_combo, 6, 1)

        # Row 7: Image Quality and Copy
        self.image_quality_combo = QComboBox()
        grid_layout.addWidget(self.image_quality_combo, 7, 0)
        self.copy_button = QPushButton()
        grid_layout.addWidget(self.copy_button, 7, 1)

        # Row 8: Generate and Save
        self.generate_image_button = QPushButton()
        grid_layout.addWidget(self.generate_image_button, 8, 0, 1, 2)

        # Image Preview (spans all rows)
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.image_preview, 0, 2, 9, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

    def connect_signals(self):
        self.text_input.textChanged.connect(self.update_preview_live)
        self.load_image_button.clicked.connect(self.load_image)
        self.fit_to_width_checkbox.stateChanged.connect(self.toggle_position_combo)
        self.font_size_spinbox.valueChanged.connect(self.update_preview_live)
        self.font_family_combo.currentTextChanged.connect(self.on_font_family_changed)
        self.font_style_combo.currentIndexChanged.connect(self.update_preview_live)
        self.text_color_combo.currentIndexChanged.connect(self.update_preview_live)
        self.enable_shadow_checkbox.toggled.connect(self.update_preview_live)
        self.text_position_combo.currentIndexChanged.connect(self.update_preview_live)
        self.image_dimensions_combo.currentIndexChanged.connect(self.update_preview_live)
        self.background_type_combo.currentIndexChanged.connect(self.update_background_options)
        self.background_color_combo.currentIndexChanged.connect(self.update_preview_live)
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        self.generate_image_button.clicked.connect(self.generate_and_save_image)

    def retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))
        self.text_input.setPlaceholderText(tr("text_input_placeholder"))
        self.load_image_button.setText(tr("load_image_button"))
        self.fit_to_width_checkbox.setText(tr("fit_to_width_checkbox"))
        self.font_size_label.setText(tr("font_size_label"))
        self.font_size_spinbox.setAccessibleName(tr("font_size_label"))
        self.enable_shadow_checkbox.setText(tr("enable_shadow_checkbox"))
        self.enable_shadow_checkbox.setAccessibleName(tr("enable_shadow_checkbox"))

        self._populate_font_style_combo()
        self._populate_font_family_combo()

        self._populate_combo(self.text_color_combo, tr("text_color_combo_label"), {
            "black": "color_black", "white": "color_white", "red": "color_red", "blue": "color_blue",
            "green": "color_green", "yellow": "color_yellow", "orange": "color_orange", "pink": "color_pink"
        })

        self._populate_combo(self.text_position_combo, tr("text_position_combo_label"), {
            "top_left": "text_position_top_left", "top_center": "text_position_top_center", "top_right": "text_position_top_right",
            "middle_left": "text_position_middle_left", "center": "text_position_center", "middle_right": "text_position_middle_right",
            "bottom_left": "text_position_bottom_left", "bottom_center": "text_position_bottom_center", "bottom_right": "text_position_bottom_right"
        })

        self._populate_combo(self.image_dimensions_combo, tr("image_dimensions_combo_label"), {
            (1200, 675): "image_dimensions_standard", (1080, 1080): "image_dimensions_square", (1080, 1920): "image_dimensions_portrait"
        })

        self._populate_combo(self.background_type_combo, tr("background_type_combo_label"), {
            "existing": "background_type_existing", "transparent": "background_type_transparent", "solid": "background_type_solid_color"
        })

        self._populate_combo(self.background_color_combo, tr("background_color_label"), {
            "white": "color_white", "black": "color_black", "gray": "color_gray", "blue": "color_blue", "lightblue": "color_lightblue",
            "green": "color_green", "lightgreen": "color_lightgreen", "yellow": "color_yellow", "red": "color_red", "orange": "color_orange", "pink": "color_pink"
        })

        self._populate_combo(self.image_quality_combo, tr("image_quality_combo_label"), {
            95: "image_quality_high", 80: "image_quality_medium", 65: "image_quality_low"
        })

        self.copy_button.setText(tr("copy_button"))
        self.generate_image_button.setText(tr("generate_and_save_button"))
        self.image_preview.setText(tr("image_preview_placeholder"))
        self.background_color_label.setText(tr("background_color_label"))

        self.setup_menubar()
        self.update_background_options()
        self.toggle_position_combo()
        self.update_preview_live()
        self.on_font_family_changed()

    def _populate_font_style_combo(self):
        """Populates the font style dropdown with available Amiri styles."""
        current_data = self.font_style_combo.currentData()
        self.font_style_combo.clear()
        self.font_style_combo.setAccessibleName(tr("font_style_combo_label"))
        styles = {
            "regular": "font_style_regular",
            "bold": "font_style_bold",
            "italic": "font_style_italic",
            "bold_italic": "font_style_bold_italic"
        }
        for data, key in styles.items():
            self.font_style_combo.addItem(tr(key), data)
        self._set_combo_by_data(self.font_style_combo, current_data)

    def _populate_font_family_combo(self):
        """Populates the font family dropdown with system fonts."""
        current_text = self.font_family_combo.currentText()
        self.font_family_combo.clear()
        self.font_family_combo.setAccessibleName(tr("font_family_combo_label"))

        db = QFontDatabase()
        families = db.families()

        self.font_family_combo.addItem("Amiri") # Add our bundled font first
        for family in sorted(families):
            if family != "Amiri":
                self.font_family_combo.addItem(family)

        if current_text:
            self.font_family_combo.setCurrentText(current_text)
        else:
            self.font_family_combo.setCurrentText("Amiri")

    def on_font_family_changed(self, family=None):
        """Handles changes in the selected font family."""
        # Font style (bold, italic) will be applied to system fonts where possible.
        # The preview is updated to reflect the change.
        self.update_preview_live()


    def _populate_combo(self, combo, label, items):
        current_data = combo.currentData()
        combo.clear()
        combo.setAccessibleName(label)
        for data, key in items.items():
            combo.addItem(tr(key), data)
        self._set_combo_by_data(combo, current_data)

    def toggle_position_combo(self, *args, **kwargs):
        is_checked = self.fit_to_width_checkbox.isChecked()
        self.text_position_combo.setEnabled(not is_checked)
        self.font_size_spinbox.setEnabled(not is_checked)
        self.update_preview_live()

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    # Legacy update checking moved to update_manager.py

    def change_language(self, lang_code):
        global CURRENT_LANG
        CURRENT_LANG = lang_code
        config = load_config()
        config["language"] = lang_code
        save_config(config)
        load_translations() # Reload translations from disk to ensure any new keys are available
        self.retranslate_ui()
        self.load_templates_to_menu()
        self.load_themes_to_menu()

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, tr("load_image_button"), "", tr("file_dialog_filter"))
        if file_name:
            try:
                self.loaded_image = Image.open(file_name)
                self.current_image_path = file_name
                self.update_preview_live()
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_could_not_load_image", e))

    def update_background_options(self, *args, **kwargs):
        is_solid_color = self.background_type_combo.currentData() == "solid"
        self.background_color_label.setVisible(is_solid_color)
        self.background_color_combo.setVisible(is_solid_color)

        is_existing_image = self.background_type_combo.currentData() == "existing"
        self.load_image_button.setVisible(is_existing_image)

        self.update_preview_live()

    def get_current_params(self):
        return {
            "text": self.text_input.toPlainText(),
            "background_type": self.background_type_combo.currentData(),
            "img_dims": self.image_dimensions_combo.currentData(),
            "bg_color": self.background_color_combo.currentData(),
            "loaded_image": self.loaded_image,
            "font_family": self.font_family_combo.currentText(),
            "font_style": self.font_style_combo.currentData() or "regular",
            "text_color": self.text_color_combo.currentData(),
            "fit_to_width": self.fit_to_width_checkbox.isChecked(),
            "enable_shadow": self.enable_shadow_checkbox.isChecked(),
            "text_position": self.text_position_combo.currentData(),
            "font_size": self.font_size_spinbox.value() * 5
        }

    def _dispatch_thread(self, action="preview"):
        if self.processing_thread.isRunning():
            self.processing_thread.is_cancelled = True
            self.processing_thread.wait()

        params = self.get_current_params()
        params["for_preview"] = (action == "preview")
        params["processor"] = self
        self.processing_thread.setup(params, action)
        self.processing_thread.start()

    def on_image_processed(self, image, qimage, action):
        if not image or not qimage:
            return

        self.generated_image = image
        pixmap = QPixmap.fromImage(qimage)
        self.image_preview.setPixmap(pixmap.scaled(
            self.image_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        if action == "save":
            self.save_image(self.generated_image)
        elif action == "copy":
            clipboard = QGuiApplication.clipboard()
            clipboard.setImage(qimage)
            if not self.generated_image.mode == 'RGBA' or self.background_type_combo.currentData() != "transparent":
                QMessageBox.information(self, tr("dialog_title_success"), tr("msg_image_copied"))

    def update_preview_live(self, *args, **kwargs):
        """Generates and updates the image preview in real-time using a background thread."""
        self._dispatch_thread("preview")

    def generate_and_save_image(self):
        if not self.text_input.toPlainText():
            QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_enter_text"))
            return
        if self.background_type_combo.currentData() == "existing" and not self.loaded_image:
            QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_load_image_first"))
            return
        self._dispatch_thread("save")

    def copy_image_to_clipboard(self):
        if not self.text_input.toPlainText():
            QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_enter_text"))
            return
        if self.background_type_combo.currentData() == "existing" and not self.loaded_image:
            QMessageBox.warning(self, tr("dialog_title_warning"), tr("msg_load_image_first"))
            return
        self._dispatch_thread("copy")

    def create_image(self, text, background_type, img_dims, bg_color, loaded_image, font_family, font_style, text_color, fit_to_width, text_position, font_size=120, for_preview=False, enable_shadow=False) -> Optional[Image.Image]:
        if not text and not for_preview:
            return None

        base_image = None

        if background_type == "existing":
            if loaded_image:
                base_image = loaded_image.copy().resize(img_dims, Image.Resampling.LANCZOS).convert("RGBA")
            elif for_preview:
                return Image.new("RGB", img_dims, color="gray")
            else:
                return None
        elif background_type == "solid":
            base_image = Image.new("RGB", img_dims, color=bg_color)
        else: # Transparent
            base_image = Image.new("RGBA", img_dims, (255, 255, 255, 0))

        if text:
            return self.add_text_to_image(base_image, text, font_family, font_style, text_color, fit_to_width, text_position, font_size, enable_shadow)
        return base_image

    def add_text_to_image(self, image, text, font_family, font_style, text_color, fit_to_width, text_position, font_size, enable_shadow):
        amiri_fallback_path = self.font_paths.get("regular")

        font_identifier = None
        if font_family == "Amiri":
            font_identifier = self.font_paths.get(font_style, amiri_fallback_path)
        else:
            style_str = ""
            if font_style == "bold":
                style_str = " Bold"
            elif font_style == "italic":
                style_str = " Italic"
            elif font_style == "bold_italic":
                style_str = " Bold Italic"
            font_identifier = f"{font_family}{style_str}"

        draw = ImageDraw.Draw(image)

        if not Path(font_identifier).exists() and font_family == "Amiri":
             return image

        # Font fallback mechanism for unsupported characters (like Arabic)
        try:
            test_font = ImageFont.truetype(font_identifier, 20)
            
            missing_boxes = [
                test_font.getmask('\uFFFF').getbbox(),
                test_font.getmask('\uFFFD').getbbox(),
                test_font.getmask('\u0000').getbbox()
            ]
            
            reshaped_text = get_display(arabic_reshaper.reshape(text))
            
            for char in set(reshaped_text):
                if char.isspace(): continue
                char_bbox = test_font.getmask(char).getbbox()
                if char_bbox is None or char_bbox in missing_boxes:
                    # Unsupported character spotted, fallback to Amiri
                    font_identifier = amiri_fallback_path
                    font_family = "Amiri"
                    break
        except Exception:
            font_identifier = amiri_fallback_path
            font_family = "Amiri"

        if fit_to_width:
            self.draw_text_fit_to_width(draw, text, font_identifier, text_color, image.size, enable_shadow)
        else:
            self.draw_text_at_position(draw, text, font_identifier, text_color, image.size, text_position, font_size, enable_shadow)

        return image

    def draw_text_fit_to_width(self, draw, text, font_identifier, text_color, image_size, enable_shadow=False):
        img_width, img_height = image_size
        margin = int(img_width * 0.05)
        target_width = img_width - (2 * margin)

        low_size = 10
        high_size = 1000
        best_size = low_size

        # Binary Search Optimization for Font Sizing
        while low_size <= high_size:
            mid_size = (low_size + high_size) // 2
            try:
                font = ImageFont.truetype(font_identifier, mid_size)
            except IOError:
                font = ImageFont.truetype(self.font_paths.get("regular"), mid_size)

            wrapped_text = self.wrap_text(draw, text, font, target_width)
            reshaped_text = get_display(arabic_reshaper.reshape(wrapped_text))
            text_height = draw.multiline_textbbox((0,0), reshaped_text, font=font, align="center")[3]

            if text_height < img_height - (2 * margin):
                best_size = mid_size
                low_size = mid_size + 1
            else:
                high_size = mid_size - 1

        try:
            font = ImageFont.truetype(font_identifier, best_size)
        except IOError:
            font = ImageFont.truetype(self.font_paths.get("regular"), best_size)

        wrapped_text = self.wrap_text(draw, text, font, target_width)
        reshaped_text = get_display(arabic_reshaper.reshape(wrapped_text))
        text_height = draw.multiline_textbbox((0,0), reshaped_text, font=font, align="center")[3]

        y = (img_height - text_height) / 2
        stroke_color = "black" if text_color != "black" else "white"
        
        if enable_shadow:
            shadow_color = (0, 0, 0, 128) if text_color in ["white", "yellow", "pink", "lightgreen", "lightblue"] else (255, 255, 255, 128)
            draw.multiline_text((img_width/2 + 2, y + 2), reshaped_text, font=font, fill=shadow_color,
                                anchor="ma", align="center")
                                
        draw.multiline_text((img_width/2, y), reshaped_text, font=font, fill=text_color,
                            anchor="ma", align="center", stroke_width=2, stroke_fill=stroke_color)

    def wrap_text(self, draw, text, font, max_width):
        lines = text.split('\n')
        wrapped_lines = []
        for line in lines:
            words = line.split()
            if not words:
                wrapped_lines.append('')
                continue

            current_line = words[0]
            for word in words[1:]:
                if draw.textlength(current_line + " " + word, font=font) <= max_width:
                    current_line += " " + word
                else:
                    wrapped_lines.append(current_line)
                    current_line = word
            wrapped_lines.append(current_line)
        return "\n".join(wrapped_lines)

    def draw_text_at_position(self, draw, text, font_identifier, text_color, image_size, position, font_size, enable_shadow=False):
        margin = 20
        try:
            font = ImageFont.truetype(font_identifier, font_size)
        except IOError:
            font = ImageFont.truetype(self.font_paths.get("regular"), font_size)

        # Wrap text to fit image width
        wrapped_text = self.wrap_text(draw, text, font, image_size[0] - (2 * margin))
        reshaped_text = get_display(arabic_reshaper.reshape(wrapped_text))

        # Determine horizontal and vertical alignment from position
        if "left" in position:
            h_align = "left"
            anchor_h = "l"
        elif "right" in position:
            h_align = "right"
            anchor_h = "r"
        else:
            h_align = "center"
            anchor_h = "m"

        if "top" in position:
            anchor_v = "a"
            y = margin
        elif "bottom" in position:
            anchor_v = "d"
            y = image_size[1] - margin
        else: # Middle
            anchor_v = "m"
            y = image_size[1] / 2

        # Calculate X coordinate based on alignment
        if h_align == "left":
            x = margin
        elif h_align == "right":
            x = image_size[0] - margin
        else: # Center
            x = image_size[0] / 2

        anchor = anchor_h + anchor_v
        stroke_color = "black" if text_color != "black" else "white"
        
        if enable_shadow:
            shadow_color = (0, 0, 0, 128) if text_color in ["white", "yellow", "pink", "lightgreen", "lightblue"] else (255, 255, 255, 128)
            draw.multiline_text((x + 2, y + 2), reshaped_text, font=font, fill=shadow_color,
                                anchor=anchor, align=h_align)
                                
        draw.multiline_text((x, y), reshaped_text, font=font, fill=text_color,
                            anchor=anchor, align=h_align, stroke_width=2, stroke_fill=stroke_color)

    # old update_preview and pil_to_qimage have been replaced by Thread signal and on_image_processed.

    def save_image(self, image):
        save_path, selected_filter = QFileDialog.getSaveFileName(self, tr("generate_and_save_button"), "generated_image.png", tr("file_dialog_filter"))
        if save_path:
            try:
                quality = self.image_quality_combo.currentData()

                # For JPG, ensure image is RGB and save with quality
                if save_path.lower().endswith((".jpg", ".jpeg")):
                    if image.mode == 'RGBA':
                        # Create a white background and paste the image onto it
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        background.paste(image, (0, 0), image)
                        image = background
                    image.save(save_path, format="JPEG", quality=quality)
                else: # For PNG and others
                    image.save(save_path, quality=quality)

                QMessageBox.information(self, tr("dialog_title_success"), tr("msg_image_saved", save_path))
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_could_not_save_image", e))

def main():
    load_translations()
    app = QApplication(sys.argv)
    window = ImageTextEditorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
