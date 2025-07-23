import sys
import requests
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog, QMessageBox, QCheckBox,
    QDialog, QVBoxLayout, QHBoxLayout, QMenuBar, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent, QGuiApplication, QDesktopServices
from PySide6.QtCore import Qt, QUrl
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

APP_VERSION = "1.0"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/ImageType/main/version.json"
GITHUB_RELEASES_URL = "https://github.com/ahmedthebest31/ImageType/releases"

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About ImageType")
        self.setFixedSize(400, 300)
        self.setAccessibleName("About ImageType Dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Name
        name_label = QLabel("<b>Name:</b> ImageType")
        name_label.setAccessibleName("Application Name: ImageType")
        layout.addWidget(name_label)

        # Version
        version_label = QLabel(f"<b>Version:</b> {APP_VERSION}")
        version_label.setAccessibleName(f"Application Version: {APP_VERSION}")
        layout.addWidget(version_label)

        # Description
        description_text = "ImageType is a desktop application designed to empower visually impaired users to easily add custom text to images or create new images with text overlays. Built with Python and PySide6, it focuses heavily on accessibility and provides a straightforward interface compatible with screen readers. Whether you want to prepare text for social media posts, YouTube Shorts, or any other visual content, ImageType makes it simple to style and position your words."
        description_label = QLabel(f"<b>Description:</b> {description_text}")
        description_label.setWordWrap(True)
        description_label.setAccessibleName("Application Description: " + description_text)
        layout.addWidget(description_label)

        # Developer
        developer_label = QLabel("<b>Developer:</b> Ahmed Samy (AhmedTheBest)")
        developer_label.setAccessibleName("Developer: Ahmed Samy, also known as AhmedTheBest")
        layout.addWidget(developer_label)

        # Email
        email_label = QLabel("<b>Email:</b> ahmedthebest31@gmail.com")
        email_label.setAccessibleName("Developer Email: ahmedthebest31@gmail.com")
        layout.addWidget(email_label)

        # GitHub
        github_label = QLabel("<b>GitHub:</b> <a href=\"https://github.com/ahmedthebest31/ImageType\">https://github.com/ahmedthebest31/ImageType</a>")
        github_label.setOpenExternalLinks(True)
        github_label.setAccessibleName("Developer GitHub Profile: https://github.com/ahmedthebest31/ImageType")
        layout.addWidget(github_label)

        # LinkedIn
        linkedin_label = QLabel("<b>LinkedIn:</b> <a href=\"https://www.linkedin.com/in/ahmedthebest\">https://www.linkedin.com/in/ahmedthebest</a>")
        linkedin_label.setOpenExternalLinks(True)
        linkedin_label.setAccessibleName("Developer LinkedIn Profile: https://www.linkedin.com/in/ahmedthebest")
        layout.addWidget(linkedin_label)

        # Close Button
        close_button = QPushButton("Close")
        close_button.setAccessibleName("Close About Dialog Button")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch() # Push content to top

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

        self.setWindowTitle("Image Text Editor")
        self.resize(1000, 700)

        self.setup_menubar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        self.text_input = AccessiblePlainTextEdit()
        self.text_input.setPlaceholderText("Enter text to add to the image...")
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        grid_layout.addWidget(self.load_image_button, 1, 0)

        self.fit_to_width_checkbox = QCheckBox("Fit Text to Image Width")
        self.fit_to_width_checkbox.stateChanged.connect(self.toggle_position_combo)
        grid_layout.addWidget(self.fit_to_width_checkbox, 1, 1)

        self.text_style_combo = QComboBox()
        self.text_style_combo.setAccessibleName("Text Style")
        self.text_style_combo.addItems(["Normal", "Bold", "Italic"])
        grid_layout.addWidget(self.text_style_combo, 2, 0)

        self.text_color_combo = QComboBox()
        self.text_color_combo.setAccessibleName("Text color")
        self.text_color_combo.addItems(["black", "white", "red", "blue", "green", "yellow"])
        grid_layout.addWidget(self.text_color_combo, 2, 1)

        self.text_position_combo = QComboBox()
        self.text_position_combo.setAccessibleName("Text Position")
        self.text_position_combo.addItems([
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ])
        grid_layout.addWidget(self.text_position_combo, 3, 0, 1, 2)

        self.image_dimensions_combo = QComboBox()
        self.image_dimensions_combo.setAccessibleName("Image Dimensions")
        self.image_dimensions_combo.addItems([
            "Standard (1200x675)",
            "Square (1080x1080)",
            "Portrait (1080x1920)"
        ])
        grid_layout.addWidget(self.image_dimensions_combo, 4, 0)

        self.background_type_combo = QComboBox()
        self.background_type_combo.setAccessibleName("background type ")
        self.background_type_combo.addItems(["Use Existing Image", "Transparent", "Solid Color"])
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
        grid_layout.addWidget(self.background_type_combo, 4, 1)

        self.background_color_label = QLabel("Background Color:")
        self.background_color_combo = QComboBox()
        self.background_color_combo.setAccessibleName("background color")
        self.background_color_combo.addItems(["white", "black", "gray", "lightblue", "lightgreen"])
        grid_layout.addWidget(self.background_color_label, 5, 0)
        grid_layout.addWidget(self.background_color_combo, 5, 1)
        self.background_color_label.hide()
        self.background_color_combo.hide()

        self.image_quality_combo = QComboBox()
        self.image_quality_combo.setAccessibleName("Image Quality")
        self.image_quality_combo.addItems(["High", "Medium", "Low"])
        grid_layout.addWidget(self.image_quality_combo, 6, 0)

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setAccessibleName("Copy Image to Clipboard")
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        grid_layout.addWidget(self.copy_button, 6, 1)

        self.generate_image_button = QPushButton("Generate and Save Image")
        self.generate_image_button.clicked.connect(self.generate_and_save_image)
        grid_layout.addWidget(self.generate_image_button, 7, 0, 1, 2)

        self.image_preview = QLabel("Image preview will be shown here.")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.image_preview, 0, 2, 8, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

        self.toggle_position_combo()

    def setup_menubar(self):
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")
        help_menu.setAccessibleName("Help Menu")

        about_action = help_menu.addAction("About ImageType")
        about_action.triggered.connect(self.show_about_dialog)

        check_for_updates_action = help_menu.addAction("Check for Updates")
        check_for_updates_action.triggered.connect(self.check_for_updates)

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def check_for_updates(self):
        try:
            response = requests.get(GITHUB_VERSION_URL)
            response.raise_for_status()  # Raise an exception for HTTP errors
            latest_version_data = response.json()
            latest_version = latest_version_data.get("version")
            whats_new = latest_version_data.get("what's new", "No new features listed.")

            if latest_version and self.compare_versions(latest_version, APP_VERSION) > 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Update Available")
                msg_box.setText("A new version of ImageType is available!")
                msg_box.setInformativeText(f"<b>Current Version:</b> {APP_VERSION}<br><b>Latest Version:</b> {latest_version}<br><br><b>What's New:</b><br>{whats_new}")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setAccessibleName("Update Available Message Box")

                download_button = msg_box.addButton("Open Download Page", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)
                
                msg_box.exec()

                if msg_box.clickedButton() == download_button:
                    QDesktopServices.openUrl(QUrl(GITHUB_RELEASES_URL))
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("No Update")
                msg_box.setText("You are using the latest version of ImageType.")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setAccessibleName("No Update Available Message Box")
                msg_box.exec()

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"Could not check for updates. Please check your internet connection.\nError: {e}")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Update Error", "Could not parse version information from the server.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while checking for updates: {e}")

    def compare_versions(self, version1, version2):
        # Simple version comparison for "X.Y" format
        v1_parts = [int(p) for p in version1.split('.')]
        v2_parts = [int(p) for p in version2.split('.')]

        for i in range(max(len(v1_parts), len(v2_parts))):
            part1 = v1_parts[i] if i < len(v1_parts) else 0
            part2 = v2_parts[i] if i < len(v2_parts) else 0
            if part1 > part2:
                return 1
            elif part1 < part2:
                return -1
        return 0 # Versions are equal

    def toggle_position_combo(self):
        is_checked = self.fit_to_width_checkbox.isChecked()
        self.text_position_combo.setEnabled(not is_checked)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.loaded_image = Image.open(file_name)
                self.update_preview(self.loaded_image)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load image: {e}")

    def update_background_options(self, text):
        if text == "Solid Color":
            self.background_color_label.show()
            self.background_color_combo.show()
        else:
            self.background_color_label.hide()
            self.background_color_combo.hide()

    def get_image_dimensions(self):
        dim_text = self.image_dimensions_combo.currentText()
        if "1200x675" in dim_text:
            return (1200, 675)
        elif "1080x1080" in dim_text:
            return (1080, 1080)
        elif "1080x1920" in dim_text:
            return (1080, 1920)
        return (1200, 675)

    def create_image(self):
        text_to_draw = self.text_input.toPlainText()
        if not text_to_draw:
            QMessageBox.warning(self, "Warning", "Please enter some text.")
            return None

        background_type = self.background_type_combo.currentText()
        img_dims = self.get_image_dimensions()
        base_image = None

        if background_type == "Use Existing Image":
            if self.loaded_image:
                base_image = self.loaded_image.copy().resize(img_dims).convert("RGBA")
            else:
                QMessageBox.warning(self, "Warning", "Please load an image first.")
                return None
        elif background_type == "Solid Color":
            bg_color = self.background_color_combo.currentText()
            base_image = Image.new("RGB", img_dims, color=bg_color)
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
            QMessageBox.information(self, "Success", "Image copied to clipboard.")

    def add_text_to_image(self, image, text):
        text_color = self.text_color_combo.currentText()
        text_style = self.text_style_combo.currentText()
        
        font_path = self.font_path
        if text_style == "Bold":
            font_path = self.font_path_bold
        elif text_style == "Italic":
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
        margin = int(img_width * 0.05) # 5% margin
        target_width = img_width - (2 * margin)

        # 1. Process text for BiDi and line breaks
        processed_lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            processed_lines.append(bidi_line)

        # 2. Find optimal font size
        font_size = 200 # Start with a large font size
        font = ImageFont.truetype(font_path, font_size)

        while font_size > 10:
            wrapped_lines = []
            total_height = 0
            for line in processed_lines:
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if font.getbbox(current_line + ' ' + word)[2] <= target_width:
                        current_line += ' ' + word
                    else:
                        wrapped_lines.append(current_line.strip())
                        current_line = word
                wrapped_lines.append(current_line.strip())
            
            # Calculate total height of wrapped lines
            text_bbox = draw.textbbox((0,0), '\n'.join(wrapped_lines), font=font)
            total_height = text_bbox[3] - text_bbox[1]

            if total_height < img_height - (2 * margin):
                break # This font size fits
            font_size -= 5 # Decrease font size and try again
            font = ImageFont.truetype(font_path, font_size)

        # 3. Draw the final text
        final_text = '\n'.join(wrapped_lines)
        text_bbox = draw.textbbox((0,0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (img_width - text_width) / 2
        y = (img_height - text_height) / 2
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def draw_text_at_position(self, image, text, text_color, font_path, position):
        draw = ImageDraw.Draw(image)
        margin = 20
        font_size = int(image.height / 8) # Larger default font size
        font = ImageFont.truetype(font_path, font_size)

        # Process each line separately to preserve line breaks
        lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            lines.append(bidi_line)
        
        final_text = '\n'.join(lines)
        text_bbox = draw.textbbox((0,0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x, y = self.calculate_text_position(image.size, (text_width, text_height), position, margin)
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def calculate_text_position(self, image_size, text_size, position, margin):
        img_width, img_height = image_size
        text_width, text_height = text_size

        if "Left" in position:
            x = margin
        elif "Right" in position:
            x = img_width - text_width - margin
        else: 
            x = (img_width - text_width) / 2

        if "Top" in position:
            y = margin
        elif "Bottom" in position:
            y = img_height - text_height - margin
        else: 
            y = (img_height - text_height) / 2
            
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
        if quality_text == "High":
            return 95
        elif quality_text == "Medium":
            return 80
        elif quality_text == "Low":
            return 65
        return 95

    def save_image(self, image):
        save_path, selected_filter = QFileDialog.getSaveFileName(self, "Save Image", "generated_image.png", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if save_path:
            try:
                file_format = "PNG"
                quality = self.get_save_quality()
                if "jpg" in selected_filter.lower():
                    file_format = "JPEG"
                
                if file_format == "JPEG":
                    image = image.convert("RGB")

                image.save(save_path, format=file_format, quality=quality)
                QMessageBox.information(self, "Success", f"Image saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageTextEditorApp()
    window.show()
    sys.exit(app.exec())

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

        self.setWindowTitle("Image Text Editor")
        self.resize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        self.text_input = AccessiblePlainTextEdit()
        self.text_input.setPlaceholderText("Enter text to add to the image...")
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        grid_layout.addWidget(self.load_image_button, 1, 0)

        self.fit_to_width_checkbox = QCheckBox("Fit Text to Image Width")
        self.fit_to_width_checkbox.stateChanged.connect(self.toggle_position_combo)
        grid_layout.addWidget(self.fit_to_width_checkbox, 1, 1)

        self.text_style_combo = QComboBox()
        self.text_style_combo.setAccessibleName("Text Style")
        self.text_style_combo.addItems(["Normal", "Bold", "Italic"])
        grid_layout.addWidget(self.text_style_combo, 2, 0)

        self.text_color_combo = QComboBox()
        self.text_color_combo.setAccessibleName("Text color")
        self.text_color_combo.addItems(["black", "white", "red", "blue", "green", "yellow"])
        grid_layout.addWidget(self.text_color_combo, 2, 1)

        self.text_position_combo = QComboBox()
        self.text_position_combo.setAccessibleName("Text Position")
        self.text_position_combo.addItems([
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ])
        grid_layout.addWidget(self.text_position_combo, 3, 0, 1, 2)

        self.image_dimensions_combo = QComboBox()
        self.image_dimensions_combo.setAccessibleName("Image Dimensions")
        self.image_dimensions_combo.addItems([
            "Standard (1200x675)",
            "Square (1080x1080)",
            "Portrait (1080x1920)"
        ])
        grid_layout.addWidget(self.image_dimensions_combo, 4, 0)

        self.background_type_combo = QComboBox()
        self.background_type_combo.setAccessibleName("background type ")
        self.background_type_combo.addItems(["Use Existing Image", "Transparent", "Solid Color"])
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
        grid_layout.addWidget(self.background_type_combo, 4, 1)

        self.background_color_label = QLabel("Background Color:")
        self.background_color_combo = QComboBox()
        self.background_color_combo.setAccessibleName("background color")
        self.background_color_combo.addItems(["white", "black", "gray", "lightblue", "lightgreen"])
        grid_layout.addWidget(self.background_color_label, 5, 0)
        grid_layout.addWidget(self.background_color_combo, 5, 1)
        self.background_color_label.hide()
        self.background_color_combo.hide()

        self.image_quality_combo = QComboBox()
        self.image_quality_combo.setAccessibleName("Image Quality")
        self.image_quality_combo.addItems(["High", "Medium", "Low"])
        grid_layout.addWidget(self.image_quality_combo, 6, 0)

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setAccessibleName("Copy Image to Clipboard")
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        grid_layout.addWidget(self.copy_button, 6, 1)

        self.generate_image_button = QPushButton("Generate and Save Image")
        self.generate_image_button.clicked.connect(self.generate_and_save_image)
        grid_layout.addWidget(self.generate_image_button, 7, 0, 1, 2)

        self.image_preview = QLabel("Image preview will be shown here.")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.image_preview, 0, 2, 8, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

        self.toggle_position_combo()

    def toggle_position_combo(self):
        is_checked = self.fit_to_width_checkbox.isChecked()
        self.text_position_combo.setEnabled(not is_checked)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.loaded_image = Image.open(file_name)
                self.update_preview(self.loaded_image)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load image: {e}")

    def update_background_options(self, text):
        if text == "Solid Color":
            self.background_color_label.show()
            self.background_color_combo.show()
        else:
            self.background_color_label.hide()
            self.background_color_combo.hide()

    def get_image_dimensions(self):
        dim_text = self.image_dimensions_combo.currentText()
        if "1200x675" in dim_text:
            return (1200, 675)
        elif "1080x1080" in dim_text:
            return (1080, 1080)
        elif "1080x1920" in dim_text:
            return (1080, 1920)
        return (1200, 675)

    def create_image(self):
        text_to_draw = self.text_input.toPlainText()
        if not text_to_draw:
            QMessageBox.warning(self, "Warning", "Please enter some text.")
            return None

        background_type = self.background_type_combo.currentText()
        img_dims = self.get_image_dimensions()
        base_image = None

        if background_type == "Use Existing Image":
            if self.loaded_image:
                base_image = self.loaded_image.copy().resize(img_dims).convert("RGBA")
            else:
                QMessageBox.warning(self, "Warning", "Please load an image first.")
                return None
        elif background_type == "Solid Color":
            bg_color = self.background_color_combo.currentText()
            base_image = Image.new("RGB", img_dims, color=bg_color)
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
            QMessageBox.information(self, "Success", "Image copied to clipboard.")

    def add_text_to_image(self, image, text):
        text_color = self.text_color_combo.currentText()
        text_style = self.text_style_combo.currentText()
        
        font_path = self.font_path
        if text_style == "Bold":
            font_path = self.font_path_bold
        elif text_style == "Italic":
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
        margin = int(img_width * 0.05) # 5% margin
        target_width = img_width - (2 * margin)

        # 1. Process text for BiDi and line breaks
        processed_lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            processed_lines.append(bidi_line)

        # 2. Find optimal font size
        font_size = 200 # Start with a large font size
        font = ImageFont.truetype(font_path, font_size)

        while font_size > 10:
            wrapped_lines = []
            total_height = 0
            for line in processed_lines:
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if font.getbbox(current_line + ' ' + word)[2] <= target_width:
                        current_line += ' ' + word
                    else:
                        wrapped_lines.append(current_line.strip())
                        current_line = word
                wrapped_lines.append(current_line.strip())
            
            # Calculate total height of wrapped lines
            text_bbox = draw.textbbox((0,0), '\n'.join(wrapped_lines), font=font)
            total_height = text_bbox[3] - text_bbox[1]

            if total_height < img_height - (2 * margin):
                break # This font size fits
            font_size -= 5 # Decrease font size and try again
            font = ImageFont.truetype(font_path, font_size)

        # 3. Draw the final text
        final_text = '\n'.join(wrapped_lines)
        text_bbox = draw.textbbox((0,0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (img_width - text_width) / 2
        y = (img_height - text_height) / 2
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def draw_text_at_position(self, image, text, text_color, font_path, position):
        draw = ImageDraw.Draw(image)
        margin = 20
        font_size = int(image.height / 8) # Larger default font size
        font = ImageFont.truetype(font_path, font_size)

        # Process each line separately to preserve line breaks
        lines = []
        for line in text.split('\n'):
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            lines.append(bidi_line)
        
        final_text = '\n'.join(lines)
        text_bbox = draw.textbbox((0,0), final_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x, y = self.calculate_text_position(image.size, (text_width, text_height), position, margin)
        
        stroke_color = "black" if text_color != "black" else "white"
        draw.text((x, y), final_text, font=font, fill=text_color, stroke_width=2, stroke_fill=stroke_color, align="center")

    def calculate_text_position(self, image_size, text_size, position, margin):
        img_width, img_height = image_size
        text_width, text_height = text_size

        if "Left" in position:
            x = margin
        elif "Right" in position:
            x = img_width - text_width - margin
        else: 
            x = (img_width - text_width) / 2

        if "Top" in position:
            y = margin
        elif "Bottom" in position:
            y = img_height - text_height - margin
        else: 
            y = (img_height - text_height) / 2
            
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
        if quality_text == "High":
            return 95
        elif quality_text == "Medium":
            return 80
        elif quality_text == "Low":
            return 65
        return 95

    def save_image(self, image):
        save_path, selected_filter = QFileDialog.getSaveFileName(self, "Save Image", "generated_image.png", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if save_path:
            try:
                file_format = "PNG"
                quality = self.get_save_quality()
                if "jpg" in selected_filter.lower():
                    file_format = "JPEG"
                
                if file_format == "JPEG":
                    image = image.convert("RGB")

                image.save(save_path, format=file_format, quality=quality)
                QMessageBox.information(self, "Success", f"Image saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageTextEditorApp()
    window.show()
    sys.exit(app.exec())