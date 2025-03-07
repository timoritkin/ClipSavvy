from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QObject, QRect
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QGridLayout, QVBoxLayout, QLabel, QFrame, QScrollArea)
import sys
import clipboard




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

        self.scroll_content.setMouseTracking(True)
        self.scroll_content.installEventFilter(self)

        self.clips = clipboard.load_from_json_file()
        self.frames = {}  # Store frames with their associated data

        # mouse event when press on frame
        self.pressPos = None
        self.clicked = QtCore.pyqtSignal()

        self.populate_clips()
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
        self.frame = QFrame()
        self.frame.setMinimumSize(QSize(200, 200))
        self.frame.setObjectName(str(id))
        self.frame.setMaximumSize(QSize(200, 200))
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(3)
        self.frame.setStyleSheet("background-color: rgb(255,85,255);")

        # Add content label
        label = QLabel(str(clip.content), self.frame)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Remove button
        # remove_button = QPushButton("Remove", frame)
        # remove_button.clicked.connect(lambda: self.remove_clip(clip, frame))  # type: ignore

        # Layout for frame
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(label)
        # frame_layout.addWidget(remove_button)
        self.frame.setLayout(frame_layout)

        # Add frame to layout and store reference
        self.scroll_layout.addWidget(self.frame)
        self.frames[clip.id] = self.frame  # Store frame with its ID

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
        # First, get the position relative to the scroll_content widget
        global_pos = self.mapToGlobal(event.pos())
        content_pos = self.scroll_content.mapFromGlobal(global_pos)

        # Add scroll offset to the y-coordinate
        scroll_offset = self.scroll_area.verticalScrollBar().value()
        content_pos.setY(content_pos.y() + scroll_offset)

        if event.button() == Qt.MouseButton.LeftButton:
            self.pressPos = content_pos
            print(f"Click position in content coordinates: {self.pressPos}")
            self.find_frame()

    def eventFilter(self, source, event):
        if source == self.scroll_content and event.type() == QtCore.QEvent.Type.MouseButtonPress:
            self.handleMousePressInContent(event)
            return True
        return super().eventFilter(source, event)

    def handleMousePressInContent(self, event):
        # This already gives us the position relative to the visible part of the scroll content
        content_pos = event.pos()

        # Add scroll offset to get the absolute position within the entire scroll content
        scroll_offset = self.scroll_area.verticalScrollBar().value()

        # Create a new point that includes the scroll offset
        absolute_pos = QtCore.QPoint(content_pos.x(), content_pos.y())

        print(f"Visible position: {content_pos}")
        print(f"Scroll offset: {scroll_offset}")
        print(f"Absolute position: {absolute_pos}")

        if event.button() == Qt.MouseButton.LeftButton:
            self.pressPos = absolute_pos
            print(f"Click position in content: {self.pressPos}")
            self.find_frame()

    def find_frame(self):
        if self.pressPos is None:
            return

        for clip_id in self.frames:
            frame = self.frames[clip_id]
            frame_position = frame.pos()
            print(f"Frame Position: {frame_position.x()}, {frame_position.y()}")

            frame_rect = QRect(frame_position.x(), frame_position.y(),
                               frame.width(), frame.height())
            if frame_rect.contains(self.pressPos):
                print(f"Clicked on frame: {clip_id}")
                # Access the content using the clip_id as a key
                if clip_id in self.clips:
                    print(self.clips[clip_id].content)


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
