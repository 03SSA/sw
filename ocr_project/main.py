import tkinter as tk
from tkinter import messagebox

class MainApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OCR Integrated Study App")
        self.root.geometry("450x620")
        self.root.resizable(False, False)

        self.selected_region = None
        self.capture_path = None

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#4B4FA6", height=100)
        header.pack(fill="x")
        tk.Label(header, text="Main Hub", font=("Segoe UI", 18, "bold"), bg="#4B4FA6", fg="white").pack(pady=30)

        card = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#DDDDDD")
        card.pack(padx=30, pady=20, fill="x")

        self.status_var = tk.StringVar(value="Ready for Scanning")
        self.region_var = tk.StringVar(value="Selected Region: None")
        self.path_var = tk.StringVar(value="Capture Path: None")

        tk.Label(card, text="SYSTEM STATUS", font=("Segoe UI", 8, "bold"), bg="white", fg="#65676B").pack(pady=(15, 0), padx=20, anchor="w")
        tk.Label(card, textvariable=self.status_var, font=("Segoe UI", 12, "bold"), bg="white", fg="#1C1E21").pack(pady=(5, 10), padx=20, anchor="w")
        tk.Label(card, textvariable=self.region_var, font=("Segoe UI", 9), bg="white", fg="#8A8D91").pack(padx=20, anchor="w")
        tk.Label(card, textvariable=self.path_var, font=("Segoe UI", 8), bg="white", fg="#8A8D91", wraplength=350, justify="left").pack(pady=(5, 15), padx=20, anchor="w")

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "height": 2, "cursor": "hand2"}

        tk.Button(self.root, text="Open Region Selector", bg="#5E66F2", command=self.open_selector, **btn_style).pack(padx=30, fill="x", pady=5)
        tk.Button(self.root, text="Open Overlay", bg="#6B7FF2", command=self.open_overlay, **btn_style).pack(padx=30, fill="x", pady=5)
        tk.Button(self.root, text="Open Study List", bg="#99A6F2", command=self.open_study_list, **btn_style).pack(padx=30, fill="x", pady=5)
        tk.Button(self.root, text="Open Test UI", bg="#B3BDF2", command=self.open_test_ui, **btn_style).pack(padx=30, fill="x", pady=5)

    def _on_region_selected(self, region, capture_path=None) -> None:
        self.selected_region = region
        self.capture_path = capture_path
        self.status_var.set("Active: Region Loaded")
        self.region_var.set(f"Selected Region: {region}")
        self.path_var.set(f"Capture Path: {capture_path or 'None'}")

    def open_selector(self) -> None:
        try:
            from selector import open_selector_window
            open_selector_window(self.root, on_selected=self._on_region_selected)
        except ImportError:
            self._open_placeholder("Selector", "selector.py or open_selector_window is missing.")

    def open_overlay(self) -> None:
        try:
            from overlay import open_overlay_window
            payload = {
                "initial_text": "OCR result preview",
                "selected_region": self.selected_region,
                "capture_path": self.capture_path,
            }
            open_overlay_window(self.root, data=payload)
        except ImportError:
            self._open_placeholder("Overlay", "overlay.py or open_overlay_window is missing.")

    def open_study_list(self) -> None:
        try:
            from study_list import open_study_list_window
            open_study_list_window(self.root)
        except ImportError:
            self._open_placeholder("Study List", "study_list.py or open_study_list_window is missing.")

    def open_test_ui(self) -> None:
        try:
            from test_ui import open_test_window
            open_test_window(self.root)
        except ImportError:
            self._open_placeholder("Test UI", "test_ui.py or open_test_window is missing.")

    def _open_placeholder(self, title: str, message: str) -> None:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("380x180")
        win.resizable(False, False)

        tk.Label(win, text=title, font=("Segoe UI", 13, "bold")).pack(pady=(20, 10))
        tk.Label(win, text=message, font=("Segoe UI", 10), fg="#444444", wraplength=330).pack(pady=(0, 16))
        tk.Button(win, text="Close", command=win.destroy, width=12).pack()

def main() -> None:
    root = tk.Tk()
    MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
