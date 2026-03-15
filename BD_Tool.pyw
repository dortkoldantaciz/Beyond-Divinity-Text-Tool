
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import sys
import os
import threading
import shutil

# Add lib directory to sys.path for tool imports
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(current_dir, "lib")
sys.path.insert(0, lib_dir)

try:
    import bd_text_tool
    import bd_gsm_tool
    import bd_extra_tools
except ImportError:
    pass

VERSION = "2"

HELP_TEXT = """
Beyond Divinity Translation Tool v2 - User Guide
=====================================================

Overview
--------
This tool batch-extracts and repacks Beyond Divinity's text files for
translation purposes. It scans the game directory and extracts all
translatable files into JSON while preserving the folder structure.

Supported File Types
---------------------
- text.cmp         -> UI / item text (Acts/Localizations)
- *.gsm            -> Dialog files (inside Acts)
- equipment.txt    -> Weapon, armor and accessory names (Localizations)
- hints.txt        -> Loading screen tips (Localizations)
- strings.txt      -> UI strings, stat descriptions, system messages (Common)
- books.txt        -> In-game book entries (Common)

Prerequisites
--------------
- Python 3.x
- The 'lib' folder containing 'bd_text_tool.py', 'bd_gsm_tool.py'
  and 'bd_extra_tools.py' must be in the same directory as this file.

Workflow
---------

1. Setup:
   - Select the game executable (div.exe).
   - Select the project folder (where your translation files will be stored).

2. Extract:
   - Click "START".
   - The tool scans Acts, Localizations, and Common directories.
   - All text files are extracted as JSON into the project folder.

3. Translate:
   - Edit the JSON files with any text editor.
   - Do NOT modify JSON structure or IDs.

4. Repack:
   - Select "REPACK" mode.
   - Choose the encoding mode
   - Click "START".

Encoding Modes
---------------
- ANSI (CP1254): Recommended for translations of languages with special characters such as Turkish and Polish.
  Uses single-byte encoding with positive item counts in text.cmp.
- Unicode: Original game format (UTF-16-LE for text.cmp).
  Uses widechar encoding with negative item counts in text.cmp.

Safety
-------
- ALWAYS back up 'Acts', 'Localizations' and 'Common' before repacking!

Troubleshooting
----------------
- "Undefined" text: Font or encoding issue. Try ANSI mode.
- Crash on load: CMP format mismatch. Use ANSI mode.

Note
-----
Starting quest descriptions and initial skill texts are hardcoded in the
game's New Game save templates (savegames/BD_ACT*_START/data.000). These
cannot be modified with this tool and require direct binary editing.
"""


class BDToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Beyond Divinity Translation Tool v{VERSION}")
        self.root.geometry("750x650")

        # Check tool availability
        tools_ok = True
        missing = []
        if 'bd_text_tool' not in sys.modules:
            missing.append('bd_text_tool.py')
            tools_ok = False
        if 'bd_gsm_tool' not in sys.modules:
            missing.append('bd_gsm_tool.py')
            tools_ok = False
        if 'bd_extra_tools' not in sys.modules:
            missing.append('bd_extra_tools.py')
            tools_ok = False

        if not tools_ok:
            messagebox.showerror("Critical Error",
                                 f"Missing modules: {', '.join(missing)}\n"
                                 f"Place them in the 'lib' folder.")
        self.tools_available = tools_ok

        self.setup_ui()

    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="User Guide", command=self.show_help)
        helpmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.root.config(menu=menubar)

        # Main Container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Directories Section
        lf_dirs = ttk.LabelFrame(main_frame, text="Directories", padding=10)
        lf_dirs.pack(fill=tk.X, pady=5)

        ttk.Label(lf_dirs, text="Game File (div.exe):").grid(row=0, column=0, sticky=tk.W)
        self.game_exe_var = tk.StringVar()
        ttk.Entry(lf_dirs, textvariable=self.game_exe_var, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(lf_dirs, text="Browse...", command=self.browse_game).grid(row=0, column=2)

        ttk.Label(lf_dirs, text="Project Workspace:").grid(row=1, column=0, sticky=tk.W)
        self.proj_dir_var = tk.StringVar()
        ttk.Entry(lf_dirs, textvariable=self.proj_dir_var, width=50).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(lf_dirs, text="Browse...", command=self.browse_project).grid(row=1, column=2)

        # 2. Mode Section
        lf_mode = ttk.LabelFrame(main_frame, text="Operation Mode", padding=10)
        lf_mode.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value="extract")
        ttk.Radiobutton(lf_mode, text="EXTRACT (Game -> JSON Workspace)",
                         variable=self.mode_var, value="extract").pack(anchor=tk.W)
        ttk.Radiobutton(lf_mode, text="REPACK (JSON Workspace -> Game)",
                         variable=self.mode_var, value="repack").pack(anchor=tk.W)

        # 3. Options Section
        lf_opts = ttk.LabelFrame(main_frame, text="Encoding & Output Format", padding=10)
        lf_opts.pack(fill=tk.X, pady=5)

        self.encoding_var = tk.StringVar(value="ansi")
        ttk.Radiobutton(lf_opts,
                         text="ANSI / CP1254 (Recommended for Turkish-Polish etc. - prevents crashes)",
                         variable=self.encoding_var, value="ansi").pack(anchor=tk.W)
        ttk.Radiobutton(lf_opts,
                         text="Unicode (Default / Original game format)",
                         variable=self.encoding_var, value="unicode").pack(anchor=tk.W)

        # 4. File Types Section
        lf_types = ttk.LabelFrame(main_frame, text="File Types", padding=10)
        lf_types.pack(fill=tk.X, pady=5)

        self.chk_cmp = tk.BooleanVar(value=True)
        self.chk_gsm = tk.BooleanVar(value=True)
        self.chk_equipment = tk.BooleanVar(value=True)
        self.chk_hints = tk.BooleanVar(value=True)
        self.chk_strings = tk.BooleanVar(value=True)
        self.chk_books = tk.BooleanVar(value=True)

        row1 = ttk.Frame(lf_types)
        row1.pack(fill=tk.X)
        ttk.Checkbutton(row1, text="text.cmp (UI/Items)", variable=self.chk_cmp).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row1, text="*.gsm (Dialogs)", variable=self.chk_gsm).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row1, text="equipment.txt", variable=self.chk_equipment).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(lf_types)
        row2.pack(fill=tk.X)
        ttk.Checkbutton(row2, text="hints.txt (Tips)", variable=self.chk_hints).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row2, text="strings.txt (UI Strings)", variable=self.chk_strings).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row2, text="books.txt (Books)", variable=self.chk_books).pack(side=tk.LEFT, padx=5)

        # 5. Action Section
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)

        self.btn_run = tk.Button(main_frame, text="START", command=self.start_process,
                                  font=("Arial", 11, "bold"), bg="#0078D7", fg="white", height=2,
                                  state="normal" if self.tools_available else "disabled")
        self.btn_run.pack(fill=tk.X, pady=5)

        # 6. Log Section
        self.log_widget = scrolledtext.ScrolledText(main_frame, height=10, state='disabled',
                                                     font=("Consolas", 9))
        self.log_widget.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log("Welcome. Select directories and mode to begin.")
        self.log(f"Dependency check: {'OK' if self.tools_available else 'MISSING TOOLS'}")

    # --- Helpers ---
    def log(self, msg):
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, msg + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state='disabled')

    def browse_game(self):
        f = filedialog.askopenfilename(filetypes=[("Game File", "div.exe"), ("All Files", "*.*")])
        if f:
            self.game_exe_var.set(f)

    def browse_project(self):
        d = filedialog.askdirectory()
        if d:
            self.proj_dir_var.set(d)

    def show_help(self):
        win = tk.Toplevel(self.root)
        win.title("User Guide")
        win.geometry("650x500")
        st = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        st.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        st.config(state='normal')
        st.insert(tk.END, HELP_TEXT)
        st.config(state='disabled')

    def show_about(self):
        messagebox.showinfo("About",
                            f"Beyond Divinity Translation Tool\n"
                            f"Version {VERSION}\n\n"
                            f"Author: dörtkoldantaciz")

    # --- Logic ---
    def start_process(self):
        if not self.tools_available:
            return

        game_exe = self.game_exe_var.get()
        proj_dir = self.proj_dir_var.get()
        mode = self.mode_var.get()
        encoding = self.encoding_var.get()

        if not game_exe or not os.path.exists(game_exe):
            messagebox.showerror("Error", "Select a valid 'div.exe' location.")
            return
        if not proj_dir or not os.path.exists(proj_dir):
            messagebox.showerror("Error", "Select a valid project directory.")
            return

        game_root = os.path.dirname(game_exe)

        if mode == "repack":
            if not messagebox.askyesno("Repack Confirmation",
                                       "WARNING: Repack will OVERWRITE files in the game directory.\n"
                                       "Make sure you have backups.\nContinue?"):
                return

        self.btn_run.config(state='disabled')
        self.log("-" * 40)
        self.log(f"Starting {mode.upper()}...")
        self.log(f"Game Root: {game_root}")
        self.log(f"Project: {proj_dir}")
        self.log(f"Encoding: {encoding}")

        threading.Thread(target=self.run_batch, args=(game_root, proj_dir, mode, encoding)).start()

    def run_batch(self, game_root, proj_dir, mode, encoding):
        try:
            ansi_mode = (encoding == "ansi")
            enc = 'cp1254' if ansi_mode else 'utf-8'

            tasks = []  # List of (source, dest, type)

            self.log("Scanning files...")

            # Scan directories: Acts, Localizations, Common
            scan_dirs = ["Acts", "Localizations", "Common"]

            if mode == "extract":
                for subd in scan_dirs:
                    full_scan_path = os.path.join(game_root, subd)
                    if not os.path.exists(full_scan_path):
                        self.log(f"Skipped directory: {subd}")
                        continue

                    for root, dirs, files in os.walk(full_scan_path):
                        for file in files:
                            full_src = os.path.join(root, file)
                            rel_path = os.path.relpath(full_src, game_root)

                            ftype = self._detect_file_type(file)
                            if ftype and self._is_type_enabled(ftype):
                                dest = os.path.join(proj_dir, rel_path + ".json")
                                tasks.append((full_src, dest, ftype))

            elif mode == "repack":
                for root, dirs, files in os.walk(proj_dir):
                    for file in files:
                        if file.endswith(".json"):
                            full_src = os.path.join(root, file)
                            rel_path_json = os.path.relpath(full_src, proj_dir)
                            clean_rel_path = rel_path_json[:-5]  # Strip .json

                            ftype = self._detect_file_type(os.path.basename(clean_rel_path))
                            if ftype and self._is_type_enabled(ftype):
                                dest = os.path.join(game_root, clean_rel_path)
                                tasks.append((full_src, dest, ftype))

            total = len(tasks)
            self.log(f"{total} files found.")

            count = 0
            errors = 0

            for src, dest, ftype in tasks:
                count += 1
                self.progress_var.set((count / total) * 100 if total > 0 else 0)

                try:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)

                    if mode == "extract":
                        self._extract_file(src, dest, ftype, ansi_mode, enc)
                    elif mode == "repack":
                        self._repack_file(src, dest, ftype, ansi_mode, enc)

                except Exception as e:
                    errors += 1
                    self.log(f"ERROR: {src} -> {e}")

            self.log(f"Done. Processed: {count}, Errors: {errors}")
            messagebox.showinfo("Complete", f"Batch operation finished.\nProcessed: {count}\nErrors: {errors}")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state='normal'))

    def _detect_file_type(self, filename):
        """Detect file type from filename."""
        lower = filename.lower()
        if lower == "text.cmp":
            return "cmp"
        if lower.endswith(".gsm"):
            return "gsm"
        if lower == "equipment.txt":
            return "equipment"
        if lower in ("hints.txt",):
            return "hints"
        if lower == "strings.txt":
            return "strings"
        if lower == "books.txt":
            return "books"
        return None

    def _is_type_enabled(self, ftype):
        """Check if file type is enabled via checkbox."""
        mapping = {
            "cmp": self.chk_cmp,
            "gsm": self.chk_gsm,
            "equipment": self.chk_equipment,
            "hints": self.chk_hints,
            "strings": self.chk_strings,
            "books": self.chk_books,
        }
        var = mapping.get(ftype)
        return var.get() if var else False

    def _extract_file(self, src, dest, ftype, ansi_mode, enc):
        """Extract a file based on its type."""
        if ftype == "cmp":
            wc = not ansi_mode  # ANSI = no widechar, Unicode = widechar
            bd_text_tool.extract_text_cmp(src, dest, widechar=wc, encoding=enc)
        elif ftype == "gsm":
            bd_gsm_tool.extract_gsm(src, dest, encoding=enc)
        elif ftype == "equipment":
            bd_extra_tools.extract_equipment(src, dest, encoding=enc)
        elif ftype == "hints":
            bd_extra_tools.extract_hints(src, dest, encoding=enc)
        elif ftype == "strings":
            bd_extra_tools.extract_strings(src, dest, encoding=enc)
        elif ftype == "books":
            bd_extra_tools.extract_books(src, dest, encoding=enc)

    def _repack_file(self, src, dest, ftype, ansi_mode, enc):
        """Repack a file based on its type."""
        if ftype == "cmp":
            wc = not ansi_mode
            m_val = 3 if ansi_mode else 1
            bd_text_tool.repack_text_cmp(src, dest, widechar=wc, mode=m_val, encoding=enc)
        elif ftype == "gsm":
            bd_gsm_tool.repack_gsm(src, dest, encoding=enc)
        elif ftype == "equipment":
            bd_extra_tools.repack_equipment(src, dest, encoding=enc)
        elif ftype == "hints":
            bd_extra_tools.repack_hints(src, dest, encoding=enc)
        elif ftype == "strings":
            bd_extra_tools.repack_strings(src, dest, encoding=enc)
        elif ftype == "books":
            bd_extra_tools.repack_books(src, dest, encoding=enc)


if __name__ == "__main__":
    root = tk.Tk()
    app = BDToolApp(root)
    root.mainloop()
