from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QGridLayout, QVBoxLayout, QLabel, QFrame, QScrollArea,
                             QCheckBox, QHBoxLayout, QSizePolicy, QMessageBox, QStackedWidget)
import sys

# Import our new clipboard manager
from clipboard_manager import ClipboardManager, ClipboardTextEntry, attach_new_clipboard


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


class DynamicContentWidget(QWidget):
    """Base class for different content pages"""

    def __init__(self, color, text):
        super().__init__()
        layout = QVBoxLayout()

        # Create a colored frame
        frame = QFrame(self)
        frame.setAutoFillBackground(True)
        palette = frame.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        frame.setPalette(palette)
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setFrameShadow(QFrame.Shadow.Raised)

        # Layout for the frame
        frame_layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(label)
        frame.setLayout(frame_layout)

        layout.addWidget(frame)
        self.setLayout(layout)


# this class will set the clipboard data into frame
class ClipInFrame(QWidget):
    def __init__(self, clip):
        super().__init__()  # Initialize QWidget
        """Dynamically add a frame for a new clipboard entry"""
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(3)
        self.frame.setStyleSheet("background-color: rgb(255,85,255);")
        self.clip = clip

        # Add content label
        label = QLabel(str(clip.content), self.frame)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.checkbox = QCheckBox(self.frame)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)  # type: ignore
        self.checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.frameSelected = False

        # Layout for frame
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(label)
        frame_layout.addWidget(self.checkbox)
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

        # Initialize the clipboard manager
        self.clipboard_manager = ClipboardManager()

        # Start clipboard monitoring in a separate thread
        self.clipboard_manager.start_monitoring()

        self.clips = {}  # {clip_id: ClipInFrame object}
        self.frames = {}  # {clip_id: QFrame widget}

        # mouse event when press on frame
        self.pressPos = None
        self.clicked = QtCore.pyqtSignal()

        # Populate UI with existing clips
        self.populate_clips()

        # Timer to check for UI updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_updates)  # type: ignore
        self.timer.start(1000)  # Check every second

    def populate_clips(self):
        """Create frames for existing clipboard content"""
        # Clear existing frames first for safety
        for frame in self.frames.values():
            self.scroll_layout.removeWidget(frame)
            if frame is not None:
                frame.deleteLater()

        self.frames.clear()
        self.clips.clear()

        # Get all entries from manager
        entries = self.clipboard_manager.get_all_entries()

        # Add frames for all entries
        for clip in entries:
            clip_frame = ClipInFrame(clip)
            self.scroll_layout.insertWidget(0, clip_frame.frame)  # Add newest first at the top
            self.frames[clip.id] = clip_frame.frame
            self.clips[clip.id] = clip_frame

    def check_for_updates(self):
        """Check for changes in clipboard entries"""
        # Reload entries from manager
        self.clipboard_manager.load_entries()
        current_entries = self.clipboard_manager.get_all_entries()

        # Get current IDs in UI and in data
        ui_ids = set(self.frames.keys())
        data_ids = {entry.id for entry in current_entries}

        # Handle removed entries
        for clip_id in (ui_ids - data_ids):
            if clip_id in self.frames:
                frame = self.frames[clip_id]
                self.scroll_layout.removeWidget(frame)
                frame.deleteLater()
                del self.frames[clip_id]
                del self.clips[clip_id]

        # Handle new entries
        for entry in current_entries:
            if entry.id not in ui_ids:
                clip_frame = ClipInFrame(entry)
                self.scroll_layout.insertWidget(0, clip_frame.frame)  # Add at top
                self.frames[entry.id] = clip_frame.frame
                self.clips[entry.id] = clip_frame

        # Update scroll area sizing
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content.setMinimumHeight(self.scroll_layout.sizeHint().height())

    # this function will delete selected clipboards that user want to delete
    def toggle_delete_mode(self):
        to_delete = []  # Collect items to delete first

        for clip_id, clip_frame in self.clips.items():
            if clip_frame.frameSelected:
                to_delete.append(clip_id)  # Store the ID for deletion

        # If the list is empty, messagebox will appear
        if not to_delete:
            show_message("Please select items to delete from the clipboard")
            return

        # Delete from manager (handles file saving too)
        self.clipboard_manager.delete_entries(to_delete)

        # Update UI
        for clip_id in to_delete:
            if clip_id in self.frames:
                frame = self.frames[clip_id]
                self.scroll_layout.removeWidget(frame)
                frame.deleteLater()
                del self.frames[clip_id]
                del self.clips[clip_id]

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

            for clip_id, frame in self.frames.items():
                frame_position = frame.pos()
                print(f"Frame Position: {frame_position.x()}, {frame_position.y()}")
                print(f"Frame size: {frame.width()} x {frame.height()}")

                frame_rect = QRect(frame_position.x(), frame_position.y(), frame.width(), frame.height())
                if frame_rect.contains(self.pressPos):  # Check if the click is inside the frame
                    print(f"Clicked on frame: {clip_id}")

                    # Get the content and copy to system clipboard
                    entry = self.clipboard_manager.get_entry_by_id(clip_id)
                    if entry:
                        self.selected_clip = entry.content
                        print(f"Selected clip content: {self.selected_clip[:30]}...")
                        attach_new_clipboard(self.selected_clip)
        except Exception as e:
            print(f"Error finding frame: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.setWindowTitle("ClipSavvy")
        self.setContentsMargins(20, 20, 20, 20)

        # Create a central widget
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        # Layouts
        self.menuLayout = QGridLayout()
        self.menuLayout.setSpacing(20)

        self.masterLayout = QGridLayout()
        self.masterLayout.addLayout(self.menuLayout, 0, 0)

        # Buttons
        self.text_button = QPushButton(text="Text")
        self.delete_button = QPushButton(text="Delete")
        self.image_button = QPushButton("Images")
        self.settings_button = QPushButton("Settings")

        # connect buttons
        self.text_button.clicked.connect(self.show_previous_page)  # type: ignore
        self.image_button.clicked.connect(self.show_next_page)  # type: ignore
        self.menuLayout.addWidget(self.text_button, 1, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.delete_button, 0, 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.image_button, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.menuLayout.addWidget(self.settings_button, 0, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        # Stacked widget to hold different content pages
        self.stacked_widget = QStackedWidget()

        # Create and add the clipboard container
        self.text_based_clipboard = ClipboardContainer()
        self.page2 = DynamicContentWidget("lightgreen", "Second Page\nMultiple Layouts Supported")
        self.stacked_widget.addWidget(self.text_based_clipboard)
        self.stacked_widget.addWidget(self.page2)
        self.masterLayout.addWidget(self.stacked_widget)

        # Set the layout on the central widget
        self.centralWidget.setLayout(self.masterLayout)

        # Connect the delete button to the container's toggle_delete_mode method
        self.delete_button.clicked.connect(self.text_based_clipboard.toggle_delete_mode)  # type: ignore

    def show_previous_page(self):
        """Navigate to the previous page"""
        current_index = self.stacked_widget.currentIndex()
        total_pages = self.stacked_widget.count()

        # Circular navigation
        new_index = (current_index - 1 + total_pages) % total_pages
        self.stacked_widget.setCurrentIndex(new_index)

    def show_next_page(self):
        """Navigate to the next page"""
        current_index = self.stacked_widget.currentIndex()
        total_pages = self.stacked_widget.count()

        # Circular navigation
        new_index = (current_index + 1) % total_pages
        self.stacked_widget.setCurrentIndex(new_index)


def start_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_gui()
