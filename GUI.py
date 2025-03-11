from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QTimer, QRect
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


# this class will set the clipboard data into frame
class ClipInFrame(QWidget):
    def __init__(self, clip):
        super().__init__()  # Initialize QWidget
        """Dynamically add a frame for a new clipboard entry"""
        self.frame = QFrame(self)
        # self.frame.setMinimumSize(QSize(200, 200))
        # self.frame.setMaximumSize(QSize(200, 200))
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(3)
        self.frame.setStyleSheet("background-color: rgb(255,85,255);")
        self.clip = clip
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

        # # Add frame to layout and store reference
        # self.scroll_layout.addWidget(self.frame)
        # self.frames[clip.id] = self.frame  # Store frame with its ID
        #


# this class hold all frames and clipboards
class ClipboardContainer(QWidget):
    def __init__(self):
        super().__init__()

        self.selected_clip = None
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

        self.clips = {}
        self.records_json = clipboard.load_from_json_file()
        self.frames = {}  # Store frames with their associated data
        # mouse event when press on frame
        self.pressPos = None
        self.clicked = QtCore.pyqtSignal()

        self.populate_clips()
        print(self.frames)
        # Timer to check for new clipboard content
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_updates)  # type: ignore
        self.timer.start(2000)  # Check every 2 seconds

    def populate_clips(self):
        """Create frames for existing clipboard content"""
        for clip in self.records_json:
            clip_frame = ClipInFrame(clip)
            # Add frame to layout and store reference
            self.scroll_layout.addWidget(clip_frame.frame)
            self.frames[clip.id] = clip_frame.frame
            self.clips[clip.id] = clip_frame  # Store the whole ClipInFrame, not just the frame

    # def remove_clip(self, clip, frame):
    #     """Remove clipboard entry from UI and storage"""
    #     if clip['id'] in self.frames:
    #         self.scroll_layout.removeWidget(frame)
    #         frame.deleteLater()
    #         del self.frames[clip['id']]
    #
    #         # Remove from JSON storage
    #         self.records_json = [c for c in self.records_json if c['id'] != clip['id']]
    #         clipboard.save_to_json_file(self.records_json)

    def check_for_updates(self):
        """Check if clipboard file has new entries"""
        new_clips = clipboard.load_from_json_file()

        # If the number of records_json has increased, process new records_json
        if len(new_clips) > len(self.records_json):
            for clip in new_clips:
                if clip.id not in self.frames:  # Only add new records_json that don't have a frame yet
                    clip_frame = ClipInFrame(clip, len(self.records_json))  # or use i if you want to keep index
                    self.frames[clip.id] = clip_frame  # Store reference in frames dictionary
                    self.scroll_layout.addWidget(clip_frame.frame)  # Add the frame to layout

            self.records_json = new_clips  # Update internal list of records_json
            self.scroll_area.setWidgetResizable(True)  # Ensure the scroll area resizes when new widgets are added
            self.scroll_content.setMinimumHeight(self.scroll_layout.sizeHint().height())  # Update scroll content size
            self.populate_clips()

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
        try:

            if self.pressPos is None:
                return

            for clip_id, frame in self.frames.items():  # Loop through frames by clip_id

                clip_frame = self.frames[clip_id]
                print(clip_id)
                frame_position = clip_frame.pos()
                print(f"Frame Position: {frame_position.x()}, {frame_position.y()}")

                frame_position = frame.pos()
                print(f"Frame Position: {frame_position.x()}, {frame_position.y()}")

                print(f"Frame size: {frame.width()} x {frame.height()}")

                frame_rect = QRect(frame_position.x(), frame_position.y(), frame.width(), frame.height())
                if frame_rect.contains(self.pressPos):  # Check if the click is inside the frame
                    print(f"Clicked on frame: {clip_id}")

                    # Set the selected clip
                    self.selected_clip = self.clips[clip_id].clip.content  # Store the selected clip
                    print(f"Selected clip content: {self.selected_clip}")
                    clipboard.attach_new_clipboard(self.selected_clip)
        except Exception as e:
            print(f"Error: {e}")


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
        clipboardContainer = ClipboardContainer()
        self.masterLayout.addWidget(clipboardContainer)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)


def start_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # Start the Qt GUI in the main thread
    start_gui()
