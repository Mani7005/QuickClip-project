import tkinter as tk
from tkinter import ttk
import pyperclip
import sqlite3
from datetime import datetime
import keyboard
import atexit

# SQLite setup
conn = sqlite3.connect("clipboard_history.db", check_same_thread=False)
cursor = conn.cursor()

def setup_database():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY,
            content TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()

setup_database()

class QuickClip:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuickClip - Clipboard Manager")
        self.root.geometry("600x400")
        self.root.configure(bg="#f5f5f5")
        self.root.minsize(500, 300)

        self.last_clip = ""
        self.ignore_next_clip = False

        atexit.register(self.cleanup)

        self.setup_ui()
        self.setup_hotkey()
        self.check_clipboard()

    def setup_ui(self):
        # Title Label
        title = tk.Label(self.root, text="QuickClip", font=("Segoe UI", 14, "bold"),
                         bg="#f5f5f5", fg="#333")
        title.pack(pady=(10, 5))

        # Frame for Listbox + Scrollbars
        frame = tk.Frame(self.root, bg="#f5f5f5")
        frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Scrollbars
        y_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
        x_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL)

        # Listbox with both scrollbars
        self.listbox = tk.Listbox(frame,
                                  font=("Consolas", 10),
                                  bg="white",
                                  fg="#111",
                                  selectbackground="#d0d0d0",
                                  selectforeground="#000",
                                  activestyle="none",
                                  relief=tk.FLAT,
                                  yscrollcommand=y_scroll.set,
                                  xscrollcommand=x_scroll.set)

        y_scroll.config(command=self.listbox.yview)
        x_scroll.config(command=self.listbox.xview)

        # Grid layout for better alignment
        self.listbox.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Buttons frame
        button_frame = tk.Frame(self.root, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        copy_btn = ttk.Button(button_frame, text="Copy", command=self.copy_selected)
        clear_btn = ttk.Button(button_frame, text="Clear", command=self.clear_history)
        hide_btn = ttk.Button(button_frame, text="Hide", command=self.hide_window)

        copy_btn.pack(side=tk.LEFT, padx=5)
        clear_btn.pack(side=tk.LEFT, padx=5)
        hide_btn.pack(side=tk.RIGHT, padx=5)

        self.update_listbox()

    def setup_hotkey(self):
        try:
            keyboard.add_hotkey('ctrl+shift+v', self.toggle_window)
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        except Exception as e:
            print(f"Hotkey setup error: {e}")

    def check_clipboard(self):
        try:
            current_clip = pyperclip.paste()
            if self.ignore_next_clip:
                self.ignore_next_clip = False
                self.last_clip = current_clip
                self.root.after(500, self.check_clipboard)
                return

            if current_clip != self.last_clip and current_clip.strip():
                self.save_clip(current_clip)
                self.last_clip = current_clip
        except Exception as e:
            print(f"Clipboard check error: {e}")

        self.root.after(500, self.check_clipboard)

    def save_clip(self, content):
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
        try:
            self.listbox.delete(0, tk.END)
            clips = cursor.execute(
                "SELECT content FROM clips ORDER BY id DESC LIMIT 50"
            ).fetchall()
            for clip in clips:
                self.listbox.insert(tk.END, clip[0])
        except sqlite3.Error as e:
            print(f"Database read error: {e}")

    def copy_selected(self):
        try:
            selection = self.listbox.curselection()
            if selection:
                selected_text = self.listbox.get(selection[0])
                self.ignore_next_clip = True
                pyperclip.copy(selected_text)
        except Exception as e:
            print(f"Copy error: {e}")

    def clear_history(self):
        try:
            cursor.execute("DELETE FROM clips")
            conn.commit()
            self.update_listbox()
            self.last_clip = ""
        except sqlite3.Error as e:
            print(f"Clear history error: {e}")

    def toggle_window(self):
        try:
            if self.root.state() == 'withdrawn':
                self.root.deiconify()
                self.root.lift()
            else:
                self.hide_window()
        except Exception as e:
            print(f"Window toggle error: {e}")

    def hide_window(self):
        try:
            self.root.withdraw()
        except Exception as e:
            print(f"Hide window error: {e}")

    def cleanup(self):
        try:
            cursor.close()
            conn.close()
        except sqlite3.Error as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    app = QuickClip()
    app.root.mainloop()

