import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from PIL import Image, ImageTk
import os
import random
import threading

import config
import filters


# =========================
# CONSTANTS
# =========================

STRENGTH_STEPS = {
    1: 0.2,
    2: 0.4,
    3: 0.6,
    4: 0.8,
    5: 1.0,
}


# =========================
# HELPERS
# =========================

def lerp(a, b, t):
    return a + (b - a) * t


def nonlinear(t, gamma):
    return t ** gamma


# =========================
# GRID GENERATION
# =========================

def generate_grid(seed_img, filter_a_name, filter_b_name, a_scale, b_scale):
    grid = []

    fa = filters.FILTERS[filter_a_name]
    fb = filters.FILTERS[filter_b_name]

    a_fn = fa["fn"]
    b_fn = fb["fn"]

    a_min, a_max = fa["range"]
    b_min, b_max = fb["range"]

    a_neutral = fa["neutral"]
    b_neutral = fb["neutral"]

    a_max = a_neutral + (a_max - a_neutral) * a_scale
    b_max = b_neutral + (b_max - b_neutral) * b_scale

    for y in range(config.GRID_HEIGHT):
        row = []

        ty = y / (config.GRID_HEIGHT - 1)
        if config.USE_NONLINEAR:
            ty = nonlinear(ty, config.NONLINEAR_GAMMA)

        b_val = lerp(b_neutral, b_max, ty)

        for x in range(config.GRID_WIDTH):
            tx = x / (config.GRID_WIDTH - 1)
            if config.USE_NONLINEAR:
                tx = nonlinear(tx, config.NONLINEAR_GAMMA)

            a_val = lerp(a_neutral, a_max, tx)

            img = seed_img
            img = a_fn(img, a_val)
            img = b_fn(img, b_val)

            row.append(img)

        grid.append(row)

    return grid


# =========================
# MAIN APP
# =========================

