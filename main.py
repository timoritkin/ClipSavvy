import threading

import pystray
import PIL.Image
import clipboard
import GUI
image = PIL.Image.open("images/testLogo.png")


def on_click(icon, item):

    if str(item) == "Start":
        # Start clipboard monitoring in a background thread
        clipboard_thread = threading.Thread(target=clipboard.check_clipboard)  # Pass window to the thread
        clipboard_thread.start()

    elif str(item) == "my clips":
        gui_thread = threading.Thread(target=GUI.start_gui, daemon=True)
        gui_thread.start()


icon = pystray.Icon("ClipSavvy", image, menu=pystray.Menu(
    pystray.MenuItem("Start", on_click),
    pystray.MenuItem("my clips", on_click)
))

icon.run()