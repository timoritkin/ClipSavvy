import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QFrame, QScrollArea,
                             QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout, QVBoxLayout
from PyQt6.QtCore import Qt
import sys
import clipboard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.setWindowTitle("ClipSavvy")
        self.setContentsMargins(20, 20, 20, 20)
        # self.setMinimumSize(400, 700)

        # Create a central widget
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        # frame
        self.masterFrame = QFrame()

        # Layouts
        self.menuLayout = QGridLayout()
        self.menuLayout.setSpacing(20)

        self.framesLayout = QVBoxLayout()

        self.masterLayout = QGridLayout()
        self.masterLayout.addLayout(self.menuLayout, 0, 0)
        self.masterLayout.addLayout(self.masterFrame, 1, 0)

        # frame
        self.masterFrame = QFrame()
        self.masterFrame.setLayout(self.masterLayout, 1, 0)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)

        # Buttons
        self.text_button = QPushButton(text="Text")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        # scroll
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.centralWidget)

        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        clips = clipboard.load_from_json_file()
        self.add_new_clip_frame(clips)

    def add_new_clip_frame(self, clips):
        for clip in clips:
            # Create a new frame
            frame = QFrame()
            frame.setMinimumSize(QSize(200, 200))
            frame.setMaximumSize(QSize(200, 200))
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLineWidth(3)
            frame.setStyleSheet("background-color: rgb(255,85,255);")

            # Create a layout for the frame
            frame_layout = QVBoxLayout(frame)
            print(clip.content)
            # Add content to the frame
            label = QLabel(str(clip.content))
            label.setWordWrap(True)  # Enable word wrapping for text
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(label)

            # Add the frame to the main layout
            self.framesLayout.addWidget(frame)

            # Force layout update
            self.framesLayout.update()

    def update_gui(self):
        # Update your GUI elements here (e.g., based on clipboard changes)
        pass


def start_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # Start the Qt GUI in the main thread
    start_gui()
