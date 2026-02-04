import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import config


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

def generate_grid(seed_img):
    grid = []

    w, h = seed_img.size
    work_img = seed_img

    if config.RENDER_SCALE != 1.0:
        work_img = seed_img.resize(
            (int(w * config.RENDER_SCALE), int(h * config.RENDER_SCALE)),
            Image.LANCZOS
        )

    for y in range(config.GRID_HEIGHT):
        row = []

        ty = y / (config.GRID_HEIGHT - 1)
        if config.USE_NONLINEAR:
            ty = nonlinear(ty, config.NONLINEAR_GAMMA)

        b_val = lerp(
            config.FILTER_B_RANGE[0],
            config.FILTER_B_RANGE[1],
            ty
        )

        for x in range(config.GRID_WIDTH):
            tx = x / (config.GRID_WIDTH - 1)
            if config.USE_NONLINEAR:
                tx = nonlinear(tx, config.NONLINEAR_GAMMA)

            a_val = lerp(
                config.FILTER_A_RANGE[0],
                config.FILTER_A_RANGE[1],
                tx
            )

            img = work_img.copy()
            img = config.FILTER_A(img, a_val)
            img = config.FILTER_B(img, b_val)

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

        # ---- TOP BAR ----
        top = tk.Frame(root)
        top.pack(padx=10, pady=5, fill="x")

        tk.Button(top, text="Load Image", command=self.load_image).pack(
            side="left", padx=5
        )
        tk.Button(top, text="Save Current", command=self.save_image).pack(
            side="left", padx=5
        )

        # ---- ORIGINAL PREVIEW ----
        self.preview_frame = tk.Frame(root)
        self.preview_frame.pack(padx=10, pady=5)

        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack()

        # ---- GRID ----
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(padx=10, pady=10)

        self.update_preview()
        self.render_grid()

    # =========================
    # UI ACTIONS
    # =========================

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Load image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*"),
            ],
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
            title="Save image",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            self.current_img.save(path)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

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
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        grid = generate_grid(self.current_img)

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

                lbl.bind(
                    "<Button-1>",
                    lambda e, im=img: self.select(im)
                )

    def select(self, img):
        self.current_img = img
        self.render_grid()


# =========================
# BOOTSTRAP
# =========================

def main():
    root = tk.Tk()

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
    app = KPTExplorer(root, img)
    root.mainloop()


if __name__ == "__main__":
    main()
