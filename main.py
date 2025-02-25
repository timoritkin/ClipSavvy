import os
import time
import uuid
from datetime import datetime
import json
import pyperclip

import keyboard

JSON_FILE = "clipboard_history.json"


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


class ClipboardEntry:
    def __init__(self, content=None, image=None):
        self.id = str(uuid.uuid4())  # Generate a unique ID
        self.timestamp = datetime.now().isoformat()  # Store timestamp
        self.content = content  # Store text
        # self.image = self._convert_image_to_bytes(image) if image else None  # Store image as bytes

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content,
            # "image": self.image  # Stored as a hex string
        }

    @classmethod
    def from_dict(cls, data):
        """Convert dictionary back to a ClipboardEntry object."""
        entry = cls(content=data["content"])
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        # entry.image = data["image"]
        return entry


while True:
    # Start listening for key presses
    keyboard.add_hotkey('ctrl+c', on_copy)
    # Keep the program running
    keyboard.wait()