class KPTExplorer:
    def __init__(self, root, seed_img):
        self.root = root
        self.root.title("KPT Convolver – Tiny Revival")

        self.is_rendering = False

        # ---- IMAGE STATE ----
        self.current_img = seed_img.convert("RGB")
        self.original_img = self.current_img.copy()

        # ---- FILTER STATE ----
        filter_names = list(filters.FILTERS.keys())

        self.filter_a_var = tk.StringVar(value=filter_names[0])
        self.filter_b_var = tk.StringVar(
            value=filter_names[1] if len(filter_names) > 1 else filter_names[0]
        )

        self.a_strength = 1.0
        self.b_strength = 1.0

        # =========================
        # TOP BAR
        # =========================

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        self.controls = []

        def ctl(widget):
            self.controls.append(widget)
            return widget

        ctl(ttk.Button(top, text="Load", command=self.load_image)).pack(side="left", padx=4)
        ctl(ttk.Button(top, text="Save", command=self.save_image)).pack(side="left", padx=4)
        ctl(ttk.Button(top, text="Reset", command=self.reset_image)).pack(side="left", padx=4)
        ctl(ttk.Button(top, text="Randomize", command=self.randomize)).pack(side="left", padx=12)

        ttk.Label(top, text="Filter A").pack(side="left", padx=(20, 4))
        self.filter_a_combo = ctl(
            ttk.Combobox(
                top,
                textvariable=self.filter_a_var,
                values=filter_names,
                state="readonly",
                width=18
            )
        )
        self.filter_a_combo.pack(side="left")
        self.filter_a_combo.bind("<<ComboboxSelected>>", lambda e: self.render_grid())

        self.a_slider = ctl(ttk.Scale(top, from_=1, to=5, length=100))
        self.a_slider.set(5)
        self.a_slider.pack(side="left", padx=4)
        self.a_slider.bind("<ButtonRelease-1>", self.on_strength_release)

        ttk.Label(top, text="Filter B").pack(side="left", padx=(12, 4))
        self.filter_b_combo = ctl(
            ttk.Combobox(
                top,
                textvariable=self.filter_b_var,
                values=filter_names,
                state="readonly",
                width=18
            )
        )
        self.filter_b_combo.pack(side="left")
        self.filter_b_combo.bind("<<ComboboxSelected>>", lambda e: self.render_grid())

        self.b_slider = ctl(ttk.Scale(top, from_=1, to=5, length=100))
        self.b_slider.set(5)
        self.b_slider.pack(side="left", padx=4)
        self.b_slider.bind("<ButtonRelease-1>", self.on_strength_release)

        # =========================
        # PREVIEW
        # =========================

        self.preview_label = tk.Label(
            root,
            bd=0,
            relief="solid"
        )
        self.preview_label.pack(pady=6)

        # =========================
        # GRID
        # =========================

        self.grid_frame = ttk.Frame(root, padding=10)
        self.grid_frame.pack()

        # =========================
        # PROGRESSBAR OVERLAY
        # =========================

        self.loader = ttk.Progressbar(
            root,
            mode="determinate",
            bootstyle="info striped",
            length=320
        )

        self.update_preview()
        self.render_grid()

    # =========================
    # SPINNER + STATE
    # =========================

    def show_spinner(self):
        self.is_rendering = True
        for c in self.controls:
            c.configure(state="disabled")

        self.loader.place(relx=0.5, rely=0.5, anchor="center")
        self.loader.start(10)

    def hide_spinner(self):
        self.loader.stop()
        self.loader.place_forget()

        for c in self.controls:
            c.configure(state="normal")

        self.is_rendering = False


    # =========================
    # UI ACTIONS
    # =========================

    def load_image(self):
        if self.is_rendering:
            return

        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not path:
            return

        img = Image.open(path).convert("RGB")
        self.current_img = img
        self.original_img = img.copy()

        self.update_preview()
        self.render_grid()

    def save_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        if not path:
            return

        self.current_img.save(path)

    def reset_image(self):
        if self.is_rendering:
            return
        self.current_img = self.original_img.copy()
        self.update_preview()
        self.render_grid()

    def update_preview(self):
        img = self.current_img.copy()
        img.thumbnail((config.THUMB_SIZE * config.GRID_WIDTH, 350))
        tk_img = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=tk_img)
        self.preview_label.image = tk_img

    # =========================
    # GRID (THREADED)
    # =========================

    def render_grid(self):
        if self.is_rendering:
            return

        self.show_spinner()

        threading.Thread(
            target=self._render_grid_worker,
            daemon=True
        ).start()

    def _render_grid_worker(self):
        grid = generate_grid(
            self.current_img,
            self.filter_a_var.get(),
            self.filter_b_var.get(),
            self.a_strength,
            self.b_strength
        )
        self.root.after(0, lambda: self._populate_grid(grid))

    def _populate_grid(self, grid):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        for y, row in enumerate(grid):
            for x, img in enumerate(row):
                thumb = img.resize(
                    (config.THUMB_SIZE, config.THUMB_SIZE),
                    Image.LANCZOS
                )
                tk_img = ImageTk.PhotoImage(thumb)

                lbl = tk.Label(
                    self.grid_frame,
                    image=tk_img,
                    bd=0,
                    relief="solid",
                    cursor="hand2"
                )
                lbl.image = tk_img
                lbl.grid(row=y, column=x, padx=2, pady=2)

                lbl.bind("<Button-1>", lambda e, im=img: self.select(im))

        self.hide_spinner()

    def select(self, img):
        if self.is_rendering:
            return
        self.current_img = img
        self.update_preview()
        self.render_grid()

    # =========================
    # CONTROLS
    # =========================

    def on_strength_release(self, event=None):
        if self.is_rendering:
            return

        a_idx = int(round(self.a_slider.get()))
        b_idx = int(round(self.b_slider.get()))

        self.a_strength = STRENGTH_STEPS[a_idx]
        self.b_strength = STRENGTH_STEPS[b_idx]

        self.render_grid()

    def randomize(self):
        if self.is_rendering:
            return

        names = list(filters.FILTERS.keys())

        self.filter_a_var.set(random.choice(names))
        self.filter_b_var.set(random.choice(names))

        self.a_slider.set(random.randint(1, 5))
        self.b_slider.set(random.randint(1, 5))

        self.on_strength_release()


# =========================
# BOOTSTRAP
# =========================

def main():
    root = ttk.Window(themename="darkly")

    if os.path.exists(config.DEFAULT_IMAGE_PATH):
        img = Image.open(config.DEFAULT_IMAGE_PATH)
    else:
        path = filedialog.askopenfilename(
            title="Select seed image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not path:
            return
        img = Image.open(path)

    KPTExplorer(root, img)
    root.mainloop()


if __name__ == "__main__":
    main()
