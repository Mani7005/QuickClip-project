import tkinter as tk
import pyperclip
import sqlite3
from datetime import datetime
import keyboard  # For hotkey support
import atexit  # For clean exit handling

# Database setup (with thread safety enabled)
conn = sqlite3.connect("clipboard_history.db", check_same_thread=False)
cursor = conn.cursor()

def setup_database():
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY,
                content TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database setup error: {e}")

setup_database()

class QuickClip:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuickClip")
        self.root.geometry("400x300")
        self.last_clip = ""  # Track last copied item
        
        # Register cleanup function
        atexit.register(self.cleanup)
        
        # UI Setup
        self.setup_ui()
        
        # Hotkey Setup
        self.setup_hotkey()
        
        # Start clipboard monitoring
        self.check_clipboard()

    def setup_ui(self):
        """Create the user interface"""
        # Main listbox
        self.listbox = tk.Listbox(self.root, width=50, height=15)
        self.listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Frame for buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X)
        
        # Copy selected button
        copy_btn = tk.Button(button_frame, text="Copy", command=self.copy_selected)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear history button
        clear_btn = tk.Button(button_frame, text="Clear", command=self.clear_history)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(button_frame, text="Hide", command=self.hide_window)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        self.update_listbox()

    def setup_hotkey(self):
        """Register the show/hide hotkey"""
        try:
            keyboard.add_hotkey('ctrl+shift+v', self.toggle_window)
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        except Exception as e:
            print(f"Hotkey setup error: {e}")

    def check_clipboard(self):
        """Check for clipboard changes (non-threaded polling)"""
        try:
            current_clip = pyperclip.paste()
            
            # Only save if content changed and isn't empty
            if current_clip != self.last_clip and current_clip.strip():
                self.save_clip(current_clip)
                self.last_clip = current_clip
        except Exception as e:
            print(f"Clipboard check error: {e}")
            
        # Check again after 500ms
        self.root.after(500, self.check_clipboard)

    def save_clip(self, content):
        """Save content to database"""
        try:
            cursor.execute(
                "INSERT INTO clips (content, timestamp) VALUES (?, ?)",
                (content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            self.update_listbox()
        except sqlite3.Error as e:
            print(f"Database save error: {e}")

    def update_listbox(self):
        """Refresh the list of clips"""
        try:
            self.listbox.delete(0, tk.END)
            clips = cursor.execute(
                "SELECT content FROM clips ORDER BY id DESC LIMIT 20"
            ).fetchall()
            for clip in clips:
                self.listbox.insert(tk.END, clip[0])
        except sqlite3.Error as e:
            print(f"Database read error: {e}")

    def copy_selected(self):
        """Copy selected item back to clipboard"""
        try:
            selection = self.listbox.curselection()
            if selection:
                selected_text = self.listbox.get(selection[0])
                pyperclip.copy(selected_text)
        except Exception as e:
            print(f"Copy error: {e}")

    def clear_history(self):
        """Delete all clipboard history"""
        try:
            cursor.execute("DELETE FROM clips")
            conn.commit()
            self.update_listbox()
            self.last_clip = ""  # Reset last clip tracking
        except sqlite3.Error as e:
            print(f"Clear history error: {e}")

    def toggle_window(self):
        """Show/hide the window"""
        try:
            if self.root.state() == 'withdrawn':
                self.root.deiconify()
                self.root.lift()
            else:
                self.hide_window()
        except Exception as e:
            print(f"Window toggle error: {e}")

    def hide_window(self):
        """Minimize to background"""
        try:
            self.root.withdraw()
        except Exception as e:
            print(f"Hide window error: {e}")

    def cleanup(self):
        """Clean up resources"""
        try:
            cursor.close()
            conn.close()
        except sqlite3.Error as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    app = QuickClip()
    app.root.mainloop()