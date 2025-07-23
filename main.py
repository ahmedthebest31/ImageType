
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QPlainTextEdit, QComboBox, QFileDialog
)
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtCore import Qt

class AccessiblePlainTextEdit(QPlainTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            self.parentWidget().focusNextChild()
            event.accept()
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Text Editor - For Visually Impaired Users")
        self.resize(800, 600)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        # Text input area
        self.text_input = AccessiblePlainTextEdit()
        self.text_input.setAccessibleName("Text to add on image")
        grid_layout.addWidget(self.text_input, 0, 0, 1, 2)

        # Load Image Button
        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.setAccessibleName("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        grid_layout.addWidget(self.load_image_button, 1, 0)

        # Text Position Dropdown
        self.text_position_combo = QComboBox()
        self.text_position_combo.setAccessibleName("Text Position")
        self.text_position_combo.addItems([
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ])
        grid_layout.addWidget(self.text_position_combo, 2, 0)

        # Text Color Dropdown
        self.text_color_combo = QComboBox()
        self.text_color_combo.setAccessibleName("Text Color")
        self.text_color_combo.addItems(["White", "Black", "Red", "Blue", "Green", "Yellow"])
        grid_layout.addWidget(self.text_color_combo, 2, 1)

        # Background Type Dropdown
        self.background_type_combo = QComboBox()
        self.background_type_combo.setAccessibleName("Background Type")
        self.background_type_combo.addItems(["Transparent", "Solid Color", "Use Existing Image"])
        self.background_type_combo.currentTextChanged.connect(self.update_background_options)
        grid_layout.addWidget(self.background_type_combo, 3, 0)

        # Background Color Dropdown
        self.background_color_combo = QComboBox()
        self.background_color_combo.setAccessibleName("Background Color")
        self.background_color_combo.addItems(["White", "Black", "Gray", "Light Blue", "Light Green"])
        self.background_color_label = QLabel("Background Color:")
        grid_layout.addWidget(self.background_color_label, 4, 0)
        grid_layout.addWidget(self.background_color_combo, 4, 1)
        self.background_color_label.hide()
        self.background_color_combo.hide()


        # Generate Image Button
        self.generate_image_button = QPushButton("Generate and Save Image")
        self.generate_image_button.setAccessibleName("Generate and Save Image")
        self.generate_image_button.clicked.connect(self.generate_image)
        grid_layout.addWidget(self.generate_image_button, 5, 0, 1, 2)

        # Image Preview Area
        self.image_preview = QLabel("Image preview will be shown here.")
        self.image_preview.setAccessibleName("Image Preview")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.image_preview, 0, 2, 6, 1)

        # Set stretch factors for layout
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 2)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def update_background_options(self, text):
        if text == "Solid Color":
            self.background_color_label.show()
            self.background_color_combo.show()
        else:
            self.background_color_label.hide()
            self.background_color_combo.hide()

    def generate_image(self):
        # This is where the image generation logic will go.
        # For now, it's a placeholder.
        print("Generating image...")
        # In a real application, you would use Pillow to create the image,
        # draw the text, and then save it.
        # After saving, you might want to update the preview.
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
