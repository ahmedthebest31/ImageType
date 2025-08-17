import sys
import requests
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog, QMessageBox, QCheckBox,
    QDialog, QVBoxLayout, QHBoxLayout, QMenuBar, QSizePolicy, QMenu
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent, QGuiApplication, QDesktopServices, QActionGroup
from PySide6.QtCore import Qt, QUrl
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

APP_VERSION = "1.0"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/ImageType/main/version.json"
GITHUB_RELEASES_URL = "https://github.com/ahmedthebest31/ImageType/releases"
CONFIG_FILE = "config.json"
LANGUAGES_DIR = "languages"
TRANSLATIONS = {}
CURRENT_LANG = "en_us"

def load_config():
    """Loads configuration from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"language": "en_us"}

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

        # Name
        name_label = QLabel(f"<b>{tr('about_dialog_name')}</b>")
        name_label.setAccessibleName(tr("about_dialog_name"))
        layout.addWidget(name_label)

        # Version
        version_label = QLabel(f"<b>{tr('about_dialog_version', APP_VERSION)}</b>")
        version_label.setAccessibleName(tr('about_dialog_version', APP_VERSION))
        layout.addWidget(version_label)

        # Description
        description_text = tr("about_dialog_description_text")
        description_label = QLabel(f"<b>{tr('about_dialog_description_text')}</b><br>{description_text}")
        description_label.setWordWrap(True)
        description_label.setAccessibleName(tr("about_dialog_description_text"))
        layout.addWidget(description_label)

        # Developer
        developer_label = QLabel(f"<b>{tr('about_dialog_developer')}</b>")
        developer_label.setAccessibleName(tr("about_dialog_developer"))
        layout.addWidget(developer_label)

        # Email
        email_label = QLabel(f"<b>{tr('about_dialog_email')}</b>")
        email_label.setAccessibleName(tr("about_dialog_email"))
        layout.addWidget(email_label)

        # GitHub
        github_label = QLabel(f"<b>{tr('about_dialog_github')}</b><br><a href=\"https://github.com/ahmedthebest31/ImageType\">https://github.com/ahmedthebest31/ImageType</a>")
        github_label.setOpenExternalLinks(True)
        github_label.setAccessibleName(tr("about_dialog_github"))
        layout.addWidget(github_label)

        # LinkedIn
        linkedin_label = QLabel(f"<b>{tr('about_dialog_linkedin')}</b><br><a href=\"https://www.linkedin.com/in/ahmedthebest\">https://www.linkedin.com/in/ahmedthebest</a>")
        linkedin_label.setOpenExternalLinks(True)
        linkedin_label.setAccessibleName(tr("about_dialog_linkedin"))
        layout.addWidget(linkedin_label)

        # Close Button
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
        if event.key() == Qt.Key.Key_Tab:
            self.parentWidget().focusNextChild()
            event.accept()
        else:
            super().keyPressEvent(event)

class ImageTextEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_image = None
        self.generated_image = None
        self.font_path = "arial.ttf"
        self.font_path_bold = "arialbd.ttf"
        self.font_path_italic = "ariali.ttf"
        
        global CURRENT_LANG
        config = load_config()
        CURRENT_LANG = config.get("language", "en_us")

        self.setWindowTitle(tr("app_title"))
        self.resize(1000, 700)
        self.setup_ui()
        self.retranslate_ui()

    def setup_ui(self):
        self.setup_menubar()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        self.text_input = AccessiblePlainTextEdit()
        self.text_input.setPlaceholderText(tr("text_input_placeholder"))
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        self.load_image_button = QPushButton(tr("load_image_button"))
        self.load_image_button.clicked.connect(self.load_image)
        self.load_image_button.setAccessibleName(tr("load_image_button") + " Button")
        grid_layout.addWidget(self.load_image_button, 1, 0)

        self.fit_to_width_checkbox = QCheckBox(tr("fit_to_width_checkbox"))
        self.fit_to_width_checkbox.stateChanged.connect(self.toggle_position_combo)
        self.fit_to_width_checkbox.setAccessibleName(tr("fit_to_width_checkbox") + " Checkbox")
        grid_layout.addWidget(self.fit_to_width_checkbox, 1, 1)

        self.text_style_combo = QComboBox()
        self.text_style_combo.setAccessibleName(tr("text_style_combo_label"))
        self.text_style_combo.addItems([tr("text_style_normal"), tr("text_style_bold"), tr("text_style_italic")])
        grid_layout.addWidget(self.text_style_combo, 2, 0)

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
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
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

    def setup_menubar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu(tr("&menu_file"))
        file_menu.setAccessibleName(tr("menu_file") + " Menu")
        
        exit_action = file_menu.addAction(tr("menu_file_exit"))
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu(tr("&menu_help"))
        help_menu.setAccessibleName(tr("menu_help") + " Menu")

        about_action = help_menu.addAction(tr("about_action"))
        about_action.triggered.connect(self.show_about_dialog)

        check_for_updates_action = help_menu.addAction(tr("check_for_updates_action"))
        check_for_updates_action.triggered.connect(self.check_for_updates)

        settings_menu = menubar.addMenu(tr("&menu_settings"))
        settings_menu.setAccessibleName(tr("menu_settings") + " Menu")

        self.language_menu = QMenu(tr("menu_settings_language"), self)
        settings_menu.addMenu(self.language_menu)

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

    def retranslate_colors(self):
        colors = ["black", "white", "red", "blue", "green", "yellow"]
        self.text_color_combo.clear()
        for color in colors:
            self.text_color_combo.addItem(tr(f"color_{color}"), color)

    def retranslate_background_colors(self):
        colors = ["white", "black", "gray", "lightblue", "lightgreen"]
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
            whats_new = latest_version_data.get("what's new", "No new features listed.")

            if latest_version and self.compare_versions(latest_version, APP_VERSION) > 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(tr("dialog_title_update_available"))
                msg_box.setText(tr("msg_update_available"))
                msg_box.setInformativeText(tr("msg_update_info", APP_VERSION, latest_version, whats_new))
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setAccessibleName(tr("dialog_title_update_available") + " Message Box")

                download_button = msg_box.addButton(tr("button_open_download_page"), QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)
                
                msg_box.exec()

                if msg_box.clickedButton() == download_button:
                    QDesktopServices.openUrl(QUrl(GITHUB_RELEASES_URL))
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(tr("dialog_title_no_update"))
                msg_box.setText(tr("msg_no_update"))
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setAccessibleName(tr("dialog_title_no_update") + " Message Box")
                msg_box.exec()

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

    def retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))
        self.text_input.setPlaceholderText(tr("text_input_placeholder"))
        self.load_image_button.setText(tr("load_image_button"))
        self.fit_to_width_checkbox.setText(tr("fit_to_width_checkbox"))
        
        self.text_style_combo.setAccessibleName(tr("text_style_combo_label"))
        self.text_style_combo.setItemText(0, tr("text_style_normal"))
        self.text_style_combo.setItemText(1, tr("text_style_bold"))
        self.text_style_combo.setItemText(2, tr("text_style_italic"))

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

        # Update menubar
        self.menuBar().clear()
        self.setup_menubar()

        # Relaunch the About Dialog if it's open to refresh its text
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AboutDialog):
                widget.close()
                self.show_about_dialog()

    def toggle_position_combo(self):
        is_checked = self.fit_to_width_checkbox.isChecked()
        self.text_position_combo.setEnabled(not is_checked)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, tr("load_image_button"), "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.loaded_image = Image.open(file_name)
                self.update_preview(self.loaded_image)
            except Exception as e:
                QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_could_not_load_image", e))

    def update_background_options(self, text):
        if text == tr("background_type_solid_color"):
            self.background_color_label.show()
            self.background_color_combo.show()
        else:
            self.background_color_label.hide()
            self.background_color_combo.hide()

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
        text_color = self.text_color_combo.currentData()
        text_style = self.text_style_combo.currentText()
        
        font_path = self.font_path
        if text_style == tr("text_style_bold"):
            font_path = self.font_path_bold
        elif text_style == tr("text_style_italic"):
            font_path = self.font_path_italic

        if self.fit_to_width_checkbox.isChecked():
            self.draw_text_full_width(image, text, text_color, font_path)
        else:
            position = self.text_position_combo.currentText()
            self.draw_text_at_position(image, text, text_color, font_path, position)

        return image

    def draw_text_full_width(self, image, text, text_color, font_path):
        draw = ImageDraw.Draw(image)
        img_width, img_height = image.size
        margin = int(img_width * 0.05)
        target_width = img_width - (2 * margin)

        processed_lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            processed_lines.append(bidi_line)

        font_size = 200
        font = ImageFont.truetype(font_path, font_size)

        while font_size > 10:
            wrapped_lines = []
            for line in processed_lines:
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if draw.textlength(current_line + ' ' + word, font=font) <= target_width:
                        current_line += ' ' + word
                    else:
                        wrapped_lines.append(current_line.strip())
                        current_line = word
                if current_line:
                    wrapped_lines.append(current_line.strip())
            
            text_bbox = draw.textbbox((0, 0), '\n'.join(wrapped_lines), font=font)
            total_height = text_bbox[3] - text_bbox[1]

            if total_height < img_height - (2 * margin):
                break
            font_size -= 5
            font = ImageFont.truetype(font_path, font_size)

        final_text = '\n'.join(wrapped_lines)
        text_bbox = draw.textbbox((0, 0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (img_width - text_width) / 2
        y = (img_height - text_height) / 2
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def draw_text_at_position(self, image, text, text_color, font_path, position):
        draw = ImageDraw.Draw(image)
        margin = 20
        font_size = int(image.height / 8)
        font = ImageFont.truetype(font_path, font_size)

        lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            lines.append(bidi_line)
        
        final_text = '\n'.join(lines)
        text_bbox = draw.textbbox((0, 0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x, y = self.calculate_text_position(image.size, (text_width, text_height), position, margin)
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def calculate_text_position(self, image_size, text_size, position, margin):
        img_width, img_height = image_size
        text_width, text_height = text_size

        if position == tr("text_position_top_left"):
            x, y = margin, margin
        elif position == tr("text_position_top_center"):
            x, y = (img_width - text_width) / 2, margin
        elif position == tr("text_position_top_right"):
            x, y = img_width - text_width - margin, margin
        elif position == tr("text_position_middle_left"):
            x, y = margin, (img_height - text_height) / 2
        elif position == tr("text_position_center"):
            x, y = (img_width - text_width) / 2, (img_height - text_height) / 2
        elif position == tr("text_position_middle_right"):
            x, y = img_width - text_width - margin, (img_height - text_height) / 2
        elif position == tr("text_position_bottom_left"):
            x, y = margin, img_height - text_height - margin
        elif position == tr("text_position_bottom_center"):
            x, y = (img_width - text_width) / 2, img_height - text_height - margin
        elif position == tr("text_position_bottom_right"):
            x, y = img_width - text_width - margin, img_height - text_height - margin
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