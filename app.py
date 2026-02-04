import tkinter as tk
from tkinter import filedialog
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
    if config.RENDER_SCALE != 1.0:
        seed_img = seed_img.resize(
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

            img = seed_img.copy()
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

        self.seed_img = seed_img.convert("RGB")

        self.container = tk.Frame(root)
        self.container.pack(padx=10, pady=10)

        self.render()

    def render(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        grid = generate_grid(self.seed_img)

        for y, row in enumerate(grid):
            for x, img in enumerate(row):
                thumb = img.resize(
                    (config.THUMB_SIZE, config.THUMB_SIZE),
                    Image.LANCZOS
                )
                tk_img = ImageTk.PhotoImage(thumb)

                lbl = tk.Label(
                    self.container,
                    image=tk_img,
                    bd=1,
                    relief="solid"
                )
                lbl.image = tk_img
                lbl.grid(row=y, column=x, padx=2, pady=2)

                lbl.bind(
                    "<Button-1>",
                    lambda e, im=img: self.select(im)
                )

    def select(self, img):
        self.seed_img = img
        self.render()


# =========================
# BOOTSTRAP
# =========================

def main():
    root = tk.Tk()

    file_path = filedialog.askopenfilename(
        title="Select seed image",
        filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.bmp"),
            ("All files", "*.*"),
        ],
    )

    if not file_path:
        return

    img = Image.open(file_path)

    app = KPTExplorer(root, img)
    root.mainloop()


if __name__ == "__main__":
    main()
