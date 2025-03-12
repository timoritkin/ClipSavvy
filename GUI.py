from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QGridLayout, QVBoxLayout, QLabel, QFrame, QScrollArea
, QCheckBox, QHBoxLayout, QSizePolicy, QMessageBox)
import sys
import clipboard


def show_message(message):
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Information")
    msg_box.setText(f"{message}")
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.exec()  # Show the message box


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
        self.checkbox = QCheckBox(self)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)  # type: ignore
        self.checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.frameSelected = False

        # Remove button
        # remove_button = QPushButton("Remove", frame)
        # remove_button.clicked.connect(lambda: self.remove_clip(clip, frame))  # type: ignore

        # Layout for frame
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(label)
        frame_layout.addWidget(self.checkbox)
        # frame_layout.addWidget(remove_button)
        self.frame.setLayout(frame_layout)

    def on_checkbox_changed(self, state):
        if self.checkbox.isChecked():
            print("Checkbox is checked ")
            self.frameSelected = True
        else:
            print("Checkbox is unchecked ")
            self.frameSelected = False


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

    def check_for_updates(self):
        """Check if clipboard file has new entries"""
        new_clips = clipboard.load_from_json_file()

        # If the number of records_json has increased, process new records_json
        if len(new_clips) > len(self.records_json):
            for clip in new_clips:
                if clip.id not in self.frames:  # Only add new records_json that don't have a frame yet
                    clip_frame = ClipInFrame(clip)  # or use i if you want to keep index
                    self.frames[clip.id] = clip_frame  # Store reference in frames dictionary
                    self.clips[clip.id] = clip_frame  # Store the whole ClipInFrame, not just the frame
                    self.scroll_layout.addWidget(clip_frame.frame)  # Add the frame to layout

            self.records_json = new_clips  # Update internal list of records_json
            self.scroll_area.setWidgetResizable(True)  # Ensure the scroll area resizes when new widgets are added
            self.scroll_content.setMinimumHeight(self.scroll_layout.sizeHint().height())  # Update scroll content size
            # self.populate_clips()

    def toggle_delete_mode(self):
        to_delete = []  # Collect items to delete first

        for clip_id, frame in list(self.clips.items()):  # Loop through frames by clip_id
            if self.clips[clip_id].frameSelected:
                to_delete.append(clip_id)  # Store the ID for deletion
        # if the list is empty messagebox will appear
        if not to_delete:
            show_message("Please select items to delete from the clipboard")

        for clip_id in to_delete:
            frame = self.clips[clip_id].frame  # Store reference before deleting

            # Remove from layout and delete the widget
            self.scroll_layout.removeWidget(frame)
            frame.deleteLater()  # Properly delete the frame
            # Remove from dictionary
            del self.clips[clip_id]
            del self.frames[clip_id]

            # Remove from clipboard JSON
            clipboard.remove_entries_by_id("clipboard_history.json", clip_id)

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
        self.delete_button = QPushButton(text="Delete")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.delete_button, 0, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        clipboardContainer = ClipboardContainer()
        self.masterLayout.addWidget(clipboardContainer)

        # Initialize QTimer
        # self.timer = QTimer(self)  # Create a timer associated with the window
        # self.timer.timeout.connect(ClipboardContainer.check_for_updates(self))   # type: ignore
        # self.timer.start(1000)  # Start the timer and check every 1 second (1000 ms)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)
        self.delete_button.clicked.connect(clipboardContainer.toggle_delete_mode)  # type: ignore


def start_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



