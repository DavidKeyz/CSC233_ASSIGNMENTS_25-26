import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, asdict
from typing import List


KEYS_12 = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
DATA_FILE = "songs_data.json"


@dataclass
class Song:
    name: str
    artists: str
    primary_key: str
    modulated_keys: List[str]

    def includes_key(self, key: str) -> bool:
        if key == "All":
            return True
        return self.primary_key == key or key in self.modulated_keys


class SongBankApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gospel Piano Key Trainer")
        self.root.geometry("1100x700")
        self.root.minsize(980, 620)

        self.songs: List[Song] = []
        self.theme = "light"
        self.selected_song_index = None

        self.palette = {
            "light": {
                "bg": "#f5f5f5",
                "panel": "#ffffff",
                "text": "#1f1f1f",
                "muted": "#5f6368",
                "accent": "#2b2b2b",
                "border": "#d9d9d9",
                "button_bg": "#ededed",
                "list_bg": "#ffffff",
            },
            "dark": {
                "bg": "#1f1f1f",
                "panel": "#2a2a2a",
                "text": "#f3f3f3",
                "muted": "#b5b5b5",
                "accent": "#ffffff",
                "border": "#454545",
                "button_bg": "#373737",
                "list_bg": "#232323",
            },
        }

        self.build_ui()
        self.load_data()
        self.refresh_song_tree()
        self.refresh_frequency_panel()
        self.apply_theme()

    def build_ui(self):
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(1, weight=1)

        self.header = tk.Frame(self.root)
        self.header.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=16, pady=(16, 8))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = tk.Label(
            self.header,
            text="Gospel Song Bank · 12 Key Practice",
            font=("Segoe UI", 16, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.theme_button = tk.Button(self.header, text="Toggle Theme", command=self.toggle_theme, width=14)
        self.theme_button.grid(row=0, column=1, sticky="e")

        self.left_panel = tk.Frame(self.root)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 16))
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        filter_frame = tk.Frame(self.left_panel)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        filter_frame.grid_columnconfigure(2, weight=1)

        tk.Label(filter_frame, text="Filter by key:").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.filter_key_var = tk.StringVar(value="All")
        self.filter_combo = ttk.Combobox(filter_frame, values=["All"] + KEYS_12, state="readonly", textvariable=self.filter_key_var, width=8)
        self.filter_combo.grid(row=0, column=1, sticky="w")
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_song_tree())

        self.export_button = tk.Button(filter_frame, text="Export to .txt", command=self.export_to_txt, width=14)
        self.export_button.grid(row=0, column=3, sticky="e")

        table_frame = tk.Frame(self.left_panel)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "artists", "primary", "modulated")
        self.song_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.song_tree.heading("name", text="Song")
        self.song_tree.heading("artists", text="Artist(s)")
        self.song_tree.heading("primary", text="Primary Key")
        self.song_tree.heading("modulated", text="Modulated Key(s)")

        self.song_tree.column("name", width=280, anchor="w")
        self.song_tree.column("artists", width=210, anchor="w")
        self.song_tree.column("primary", width=100, anchor="center")
        self.song_tree.column("modulated", width=180, anchor="w")

        self.song_tree.grid(row=0, column=0, sticky="nsew")
        self.song_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.song_tree.yview)
        self.song_tree.configure(yscrollcommand=yscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")

        self.right_panel = tk.Frame(self.root)
        self.right_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(0, 16))
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        form_frame = tk.Frame(self.right_panel)
        form_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        form_frame.grid_columnconfigure(0, weight=1)

        tk.Label(form_frame, text="Song Name").grid(row=0, column=0, sticky="w")
        self.song_name_var = tk.StringVar()
        self.song_name_entry = tk.Entry(form_frame, textvariable=self.song_name_var)
        self.song_name_entry.grid(row=1, column=0, sticky="ew", pady=(2, 10))

        tk.Label(form_frame, text="Artist(s) (comma-separated)").grid(row=2, column=0, sticky="w")
        self.artists_var = tk.StringVar()
        self.artists_entry = tk.Entry(form_frame, textvariable=self.artists_var)
        self.artists_entry.grid(row=3, column=0, sticky="ew", pady=(2, 0))
        self.artists_entry.bind("<KeyRelease>", self.update_artist_suggestions)
        self.artists_entry.bind("<FocusIn>", self.update_artist_suggestions)

        self.suggestion_list = tk.Listbox(form_frame, height=4)
        self.suggestion_list.grid(row=4, column=0, sticky="ew", pady=(2, 10))
        self.suggestion_list.bind("<<ListboxSelect>>", self.apply_artist_suggestion)

        tk.Label(form_frame, text="Primary Key").grid(row=5, column=0, sticky="w")
        self.primary_key_var = tk.StringVar(value=KEYS_12[0])
        self.primary_key_combo = ttk.Combobox(form_frame, values=KEYS_12, textvariable=self.primary_key_var, state="readonly")
        self.primary_key_combo.grid(row=6, column=0, sticky="ew", pady=(2, 10))

        self.has_modulation_var = tk.BooleanVar(value=False)
        self.has_mod_chk = tk.Checkbutton(form_frame, text="Has modulation", variable=self.has_modulation_var, command=self.toggle_modulation)
        self.has_mod_chk.grid(row=7, column=0, sticky="w")

        mod_frame = tk.LabelFrame(form_frame, text="Modulated Key(s)")
        mod_frame.grid(row=8, column=0, sticky="ew", pady=(8, 10))
        mod_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.mod_vars = {}
        self.mod_checkbuttons = {}
        for i, k in enumerate(KEYS_12):
            var = tk.BooleanVar(value=False)
            self.mod_vars[k] = var
            cb = tk.Checkbutton(mod_frame, text=k, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=6, pady=2)
            self.mod_checkbuttons[k] = cb

        action_frame = tk.Frame(form_frame)
        action_frame.grid(row=9, column=0, sticky="ew")
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.add_button = tk.Button(action_frame, text="Add Song", command=self.add_song)
        self.add_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.update_button = tk.Button(action_frame, text="Update Selected", command=self.update_song)
        self.update_button.grid(row=0, column=1, sticky="ew", padx=3)

        self.clear_button = tk.Button(action_frame, text="Clear Form", command=self.clear_form)
        self.clear_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        freq_frame = tk.LabelFrame(self.right_panel, text="Key Frequency (High → Low)")
        freq_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        freq_frame.grid_rowconfigure(0, weight=1)
        freq_frame.grid_columnconfigure(0, weight=1)

        self.frequency_text = tk.Text(freq_frame, height=10, wrap="word", state="disabled", relief="flat")
        self.frequency_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.toggle_modulation()

    def apply_theme(self):
        colors = self.palette[self.theme]
        self.root.configure(bg=colors["bg"])

        for panel in [self.header, self.left_panel, self.right_panel]:
            panel.configure(bg=colors["panel"], highlightbackground=colors["border"], highlightthickness=1)

        for widget in self.root.winfo_children():
            self._theme_widget_recursive(widget, colors)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=colors["list_bg"], foreground=colors["text"], fieldbackground=colors["list_bg"], bordercolor=colors["border"])
        style.configure("Treeview.Heading", background=colors["button_bg"], foreground=colors["text"], relief="flat")
        style.map("Treeview", background=[("selected", "#6f6f6f")], foreground=[("selected", "#ffffff")])

        self.frequency_text.configure(bg=colors["list_bg"], fg=colors["text"], insertbackground=colors["text"])

    def _theme_widget_recursive(self, widget, colors):
        cls = widget.winfo_class()
        if cls in {"Frame", "Labelframe", "TFrame"}:
            widget.configure(bg=colors["panel"])
        elif cls == "Label":
            widget.configure(bg=colors["panel"], fg=colors["text"])
        elif cls in {"Entry", "Text", "Listbox"}:
            widget.configure(bg=colors["list_bg"], fg=colors["text"], insertbackground=colors["text"], highlightbackground=colors["border"])
        elif cls == "Button":
            widget.configure(
                bg=colors["button_bg"],
                fg=colors["text"],
                activebackground=colors["panel"],
                activeforeground=colors["text"],
                relief="flat",
            )
        elif cls == "Checkbutton":
            widget.configure(
                bg=colors["button_bg"],
                fg=colors["text"],
                activebackground=colors["panel"],
                activeforeground=colors["text"],
                selectcolor=colors["panel"],
                relief="flat",
            )
        elif cls in {"Labelframe"}:
            widget.configure(bg=colors["panel"], fg=colors["text"])

        for child in widget.winfo_children():
            self._theme_widget_recursive(child, colors)

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.apply_theme()

    def toggle_modulation(self):
        enabled = self.has_modulation_var.get()
        state = "normal" if enabled else "disabled"
        if not enabled:
            for var in self.mod_vars.values():
                var.set(False)

        for key, cb in self.mod_checkbuttons.items():
            cb.configure(state=state)

    def get_selected_modulated_keys(self) -> List[str]:
        if not self.has_modulation_var.get():
            return []
        selected = [k for k, var in self.mod_vars.items() if var.get()]
        return [k for k in selected if k != self.primary_key_var.get()]

    def validate_form(self) -> bool:
        if not self.song_name_var.get().strip():
            messagebox.showerror("Validation", "Please enter a song name.")
            return False
        if not self.artists_var.get().strip():
            messagebox.showerror("Validation", "Please enter at least one artist.")
            return False
        if self.primary_key_var.get() not in KEYS_12:
            messagebox.showerror("Validation", "Please choose a valid primary key.")
            return False
        return True

    def add_song(self):
        if not self.validate_form():
            return

        song = Song(
            name=self.song_name_var.get().strip(),
            artists=self.normalize_artists(self.artists_var.get()),
            primary_key=self.primary_key_var.get(),
            modulated_keys=self.get_selected_modulated_keys(),
        )
        self.songs.append(song)
        self.save_data()
        self.refresh_song_tree()
        self.refresh_frequency_panel()
        self.clear_form()

    def update_song(self):
        if self.selected_song_index is None:
            messagebox.showinfo("Edit", "Please select a song from the list to update.")
            return
        if not self.validate_form():
            return

        self.songs[self.selected_song_index] = Song(
            name=self.song_name_var.get().strip(),
            artists=self.normalize_artists(self.artists_var.get()),
            primary_key=self.primary_key_var.get(),
            modulated_keys=self.get_selected_modulated_keys(),
        )
        self.save_data()
        self.refresh_song_tree()
        self.refresh_frequency_panel()
        self.clear_form()

    def clear_form(self):
        self.song_name_var.set("")
        self.artists_var.set("")
        self.primary_key_var.set(KEYS_12[0])
        self.has_modulation_var.set(False)
        for var in self.mod_vars.values():
            var.set(False)
        self.suggestion_list.delete(0, tk.END)
        self.selected_song_index = None
        self.song_tree.selection_remove(self.song_tree.selection())

    def refresh_song_tree(self):
        for row in self.song_tree.get_children():
            self.song_tree.delete(row)

        filter_key = self.filter_key_var.get()
        for idx, song in enumerate(self.songs):
            if song.includes_key(filter_key):
                self.song_tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(song.name, song.artists, song.primary_key, ", ".join(song.modulated_keys) if song.modulated_keys else "—"),
                )

    def refresh_frequency_panel(self):
        counts = {k: 0 for k in KEYS_12}
        for song in self.songs:
            counts[song.primary_key] += 1
            for k in song.modulated_keys:
                if k in counts:
                    counts[k] += 1

        sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], KEYS_12.index(item[0])))

        self.frequency_text.configure(state="normal")
        self.frequency_text.delete("1.0", tk.END)
        self.frequency_text.insert("1.0", "Practice priority based on your songs:\n\n")
        for i, (k, c) in enumerate(sorted_counts, start=1):
            self.frequency_text.insert(tk.END, f"{i:>2}. {k:<2}  —  {c} song(s)\n")
        self.frequency_text.configure(state="disabled")

    def on_tree_select(self, _event):
        selected = self.song_tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        if idx >= len(self.songs):
            return
        song = self.songs[idx]
        self.selected_song_index = idx

        self.song_name_var.set(song.name)
        self.artists_var.set(song.artists)
        self.primary_key_var.set(song.primary_key)

        has_mod = len(song.modulated_keys) > 0
        self.has_modulation_var.set(has_mod)
        for k, var in self.mod_vars.items():
            var.set(k in song.modulated_keys)

    def get_known_artists(self) -> List[str]:
        artist_set = set()
        for song in self.songs:
            for artist in [a.strip() for a in song.artists.split(",") if a.strip()]:
                artist_set.add(artist)
        return sorted(artist_set, key=lambda s: s.lower())

    def update_artist_suggestions(self, _event=None):
        text = self.artists_var.get().strip()
        tail = text.split(",")[-1].strip().lower() if text else ""
        known = self.get_known_artists()

        self.suggestion_list.delete(0, tk.END)
        if not known:
            return

        for artist in known:
            if tail == "" or artist.lower().startswith(tail):
                self.suggestion_list.insert(tk.END, artist)

    def apply_artist_suggestion(self, _event=None):
        selection = self.suggestion_list.curselection()
        if not selection:
            return

        chosen = self.suggestion_list.get(selection[0])
        current = self.artists_var.get().strip()
        if not current or "," not in current:
            self.artists_var.set(chosen)
            return

        parts = [p.strip() for p in current.split(",")]
        parts[-1] = chosen
        final = ", ".join(p for p in parts if p)
        self.artists_var.set(final)

    def normalize_artists(self, artists_text: str) -> str:
        artists = [a.strip() for a in artists_text.split(",") if a.strip()]
        return ", ".join(artists)

    def export_to_txt(self):
        if not self.songs:
            messagebox.showinfo("Export", "No songs available to export yet.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            title="Export Song Bank",
            initialfile="gospel_song_bank_export.txt",
        )
        if not filepath:
            return

        counts = {k: 0 for k in KEYS_12}
        for song in self.songs:
            counts[song.primary_key] += 1
            for k in song.modulated_keys:
                counts[k] += 1
        sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], KEYS_12.index(item[0])))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Gospel Song Bank Export\n")
            f.write("=" * 30 + "\n\n")

            f.write("Songs\n")
            f.write("-" * 30 + "\n")
            for i, song in enumerate(self.songs, start=1):
                mods = ", ".join(song.modulated_keys) if song.modulated_keys else "None"
                f.write(f"{i}. Song: {song.name}\n")
                f.write(f"   Artist(s): {song.artists}\n")
                f.write(f"   Primary Key: {song.primary_key}\n")
                f.write(f"   Modulated Key(s): {mods}\n\n")

            f.write("Key Frequency (High → Low)\n")
            f.write("-" * 30 + "\n")
            for key, count in sorted_counts:
                f.write(f"{key}: {count}\n")

        messagebox.showinfo("Export", f"Song bank exported successfully to:\n{filepath}")

    def save_data(self):
        data = [asdict(song) for song in self.songs]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.songs = [Song(**entry) for entry in data]
        except (json.JSONDecodeError, TypeError, ValueError):
            messagebox.showwarning("Data", "Could not read existing data file. Starting fresh.")
            self.songs = []


def main():
    root = tk.Tk()
    app = SongBankApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
