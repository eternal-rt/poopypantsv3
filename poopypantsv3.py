import tkinter as tk
import random
import math
import ctypes
import os
import time


GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000


def primary_screen_size():
    u = ctypes.windll.user32
    return u.GetSystemMetrics(0), u.GetSystemMetrics(1)


def hide_from_taskbar(root):
    root.update_idletasks()
    hwnd = root.winfo_id()
    exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    exstyle = (exstyle | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle)


def load_photo(path: str):
    if not os.path.exists(path):
        return None
    try:
        return tk.PhotoImage(file=path)
    except Exception:
        return None


def scale_wipe_cursor(img: tk.PhotoImage):
    if img is None:
        return None
    try:
        return img.subsample(2, 2)
    except Exception:
        return img


class PoopyPantsV3Flow:
    def __init__(self):
        self.overlay_root = tk.Tk()
        self.overlay = OverlayWipe(self.overlay_root, on_done=self.on_overlay_done)
        self.overlay_root.after(60, lambda: hide_from_taskbar(self.overlay_root))
        self.overlay.start()
        self.overlay_root.mainloop()

    def on_overlay_done(self):
        self.overlay_root.after(200, self.transition_to_executor)

    def transition_to_executor(self):
        try:
            self.overlay_root.destroy()
        except Exception:
            pass
        self.create_executor_window()

    def create_executor_window(self):
        root = tk.Tk()
        root.title("Poopy Pants Executor v3")
        root.geometry("920x560")
        root.minsize(700, 420)
        root.configure(bg="#5a5a5a")

        topbar = tk.Frame(root, bg="#2f2f2f", height=46)
        topbar.pack(side="top", fill="x")

        title = tk.Label(
            topbar,
            text="Poopy Pants Executor v3",
            bg="#2f2f2f",
            fg="white",
            font=("Segoe UI", 14, "bold")
        )
        title.place(x=14, y=10)

        body = tk.Frame(root, bg="#5a5a5a")
        body.pack(fill="both", expand=True)

        root.mainloop()


