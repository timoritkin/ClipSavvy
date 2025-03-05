import threading

from PyQt6 import QtCore
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
        # self.masterLayout.addLayout(self.masterFrame, 1, 0)

        # frame
        # self.masterFrame = QFrame()
        # self.masterFrame.setLayout(self.masterLayout, 1, 0)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)

        # Buttons
        self.text_button = QPushButton(text="Text")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        # Scroll Area to handle multiple frames
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.masterLayout.addWidget(self.scroll_area, 1, 0)
        self.clips = clipboard.load_from_json_file() or []  # Ensure it's a list
        self.frames = {}  # Store frames with their associated data

        self.populate_clips()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_updates)  # Call a function here
        self.timer.start(1000)  # Runs every 1 second

    @staticmethod
    def add_clip_frame(self, clip):
        """Dynamically add a frame for a new clipboard entry"""
        frame = QFrame()
        frame.setMinimumSize(QSize(200, 200))
        frame.setMaximumSize(QSize(200, 200))
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setLineWidth(3)
        frame.setStyleSheet("background-color: rgb(255,85,255);")

        # Add content label
        label = QLabel(str(clip['content']), frame)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Remove button
        # remove_button = QPushButton("Remove", frame)
        # remove_button.clicked.connect(lambda: self.remove_clip(clip, frame))

        # Layout for frame
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(label)
        # frame_layout.addWidget(remove_button)
        frame.setLayout(frame_layout)

        # Add frame to layout and store reference
        self.scroll_layout.addWidget(frame)
        self.frames[clip['id']] = frame  # Store frame with its ID



    def check_for_updates(self):
        """Check if clipboard file has new entries"""
        new_clips = clipboard.load_from_json_file()
        if len(new_clips) > len(self.clips):
            for clip in new_clips:
                if clip['id'] not in self.frames:
                    self.add_clip_frame(clip)
            self.clips = new_clips  # Update internal list

    def populate_clips(self):
        """Create frames for existing clipboard content"""
        for clip in self.clips:
            self.add_clip_frame(clip)

#
# def add_new_clip_frame(self, clips):
#     for clip in clips:
#         # Create a new frame
#         frame = QFrame()
#         frame.setMinimumSize(QSize(200, 200))
#         frame.setMaximumSize(QSize(200, 200))
#         frame.setFrameShape(QFrame.Shape.Box)
#         frame.setLineWidth(3)
#         frame.setStyleSheet("background-color: rgb(255,85,255);")
#
#         print(clip.content)
#         # Add content to the frame
#         label = QLabel(str(clip.content))
#         label.setWordWrap(True)  # Enable word wrapping for text
#         label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#

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
