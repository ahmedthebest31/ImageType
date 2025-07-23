import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog, QMessageBox, QCheckBox
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent
from PySide6.QtCore import Qt
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

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
        self.font_path = "arial.ttf"

        self.setWindowTitle("Image Text Editor")
        self.resize(800, 600)

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
        grid_layout.addWidget(self.fit_to_width_checkbox, 1, 1)

        self.text_position_combo = QComboBox()
        self.text_position_combo.addItems([
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ])
        grid_layout.addWidget(self.text_position_combo, 2, 0)

        self.text_color_combo = QComboBox()
        self.text_color_combo.addItems(["black", "white", "red", "blue", "green", "yellow"])
        grid_layout.addWidget(self.text_color_combo, 2, 1)

        self.background_type_combo = QComboBox()
        self.background_type_combo.addItems(["Use Existing Image", "Transparent", "Solid Color"])
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
        grid_layout.addWidget(self.background_type_combo, 3, 0)

        self.background_color_label = QLabel("Background Color:")
        self.background_color_combo = QComboBox()
        self.background_color_combo.addItems(["white", "black", "gray", "lightblue", "lightgreen"])
        grid_layout.addWidget(self.background_color_label, 4, 0)
        grid_layout.addWidget(self.background_color_combo, 4, 1)
        self.background_color_label.hide()
        self.background_color_combo.hide()

        self.generate_image_button = QPushButton("Generate and Save Image")
        self.generate_image_button.clicked.connect(self.generate_and_save_image)
        grid_layout.addWidget(self.generate_image_button, 5, 0, 1, 2)

        self.image_preview = QLabel("Image preview will be shown here.")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.image_preview, 0, 2, 6, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

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

    def generate_and_save_image(self):
        text_to_draw = self.text_input.toPlainText()
        if not text_to_draw:
            QMessageBox.warning(self, "Warning", "Please enter some text.")
            return

        background_type = self.background_type_combo.currentText()
        base_image = None

        if background_type == "Use Existing Image":
            if self.loaded_image:
                base_image = self.loaded_image.copy().convert("RGBA")
            else:
                QMessageBox.warning(self, "Warning", "Please load an image first.")
                return
        elif background_type == "Solid Color":
            bg_color = self.background_color_combo.currentText()
            base_image = Image.new("RGB", (800, 600), color=bg_color)
        else:  # Transparent
            base_image = Image.new("RGBA", (800, 600), (255, 255, 255, 0))

        generated_image = self.add_text_to_image(base_image, text_to_draw)
        if generated_image:
            self.update_preview(generated_image)
            self.save_image(generated_image)

    def add_text_to_image(self, image, text):
        draw = ImageDraw.Draw(image)
        text_color = self.text_color_combo.currentText()
        position = self.text_position_combo.currentText()
        margin = 20

        # Reshape and reorder Arabic text
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)

        font_size = int(image.height / 2.5)

        if self.fit_to_width_checkbox.isChecked():
            font_size = 1
            font = ImageFont.truetype(self.font_path, font_size)
            while font.getbbox(bidi_text)[2] < image.width - (margin * 2):
                font_size += 1
                font = ImageFont.truetype(self.font_path, font_size)
            font_size -= 1

        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except IOError:
            QMessageBox.warning(self, "Font Error", f"Font not found at {self.font_path}. Using default font.")
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x, y = self.calculate_text_position(image.size, (text_width, text_height), position, margin)
        
        stroke_color = "black" if text_color != "black" else "white"
        stroke_width = 2
        draw.text((x, y), bidi_text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color, align="center")

        return image

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

    def save_image(self, image):
        save_path, selected_filter = QFileDialog.getSaveFileName(self, "Save Image", "generated_image.png", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if save_path:
            try:
                file_format = "PNG"
                if "jpg" in selected_filter.lower():
                    file_format = "JPEG"
                
                if file_format == "JPEG":
                    image = image.convert("RGB")

                image.save(save_path, format=file_format)
                QMessageBox.information(self, "Success", f"Image saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageTextEditorApp()
    window.show()
    sys.exit(app.exec())