class OverlayWipe:
    def __init__(self, root: tk.Tk, on_done):
        self.root = root
        self.on_done_cb = on_done

        self.W, self.H = primary_screen_size()

        self.root.geometry(f"{self.W}x{self.H}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.transparent_key = "#ff00ff"
        self.root.configure(bg=self.transparent_key)
        self.root.wm_attributes("-transparentcolor", self.transparent_key)

        self.canvas = tk.Canvas(
            self.root,
            width=self.W,
            height=self.H,
            bg=self.transparent_key,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.splatter_ids = set()
        self.brush_radius = 44
        self.brush_preview_id = None

        self.finished = False

        self.wipe_active = False
        self.wipe_uses_left = 0
        self.cursor_wipe_id = None
        self.cursor_shadow_id = None

        self.bag_item_id = None
        self.bag_tag = "wipe_bag"

        self._last_mouse = (self.W // 2, self.H // 2)
        self._last_wipe_time = 0.0

        self.wipes_bag_img = None
        self.wipe_cursor_img_raw = None
        self.wipe_cursor_img = None

        self.title_ids = []

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("r", lambda e: self.reset())
        self.root.bind("-", lambda e: self.adjust_brush(-3))
        self.root.bind("=", lambda e: self.adjust_brush(3))
        self.root.bind("+", lambda e: self.adjust_brush(3))

    def start(self):
        self.load_images()
        self.draw_center_text_under_splatter()
        self.spawn_splatter_huge_optimized()
        self.draw_wipe_bag_static()
        self.raise_layers()

    def load_images(self):
        self.wipes_bag_img = load_photo("wipes.png")
        self.wipe_cursor_img_raw = load_photo("wipes2.png")
        self.wipe_cursor_img = scale_wipe_cursor(self.wipe_cursor_img_raw)

    def adjust_brush(self, delta):
        self.brush_radius = max(14, min(160, self.brush_radius + delta))

    def reset(self):
        self.canvas.delete("all")
        self.splatter_ids.clear()
        self.brush_preview_id = None
        self.finished = False

        self.wipe_active = False
        self.wipe_uses_left = 0
        self._last_wipe_time = 0.0
        self.delete_cursor_images()

        self.bag_item_id = None
        self.title_ids = []

        self.root.configure(cursor="")
        self.start()

    def raise_layers(self):
        for tid in self.title_ids:
            self.canvas.tag_lower(tid)

        self.canvas.tag_raise("splatter")
        self.canvas.tag_raise("wipe_ui")

        if self.brush_preview_id is not None:
            self.canvas.tag_raise(self.brush_preview_id)

        if self.cursor_shadow_id is not None:
            self.canvas.tag_raise(self.cursor_shadow_id)
        if self.cursor_wipe_id is not None:
            self.canvas.tag_raise(self.cursor_wipe_id)

    def draw_center_text_under_splatter(self):
        cx = self.W // 2
        cy = self.H // 2

        main = "Poopy Pants Executor"
        v3 = "V3"

        main_font = ("Segoe UI", 44, "bold")
        v3_font = ("Segoe UI", 24, "bold")

        offsets = [(dx, dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) if not (dx == 0 and dy == 0)]

        main_outlines = [
            self.canvas.create_text(cx + dx, cy + dy, text=main, fill="black", font=main_font, tags=("title",))
            for dx, dy in offsets
        ]
        main_id = self.canvas.create_text(cx, cy, text=main, fill="white", font=main_font, tags=("title",))

        self.root.update_idletasks()
        bbox = self.canvas.bbox(main_id) or (cx - 200, cy - 30, cx + 200, cy + 30)
        right_edge = bbox[2]
        padding = 14

        v3_x = right_edge + padding
        v3_y = cy + 10

        v3_outlines = [
            self.canvas.create_text(v3_x + dx, v3_y + dy, text=v3, fill="black", font=v3_font, tags=("title",))
            for dx, dy in offsets
        ]
        v3_id = self.canvas.create_text(v3_x, v3_y, text=v3, fill="white", font=v3_font, tags=("title",))

        self.title_ids = main_outlines + [main_id] + v3_outlines + [v3_id]
        for tid in self.title_ids:
            self.canvas.tag_lower(tid)

    def draw_wipe_bag_static(self):
        x = 24
        y = self.H - 24

        if self.wipes_bag_img is not None:
            self.bag_item_id = self.canvas.create_image(x, y, anchor="sw", image=self.wipes_bag_img, tags=("wipe_ui", self.bag_tag))
        else:
            self.bag_item_id = self.canvas.create_rectangle(x, y - 70, x + 140, y, fill="#d8d8d8", outline="#111111", width=2, tags=("wipe_ui", self.bag_tag))
            self.canvas.create_text(x + 70, y - 35, text="WIPES", fill="#111111", font=("Segoe UI", 14, "bold"), tags=("wipe_ui", self.bag_tag))

        self.canvas.tag_bind(self.bag_tag, "<Button-1>", self.on_bag_click)

    def on_bag_click(self, _event=None):
        if self.finished:
            return
        self.pickup_new_wipe()

    def pickup_new_wipe(self):
        cursor_img = self.wipe_cursor_img if self.wipe_cursor_img is not None else self.wipe_cursor_img_raw
        if cursor_img is None:
            return

        self.wipe_active = True
        self.wipe_uses_left = 32
        self._last_wipe_time = 0.0

        self.root.configure(cursor="none")
        self.delete_cursor_images()

        self.cursor_shadow_id = self.canvas.create_image(
            self._last_mouse[0] + 3,
            self._last_mouse[1] + 3,
            anchor="center",
            image=cursor_img,
            tags=("wipe_ui",)
        )
        self.cursor_wipe_id = self.canvas.create_image(
            self._last_mouse[0],
            self._last_mouse[1],
            anchor="center",
            image=cursor_img,
            tags=("wipe_ui",)
        )
        self.canvas.tag_lower(self.cursor_shadow_id, self.cursor_wipe_id)
        self.raise_layers()

    def delete_cursor_images(self):
        if self.cursor_wipe_id is not None:
            try:
                self.canvas.delete(self.cursor_wipe_id)
            except Exception:
                pass
        self.cursor_wipe_id = None

        if self.cursor_shadow_id is not None:
            try:
                self.canvas.delete(self.cursor_shadow_id)
            except Exception:
                pass
        self.cursor_shadow_id = None

    def drop_wipe(self):
        self.wipe_active = False
        self.wipe_uses_left = 0
        self.root.configure(cursor="")
        self.delete_cursor_images()

    def on_mouse_move(self, event):
        self._last_mouse = (event.x, event.y)

        if self.wipe_active:
            if self.cursor_wipe_id is not None:
                self.canvas.coords(self.cursor_wipe_id, event.x, event.y)
            if self.cursor_shadow_id is not None:
                self.canvas.coords(self.cursor_shadow_id, event.x + 3, event.y + 3)

        self.draw_brush_preview(event.x, event.y)

    def on_left_press(self, event):
        self._last_mouse = (event.x, event.y)
        if self.finished or not self.wipe_active:
            return
        self.wipe_at(event.x, event.y)

    def on_drag(self, event):
        self._last_mouse = (event.x, event.y)
        if self.finished or not self.wipe_active:
            return
        self.wipe_at(event.x, event.y)

    def draw_brush_preview(self, x, y):
        r = self.brush_radius
        if self.brush_preview_id is None:
            self.brush_preview_id = self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="#bbbbbb", width=2)
        else:
            self.canvas.coords(self.brush_preview_id, x - r, y - r, x + r, y + r)

        self.canvas.tag_raise(self.brush_preview_id)
        if self.cursor_shadow_id is not None:
            self.canvas.tag_raise(self.cursor_shadow_id)
        if self.cursor_wipe_id is not None:
            self.canvas.tag_raise(self.cursor_wipe_id)

    def wipe_at(self, x, y):
        now = time.perf_counter()
        if (now - self._last_wipe_time) < 0.016:
            return
        self._last_wipe_time = now

        r = self.brush_radius
        hits = self.canvas.find_overlapping(x - r, y - r, x + r, y + r)

        removed_any = False
        for item in hits:
            if item in self.splatter_ids:
                self.canvas.delete(item)
                self.splatter_ids.discard(item)
                removed_any = True

        if removed_any:
            self.wipe_uses_left -= 1
            if self.wipe_uses_left <= 0:
                self.drop_wipe()

        if not self.splatter_ids:
            self.finished = True
            if callable(self.on_done_cb):
                self.on_done_cb()
        else:
            self.raise_layers()

    def spawn_splatter_huge_optimized(self):
        cx = int(self.W * random.uniform(0.42, 0.62))
        cy = int(self.H * random.uniform(0.35, 0.65))

        base = min(self.W, self.H) * 0.36
        self.make_puddle(cx, cy, base_radius=base, density_scale=2.2)

        for _ in range(18):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(140, 620)
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist
            self.make_droplet(x, y, size=random.uniform(12, 34), density=18)

        for _ in range(380):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(0, 860)
            x = cx + math.cos(ang) * dist + random.uniform(-55, 55)
            y = cy + math.sin(ang) * dist + random.uniform(-55, 55)
            rr = random.uniform(2, 10)
            self.make_blob(x, y, rr)

    def make_puddle(self, cx, cy, base_radius, density_scale=1.0):
        for i in range(7):
            layer_r = base_radius * (1 - i * 0.10)
            density = int(190 * density_scale * (1 - i * 0.10))
            for _ in range(density):
                ang = random.uniform(0, math.tau)
                dist = random.uniform(0, layer_r)
                x = cx + math.cos(ang) * dist + random.uniform(-12, 12)
                y = cy + math.sin(ang) * dist + random.uniform(-12, 12)
                rr = random.uniform(6, 19) * (1 - i * 0.05)
                self.make_blob(x, y, rr, darker=(i < 3))

    def make_droplet(self, x, y, size=12, density=16):
        for _ in range(density):
            ox = random.uniform(-size, size)
            oy = random.uniform(-size, size)
            rr = random.uniform(2, size * 0.62)
            self.make_blob(x + ox, y + oy, rr, darker=random.random() < 0.42)

    def make_blob(self, x, y, rr, darker=False):
        colors = ["#2a1609", "#2e180a", "#3f220f", "#4b2a12", "#5a2f14"] if darker else ["#5f3416", "#6b3a18", "#7a421c", "#8a4b20", "#9a5423"]
        fill = random.choice(colors)
        item = self.canvas.create_oval(
            x - rr, y - rr, x + rr, y + rr,
            fill=fill,
            outline="",
            tags=("splatter",)
        )
        self.splatter_ids.add(item)


if __name__ == "__main__":
    PoopyPantsV3Flow()
