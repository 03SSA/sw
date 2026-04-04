import os
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None


class SelectorWindow:
    def __init__(self, parent: tk.Misc, on_selected=None) -> None:
        self.parent = parent
        self.on_selected = on_selected

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.selected_region = None
        self.capture_path = None

        self.win = tk.Toplevel(parent)
        self.win.title("Region Selector")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.28)

        width = self.win.winfo_screenwidth()
        height = self.win.winfo_screenheight()
        self.win.geometry(f"{width}x{height}+0+0")

        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self) -> None:
        self.canvas = tk.Canvas(self.win, bg="black", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        self.hud = tk.Frame(self.win, bg="#111111", padx=10, pady=8)
        self.hud.place(x=20, y=20)

        self.info_var = tk.StringVar(value="Drag to select a region. Enter: capture / Esc: cancel")
        tk.Label(self.hud, textvariable=self.info_var, fg="white", bg="#111111", anchor="w").pack(fill="x")

        row = tk.Frame(self.hud, bg="#111111")
        row.pack(fill="x", pady=(8, 0))

        tk.Button(row, text="Capture", width=10, command=self._capture_and_finish).pack(side="left")
        tk.Button(row, text="Reset", width=10, command=self._reset_selection).pack(side="left", padx=(6, 0))
        tk.Button(row, text="Cancel", width=10, command=self.win.destroy).pack(side="left", padx=(6, 0))

    def _bind_shortcuts(self) -> None:
        self.win.bind("<Return>", lambda _e: self._capture_and_finish())
        self.win.bind("<Escape>", lambda _e: self.win.destroy())

    def _on_mouse_down(self, event: tk.Event) -> None:
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="#2ed3ff",
            width=2,
            dash=(4, 3),
        )

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if not self.rect_id:
            return
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def _on_mouse_up(self, event: tk.Event) -> None:
        if not self.rect_id:
            return
        left = min(self.start_x, event.x)
        top = min(self.start_y, event.y)
        right = max(self.start_x, event.x)
        bottom = max(self.start_y, event.y)
        self.selected_region = (left, top, right, bottom)
        w = right - left
        h = bottom - top
        self.info_var.set(f"Selected: {self.selected_region}  Size: {w}x{h}")

    def _reset_selection(self) -> None:
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        self.selected_region = None
        self.capture_path = None
        self.info_var.set("Drag to select a region. Enter: capture / Esc: cancel")

    def _capture_and_finish(self) -> None:
        if not self.selected_region:
            messagebox.showwarning("Notice", "Please select an area first.")
            return

        if ImageGrab is None:
            messagebox.showwarning("Notice", "Pillow is not installed. Region is saved without image capture.")
            self._emit_callback_and_close()
            return

        left, top, right, bottom = self.selected_region
        if right - left < 2 or bottom - top < 2:
            messagebox.showwarning("Notice", "Selection is too small.")
            return

        try:
            self.win.withdraw()
            self.win.update_idletasks()
            img = ImageGrab.grab(bbox=(left, top, right, bottom))

            out_dir = Path(__file__).resolve().parent / "captures"
            out_dir.mkdir(parents=True, exist_ok=True)
            name = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = out_dir / name
            img.save(path)
            self.capture_path = str(path)
        except Exception as exc:
            self.win.deiconify()
            messagebox.showerror("Error", f"Capture failed.\n{exc}")
            return

        self._emit_callback_and_close()

    def _emit_callback_and_close(self) -> None:
        if callable(self.on_selected):
            try:
                self.on_selected(self.selected_region, self.capture_path)
            except TypeError:
                self.on_selected(self.selected_region)
        self.win.destroy()


def open_selector_window(parent: tk.Misc, on_selected=None) -> SelectorWindow:
    return SelectorWindow(parent, on_selected=on_selected)
