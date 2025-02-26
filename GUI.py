from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
import sys
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClipSavvy")

        # central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # background color of the central widget
        # central_widget.setStyleSheet("background-color: ;")

        # Create layout
        upper_layout = QHBoxLayout(central_widget)

        # Create buttons
        text_button = QPushButton(text="Text")
        text_button.setFixedSize(100, 30)

        image_button = QPushButton("Images")
        image_button.setFixedSize(100, 30)


        #  central widget and layout
        upper_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        upper_layout.setSpacing(50)  # Set space between widgets to 50 pixels
        upper_layout.addWidget(text_button)
        upper_layout.addWidget(image_button)

        # Set the central widget
        self.setCentralWidget(central_widget)

        self.setMinimumSize(400, 700)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
