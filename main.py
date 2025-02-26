import base64
import io
import os
import time
import uuid
from datetime import datetime
import json
import pyperclip
import threading
import keyboard
from PIL import ImageGrab, Image

JSON_FILE = "clipboard_history.json"


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
            return [ClipboardEntry.from_dict(entry) for entry in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def on_copy():
    """Triggers when Ctrl+C is pressed."""
    time.sleep(0.05)  # Wait 50ms to ensure clipboard updates
    currently_copied_content = pyperclip.paste()
    print(currently_copied_content)
    ce = ClipboardEntry(currently_copied_content)
    ce.to_dict()
    save_to_json_file(ce)
    print(currently_copied_content)
    return False  # Stop listening if needed


def _convert_image_to_bytes(image):
    """Converts an image to bytes for storage."""
    if isinstance(image, Image.Image):
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")  # Save as PNG or any format you need
        return img_buffer.getvalue()  # Return the byte data
    return None


class ClipboardEntry:
    def __init__(self, content=None, image=None):
        self.id = str(uuid.uuid4())  # Generate a unique ID
        self.timestamp = datetime.now().isoformat()  # Store timestamp
        self.content = content  # Store text
        self.image = _convert_image_to_bytes(image) if image else None  # Store image as bytes

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content,
            "image": self.image_to_base64()  # Convert image to Base64 string
        }

    def image_to_base64(self):
        """Converts image bytes to a Base64 string."""
        if self.image:
            return base64.b64encode(self.image).decode('utf-8')  # Encode bytes to Base64 string
        return None

    @staticmethod
    def from_base64(self, base64_string):
        """Converts Base64 string back to image bytes."""
        return base64.b64decode(base64_string)

    @classmethod
    def from_dict(cls, data):
        """Convert dictionary back to a ClipboardEntry object."""
        entry = cls(content=data["content"])
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        entry.image = data["image"]
        return entry


if __name__ == "__main__":

    clipboard_thread = threading.Thread(target=check_clipboard, daemon=True)
    clipboard_thread.start()

    while True:
        # Start listening for key presses
        keyboard.add_hotkey('ctrl+c', on_copy)
        # Keep the program running
        keyboard.wait()
