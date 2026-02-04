import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import config
import filters
import os


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

    # 1️ Look up filter metadata
    fa = filters.FILTERS[filter_a_name]
    fb = filters.FILTERS[filter_b_name]

    a_fn = fa["fn"]
    b_fn = fb["fn"]

    a_min, a_max = fa["range"]
    b_min, b_max = fb["range"]

    a_neutral = fa["neutral"]
    b_neutral = fb["neutral"]

    # 2️ Apply slider scaling to MAX ONLY
    a_max = a_neutral + (a_max - a_neutral) * a_scale
    b_max = b_neutral + (b_max - b_neutral) * b_scale

    for y in range(config.GRID_HEIGHT):
        row = []

        ty = y / (config.GRID_HEIGHT - 1)
        if config.USE_NONLINEAR:
            ty = nonlinear(ty, config.NONLINEAR_GAMMA)

        # THIS is where b_val is computed
        b_val = lerp(b_neutral, b_max, ty)

        for x in range(config.GRID_WIDTH):
            tx = x / (config.GRID_WIDTH - 1)
            if config.USE_NONLINEAR:
                tx = nonlinear(tx, config.NONLINEAR_GAMMA)

            # THIS is where your snippet lives
            a_val = lerp(a_neutral, a_max, tx)

            img = seed_img.copy()
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

        self.original_img = seed_img.convert("RGB")
        self.current_img = self.original_img

        self.filter_a_var = tk.StringVar(value=list(filters.FILTERS.keys())[0])
        self.filter_b_var = tk.StringVar(value=list(filters.FILTERS.keys())[0])

        self.filter_a_name = self.filter_a_var.get()
        self.filter_b_name = self.filter_b_var.get()

        self.a_strength = 1.0
        self.b_strength = 1.0

        # ---- TOP BAR ----
        top = tk.Frame(root)
        top.pack(padx=10, pady=5, fill="x")

        tk.Button(top, text="Load", command=self.load_image).pack(side="left", padx=5)
        tk.Button(top, text="Save", command=self.save_image).pack(side="left", padx=5)

        filter_names = list(filters.FILTERS.keys())

        # ---- FILTER DROPDOWNS ----
        self.filter_a_var = tk.StringVar(value=filter_names[0])
        self.filter_b_var = tk.StringVar(value=filter_names[1] if len(filter_names) > 1 else filter_names[0])

        tk.Label(top, text="Filter A").pack(side="left", padx=(20, 5))
        tk.OptionMenu(
            top,
            self.filter_a_var,
            *filter_names,
            command=self.on_filter_change
        ).pack(side="left")

        self.a_slider = tk.Scale(
            top,
            from_=1,
            to=5,
            orient="horizontal",
            showvalue=False,
            command=self.on_strength_change,
            length=100
        )
        self.a_slider.set(5)
        self.a_slider.pack(side="left", padx=5)

        tk.Label(top, text="Filter B").pack(side="left", padx=(10, 5))
        tk.OptionMenu(
            top,
            self.filter_b_var,
            *filter_names,
            command=self.on_filter_change
        ).pack(side="left")

        self.b_slider = tk.Scale(
            top,
            from_=1,
            to=5,
            orient="horizontal",
            showvalue=False,
            command=self.on_strength_change,
            length=100
        )
        self.b_slider.set(5)
        self.b_slider.pack(side="left", padx=5)

        # ---- PREVIEW ----
        self.preview_label = tk.Label(root)
        self.preview_label.pack(padx=10, pady=5)

        # ---- GRID ----
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(padx=10, pady=10)

        self.update_preview()
        self.render_grid()

    # =========================
    # FILTER HANDLING
    # =========================

    def get_filter_name(self, fn):
        for name, f in filters.FILTERS.items():
            if f == fn:
                return name
        return list(filters.FILTERS.keys())[0]

    def on_filter_change(self, _=None):
        self.filter_a_name = self.filter_a_var.get()
        self.filter_b_name = self.filter_b_var.get()
        self.render_grid()


    def on_strength_change(self, _=None):
        self.a_strength = STRENGTH_STEPS[self.a_slider.get()]
        self.b_strength = STRENGTH_STEPS[self.b_slider.get()]
        self.render_grid()

    # =========================
    # UI ACTIONS
    # =========================

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not path:
            return

        img = Image.open(path)
        self.original_img = img.convert("RGB")
        self.current_img = self.original_img

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

    def update_preview(self):
        img = self.original_img.copy()
        img.thumbnail((config.THUMB_SIZE * config.GRID_WIDTH, 300))
        tk_img = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=tk_img)
        self.preview_label.image = tk_img

    # =========================
    # GRID
    # =========================

    def render_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        grid = generate_grid(
            self.current_img,
            self.filter_a_var.get(),
            self.filter_b_var.get(),
            self.a_strength,
            self.b_strength
        )

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
                    bd=1,
                    relief="solid",
                    cursor="hand2"
                )
                lbl.image = tk_img
                lbl.grid(row=y, column=x, padx=2, pady=2)

                lbl.bind("<Button-1>", lambda e, im=img: self.select(im))

    def select(self, img):
        self.current_img = img
        self.render_grid()


# =========================
# BOOTSTRAP
# =========================

def main():
    root = tk.Tk()

    img = None

    if os.path.exists(config.DEFAULT_IMAGE_PATH):
        try:
            img = Image.open(config.DEFAULT_IMAGE_PATH)
        except Exception as e:
            print(f"Failed to load default image: {e}")

    if img is None:
        path = filedialog.askopenfilename(
            title="Select seed image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        img = Image.open(path)

    KPTExplorer(root, img)
    root.mainloop()



if __name__ == "__main__":
    main()
