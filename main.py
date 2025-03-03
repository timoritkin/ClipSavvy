import threading

from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QFrame, QScrollArea,
                             QHBoxLayout, QVBoxLayout)
import sys
from PyQt6.QtCore import Qt, QSize, QTimer

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

        # Layouts
        self.menuLayout = QGridLayout()
        self.menuLayout.setSpacing(20)

        self.framesLayout = QVBoxLayout()

        self.masterLayout = QGridLayout()
        self.masterLayout.addLayout(self.menuLayout, 0, 0)
        self.masterLayout.addLayout(self.framesLayout, 1, 0)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)

        # Buttons
        self.text_button = QPushButton(text="Text")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

    def add_new_clip_frame(self, clipboard_data):
        # Create a new frame
        frame = QFrame()
        frame.setMinimumSize(QSize(200, 200))
        frame.setMaximumSize(QSize(200, 200))
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setLineWidth(3)
        frame.setStyleSheet("background-color: rgb(255,85,255);")

        # Create a layout for the frame
        frame_layout = QVBoxLayout(frame)

        # Add content to the frame
        if isinstance(clipboard_data, str):
            label = QLabel(clipboard_data)
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

    timer = QTimer()
    timer.timeout.connect(window.update_gui)  # Connect timer to update_gui method
    timer.start(1000)

    # Start clipboard monitoring in a background thread
    clipboard_thread = threading.Thread(target=clipboard.check_clipboard, args=(window,),
                                        daemon=True)  # Pass window to the thread
    clipboard_thread.start()

    # Start keyboard hotkey listener in a background thread
    keyboard_thread = threading.Thread(target=clipboard.start_hotkeys, daemon=True)
    keyboard_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    # Start the Qt GUI in the main thread
    start_gui()
