from PyQt6 import QtCore
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QFrame, QScrollArea,
                             QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QObject
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout, QVBoxLayout
from PyQt6.QtCore import Qt
import sys
import clipboard


class CustomFrame(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_frame


class Mouse(QtCore.QObject):
    def __init__(self):
        super().__init__()
        # mouse event when press on frame
        self.pressPos = None
        self.clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressPos = event.pos()
            print(self.pressPos)

    def mouseReleaseEvent(self, event):
        # ensure that the left button was pressed *and* released within the
        # geometry of the widget; if so, emit the signal;
        if (self.pressPos is not None and
                event.button() == Qt.MouseButton.LeftButton and
                event.pos() in self.rect()):
            self.clicked.emit()
        self.pressPos = None


class ClipboardContainer(QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        # Scroll Area to handle multiple frames
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)

        self.clips = clipboard.load_from_json_file()
        self.frames = {}  # Store frames with their associated data

        self.populate_clips()
        self.find_frame()
        # mouse event when press on frame
        self.pressPos = None
        self.clicked = QtCore.pyqtSignal()

        # Timer to check for new clipboard content
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_updates)  # type: ignore
        self.timer.start(2000)  # Check every 2 seconds

    def populate_clips(self):
        """Create frames for existing clipboard content"""
        for i, clip in enumerate(self.clips):
            self.add_clip_frame(clip, i)

    def add_clip_frame(self, clip, id):
        """Dynamically add a frame for a new clipboard entry"""
        frame = QFrame()
        frame.setMinimumSize(QSize(200, 200))
        frame.setObjectName(str(id))
        frame.setMaximumSize(QSize(200, 200))
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setLineWidth(3)
        frame.setStyleSheet("background-color: rgb(255,85,255);")

        # Add content label
        label = QLabel(str(clip.content), frame)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Remove button
        # remove_button = QPushButton("Remove", frame)
        # remove_button.clicked.connect(lambda: self.remove_clip(clip, frame))  # type: ignore

        # Layout for frame
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(label)
        # frame_layout.addWidget(remove_button)
        frame.setLayout(frame_layout)

        # Add frame to layout and store reference
        self.scroll_layout.addWidget(frame)
        self.frames[clip.id] = frame  # Store frame with its ID

    # def remove_clip(self, clip, frame):
    #     """Remove clipboard entry from UI and storage"""
    #     if clip['id'] in self.frames:
    #         self.scroll_layout.removeWidget(frame)
    #         frame.deleteLater()
    #         del self.frames[clip['id']]
    #
    #         # Remove from JSON storage
    #         self.clips = [c for c in self.clips if c['id'] != clip['id']]
    #         clipboard.save_to_json_file(self.clips)

    def check_for_updates(self):
        """Check if clipboard file has new entries"""
        new_clips = clipboard.load_from_json_file()
        if len(new_clips) > len(self.clips):
            for i, clip in enumerate(new_clips):
                if clip.id not in self.frames:
                    self.add_clip_frame(clip, i)
            self.clips = new_clips  # Update internal list

    def mousePressEvent(self, event):
        # Get the event's position relative to the scroll area
        event_pos = event.pos()
        # Adjust for the scroll offset of the scroll area
        scroll_offset = self.scroll_area.verticalScrollBar().value()
        # Map the position relative to the global coordinates, considering the scroll offset
        global_pos = self.scroll_content.mapToGlobal(event_pos)
        global_pos.setY(global_pos.y() + scroll_offset)

        if event.button() == Qt.MouseButton.LeftButton:
            self.pressPos = global_pos
            self.find_frame()
            print(self.pressPos)

    def find_frame(self):

        for clip_id in self.frames:
            frame = self.frames[clip_id]
            frame_position = frame.pos()  # Returns QPoint(x, y)
            print(f"Frame Position: {frame_position.x()}, {frame_position.y()}")


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

        self.masterLayout = QGridLayout()
        self.masterLayout.addLayout(self.menuLayout, 0, 0)
        # self.masterLayout.addLayout(self.masterFrame, 1, 0)

        # Buttons
        self.text_button = QPushButton(text="Text")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        cc = ClipboardContainer()
        self.masterLayout.addWidget(cc)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)


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
