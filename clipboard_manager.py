# clipboard_manager.py
import base64
import io
import os
import time
import uuid
import json
import threading
from datetime import datetime

import pyperclip
from PIL import ImageGrab, Image

JSON_FILE = "clipboard_history.json"


class ClipboardManager:
    _instance = None

    # Singleton pattern to ensure only one manager exists
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, json_file=JSON_FILE):
        # Only initialize once
        if self.initialized:
            return

        self.json_file = json_file
        self.entries = []
        self.last_save_time = time.time()
        self.save_interval = 2  # Save every 2 seconds if changes
        self.changes_pending = False
        self.monitoring_active = False

        # Load existing entries on startup
        self.load_entries()
        self.initialized = True

    def load_entries(self):
        """Load clipboard entries from JSON file"""
        self.entries = load_from_json_file(self.json_file)

    def save_entries(self, force=False):
        """Save entries to JSON file if changes pending or forced"""
        current_time = time.time()
        if (force or self.changes_pending) and (current_time - self.last_save_time >= self.save_interval):
            data = [entry.to_dict() for entry in self.entries]

            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            self.last_save_time = current_time
            self.changes_pending = False
            print(f"Saved {len(data)} entries to JSON file: {self.json_file}")

    def is_entry_exist(self ,content):

        for entry in self.entries:
            if content == entry.content:
                return True

    def add_entry(self, content):
        """Add a new clipboard entry"""
        # Skip if content is empty or already exists as the most recent entry
        if not content or (self.entries and self.entries[0].content == content):
            return None

        # Create new entry with unique ID
        new_entry = ClipboardTextEntry(content)

        # Add to in-memory list at the beginning (newest first)
        self.entries.insert(0, new_entry)

        # Mark changes as pending
        self.changes_pending = True

        # Try to save
        self.save_entries()

        return new_entry

    def delete_entry(self, entry_id):
        """Delete an entry by ID"""
        original_length = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.id != entry_id]

        # If an entry was actually removed
        if len(self.entries) < original_length:
            self.changes_pending = True
            # Force save after deletion
            self.save_entries(force=True)
            return True
        return False

    def delete_entries(self, entry_ids):
        """Delete multiple entries by ID"""
        if not entry_ids:
            return False

        original_length = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.id not in entry_ids]

        # If entries were actually removed
        if len(self.entries) < original_length:
            self.changes_pending = True
            # Force save after deletion
            self.save_entries(force=True)
            return True
        return False

    def get_all_entries(self):
        """Get all clipboard entries"""
        return self.entries

    def get_entry_by_id(self, entry_id):
        """Get a specific entry by ID"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def start_monitoring(self):
        """Start monitoring clipboard in a separate thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.clipboard_thread = threading.Thread(
                target=self._monitor_clipboard,
                daemon=True
            )
            self.clipboard_thread.start()

    def _monitor_clipboard(self):
        """Background thread function to monitor clipboard changes"""
        last_clipboard_content = ""

        while self.monitoring_active:
            try:
                current_clipboard_content = pyperclip.paste()

                # Only process if content changed and is not empty
                if not self.is_entry_exist(current_clipboard_content):
                    print(f"Clipboard changed: {current_clipboard_content[:30]}...")
                    last_clipboard_content = current_clipboard_content

                    # Add to manager
                    self.add_entry(current_clipboard_content)

                # Periodically try to save any pending changes
                self.save_entries()

                time.sleep(1)  # Check every second

            except Exception as e:
                print(f"Error in clipboard monitoring: {e}")
                time.sleep(5)  # Wait a bit longer if there's an error


# ClipboardTextEntry class
class ClipboardTextEntry:
    def __init__(self, content, id=None, timestamp=None):
        self.content = content if content is not None else ""  # Ensure empty string instead of None
        self.id = id if id is not None else str(uuid.uuid4())  # Generate a unique ID if not provided
        self.timestamp = timestamp if timestamp is not None else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data):
        """Convert dictionary back to a ClipboardTextEntry object."""
        entry = cls(content=data["content"], id=data["id"], timestamp=data["timestamp"])
        return entry


# Legacy functions for backward compatibility
def save_to_json_file(clipboard_entry):
    """Saves the clipboard entry to a JSON file."""
    manager = ClipboardManager()
    manager.add_entry(clipboard_entry.content)


def load_from_json_file(filename=JSON_FILE):
    """Load clipboard history from a JSON file."""
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            # Create a list of ClipboardTextEntry objects from the loaded data
            return [ClipboardTextEntry.from_dict(entry) for entry in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def remove_entries_by_id(json_file, ids_to_delete):
    """Remove entries by ID"""
    if isinstance(ids_to_delete, str):  # If single ID passed as string
        ids_to_delete = [ids_to_delete]

    manager = ClipboardManager(json_file)
    manager.delete_entries(ids_to_delete)


def attach_new_clipboard(to_paste):
    """Set clipboard content"""
    pyperclip.copy(to_paste)


# Legacy check_clipboard function (not needed when using manager)
def check_clipboard():
    manager = ClipboardManager()
    manager.start_monitoring()