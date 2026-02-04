# filters.py
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import colorsys
import random
import math



# =========================
# FILTERS
# =========================

def blur(img, strength):
    """
    Gaussian blur.
    strength: 0.0 – ~10.0
    """
    if strength <= 0:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=strength))


def hue_shift(img, strength):
    """
    Hue shift using Pillow HSV colorspace.
    strength: 0.0 – 1.0
    """
    if strength == 0:
        return img

    # Convert to HSV
    hsv = img.convert("HSV")
    h, s, v = hsv.split()

    # Hue channel is 0–255
    h = h.point(lambda p: (p + int(strength * 255)) % 256)

    hsv = Image.merge("HSV", (h, s, v))
    return hsv.convert("RGB")


# =========================
# OPTIONAL EXTRAS
# (safe for evolution)
# =========================

def contrast(img, strength):
    """
    Contrast adjustment.
    strength: 0.5 – 2.0 (1.0 = neutral)
    """
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(strength)


def brightness(img, strength):
    """
    Brightness adjustment.
    strength: 0.5 – 2.0 (1.0 = neutral)
    """
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(strength)


def sharpen(img, strength):
    """
    Sharpen with controlled intensity.
    strength: 0.0 – 2.0
    """
    if strength <= 0:
        return img

    enhancer = ImageEnhance.Sharpness(img)
    return enhancer.enhance(1.0 + strength)

def blur(img, strength):
    if strength <= 0:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=strength))


def unsharp(img, strength):
    return img.filter(
        ImageFilter.UnsharpMask(
            radius=2,
            percent=int(strength * 100),
            threshold=3
        )
    )


def noise(img, strength):
    img = img.copy()
    px = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            n = int(random.uniform(-strength, strength))
            r, g, b = px[x, y]
            px[x, y] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n))
            )
    return img

def gamma(img, strength):
    inv = 1.0 / max(strength, 0.01)
    lut = [int((i / 255.0) ** inv * 255) for i in range(256)]
    return img.point(lut * 3)


def solarize(img, threshold):
    return ImageOps.solarize(img, int(threshold))
