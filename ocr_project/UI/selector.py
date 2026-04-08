import os
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import threading

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

try:
    import numpy as np
except Exception:
    np = None

try:
    from CORE.ocr_engine import get_ocr_engine
except ImportError:
    get_ocr_engine = None


class SelectorWindow:
    def __init__(self, parent: tk.Misc, on_selected=None) -> None:
        self.parent = parent
        self.on_selected = on_selected

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.preview_rect_id = None
        self.selected_region = None
        self.capture_path = None
        self.ocr_engine = get_ocr_engine() if get_ocr_engine else None
        self.last_capture_time = 0
        self.capture_interval = 0.5  # 0.5초 간격으로 캡처
        self.current_preview = None

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

        self.info_var = tk.StringVar(value="Drag to select. Real-time OCR: ON")
        tk.Label(self.hud, textvariable=self.info_var, fg="white", bg="#111111", anchor="w").pack(fill="x")

        # 실시간 OCR 미리보기 영역
        self.preview_frame = tk.Frame(self.hud, bg="#222222", width=400, height=60)
        self.preview_frame.pack(fill="x", pady=(8, 0))
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(
            self.preview_frame, 
            text="OCR Preview: Drag to select area...",
            fg="#888888",
            bg="#222222",
            anchor="w",
            justify="left",
            wraplength=380,
            font=("Consolas", 9)
        )
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)

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
        
        # 미리보기 사각형 삭제
        if self.preview_rect_id:
            self.canvas.delete(self.preview_rect_id)
            self.preview_rect_id = None

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
        
        # 실시간 캡처 및 OCR
        self._realtime_capture(event)

    def _realtime_capture(self, event: tk.Event) -> None:
        """마우스 드래그 중 실시간 캡처 및 OCR"""
        current_time = time.time()
        if current_time - self.last_capture_time < self.capture_interval:
            return
        
        # 선택 영역 계산
        left = min(self.start_x, event.x)
        top = min(self.start_y, event.y)
        right = max(self.start_x, event.x)
        bottom = max(self.start_y, event.y)
        
        width = right - left
        height = bottom - top
        
        # 너무 작으면 스킵
        if width < 20 or height < 20:
            return
        
        self.last_capture_time = current_time
        
        # 캡처 실행 (백그라운드)
        try:
            if ImageGrab:
                img = ImageGrab.grab(bbox=(left, top, right, bottom))
                
                # OCR 실행 (별도 스레드에서)
                if self.ocr_engine:
                    # 이미지 저장 없이 메모리에서 OCR
                    self._run_realtime_ocr(img)
                    
        except Exception as e:
            pass  # 캡처 실패는 무시

    def _run_realtime_ocr(self, img) -> None:
        """실시간 OCR 처리 (별도 스레드)"""
        def ocr_worker():
            try:
                # PIL 이미지를 임시로 저장하지 않고 직접 OCR
                # EasyOCR은 numpy array를 받을 수 있음
                import numpy as np
                img_array = np.array(img)
                
                result = self.ocr_engine.read_text_simple(img_array)
                
                # UI 업데이트 (메인 스레드에서)
                self.win.after(0, lambda: self._update_preview(result))
                
            except Exception as e:
                pass
        
        # 별도 스레드에서 OCR 실행
        thread = threading.Thread(target=ocr_worker, daemon=True)
        thread.start()

    def _update_preview(self, ocr_result) -> None:
        """미리보기 영역 업데이트"""
        if ocr_result:
            text = '\n'.join(ocr_result[:5])  # 최대 5개 텍스트만
            if len('\n'.join(ocr_result)) > 200:
                text += "\n..."
            self.preview_label.config(text=f"OCR Result:\n{text}", fg="#00ff00")
        else:
            self.preview_label.config(text="No text detected", fg="#ff6600")

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
        self.info_var.set(f"Selected: ({left},{top})-({right},{bottom})  Size: {w}x{h}")

    def _reset_selection(self) -> None:
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        if self.preview_rect_id:
            self.canvas.delete(self.preview_rect_id)
            self.preview_rect_id = None
        self.selected_region = None
        self.capture_path = None
        self.preview_label.config(text="OCR Preview: Drag to select area...", fg="#888888")
        self.info_var.set("Drag to select. Real-time OCR: ON")

    def _capture_and_finish(self) -> None:
        if not self.selected_region:
            messagebox.showwarning("Notice", "Please select an area first.")
            return

        if ImageGrab is None:
            messagebox.showwarning("Notice", "Pillow is not installed. Region is saved without image capture.")
            self._emit_callback_and_close()
            return

        left, top, right, bottom = self.selected_region
        width = right - left
        height = bottom - top
        
        if width < 10 or height < 10:
            messagebox.showwarning("Notice", "Selection is too small. Minimum 10x10 pixels required.")
            return

        self.info_var.set(f"Capturing... {width}x{height}")
        self.win.update()

        try:
            # 캡처 전 화면 업데이트
            self.win.update_idletasks()
            
            # 이미지 캡처
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # 캡처 결과 확인
            img_width, img_height = img.size
            self.info_var.set(f"Captured: {img_width}x{img_height} pixels")
            self.win.update()
            
            # 저장
            out_dir = Path(__file__).resolve().parent / "captures"
            out_dir.mkdir(parents=True, exist_ok=True)
            name = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = out_dir / name
            img.save(path)
            self.capture_path = str(path)
            
            self.info_var.set(f"Saved: {name}")
            self.win.update()
            
        except Exception as exc:
            messagebox.showerror("Error", f"Capture failed.\n{exc}")
            return

        # Run OCR
        ocr_text = []
        if self.ocr_engine and self.capture_path:
            self.info_var.set("Processing OCR...")
            self.win.update()
            try:
                ocr_text = self.ocr_engine.read_text_simple(self.capture_path)
                if ocr_text:
                    self.info_var.set(f"OCR: {len(ocr_text)} text(s) found")
                else:
                    self.info_var.set("No text detected")
            except Exception as e:
                self.info_var.set(f"OCR failed: {e}")

        self._emit_callback_and_close(ocr_text)

    def _emit_callback_and_close(self, ocr_text=None) -> None:
        if callable(self.on_selected):
            try:
                self.on_selected(self.selected_region, self.capture_path, ocr_text or [])
            except TypeError:
                self.on_selected(self.selected_region, self.capture_path)
        self.win.destroy()


def open_selector_window(parent: tk.Misc, on_selected=None) -> SelectorWindow:
    return SelectorWindow(parent, on_selected=on_selected)
