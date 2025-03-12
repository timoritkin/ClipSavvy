import base64
import io
import os
import time
import uuid
import json
import pyperclip
from PIL import ImageGrab, Image

JSON_FILE = "clipboard_history.json"


def remove_entries_by_id(json_file, ids_to_delete):
    # Load existing clipboard history
    with open(json_file, "r") as file:
        clipboard_data = json.load(file)

        # Keep only entries whose ID is NOT in `ids_to_delete`
    clipboard_data = [entry for entry in clipboard_data if entry["id"] not in ids_to_delete]

    # Save the updated clipboard history back to the file
    with open(json_file, "w") as file:
        json.dump(clipboard_data, file, indent=4)


# Function will set new clipboard to paste that user selected from its list
def attach_new_clipboard(to_paste):
    pyperclip.copy(to_paste)


# Function to check clipboard contents
def check_clipboard():
    last_clipboard_content = ""
    last_img_content = ""
    while True:
        current_clipboard_content = pyperclip.paste()
        img = ImageGrab.grabclipboard()
        if current_clipboard_content != last_clipboard_content:
            print(f"Clipboard changed: {current_clipboard_content}")
            last_clipboard_content = current_clipboard_content
            ce = ClipboardEntry(current_clipboard_content, None)
            ce.to_dict()
            save_to_json_file(ce)
        if last_img_content != img:
            print(f"Clipboard changed: {img}")
            last_img_content = img
            ce = ClipboardEntry(None, img)
            ce.to_dict()
            save_to_json_file(ce)
        time.sleep(1)  # Check clipboard every second


def save_to_json_file(clipboard_entry):
    """Saves the clipboard entry to a JSON file."""
    data = []

    # If file exists, load existing data
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # Append the new clipboard entry
    data.append(clipboard_entry.to_dict())

    # Write back to the file
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("Saved to JSON file:", JSON_FILE)


def load_from_json_file(filename="clipboard_history.json"):
    """Load clipboard history from a JSON file."""
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            # Create a list of ClipboardEntry objects from the loaded data
            return [ClipboardEntry.from_dict(entry) for entry in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _convert_image_to_bytes(image):
    """Converts an image to bytes for storage."""
    if isinstance(image, Image.Image):
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")  # Save as PNG or any format you need
        return img_buffer.getvalue()  # Return the byte data
    return None


class ClipboardEntry:
    def __init__(self, content, id=None, timestamp=None):
        self.content = content
        self.id = id if id is not None else str(uuid.uuid4())  # Generate a unique ID if not provided
        self.timestamp = timestamp if timestamp is not None else time.time()  # Use current time if timestamp is None
        # self.image = _convert_image_to_bytes(image) if image else None  # Store image as bytes

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content,
        }

    # def image_to_base64(self):
    #     """Converts image bytes to a Base64 string."""
    #     if self.image:
    #         return base64.b64encode(self.image).decode('utf-8')  # Encode bytes to Base64 string
    #     return None

    @staticmethod
    def from_base64(self, base64_string):
        """Converts Base64 string back to image bytes."""
        return base64.b64decode(base64_string)

    @classmethod
    def from_dict(cls, data):
        """Convert dictionary back to a ClipboardEntry object."""
        entry = cls(content=data["content"], id=data["id"], timestamp=data["timestamp"])
        # If you're handling images, you might want to set `entry.image` here
        return entry
