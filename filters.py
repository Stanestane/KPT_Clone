from PIL import Image, ImageFilter, ImageEnhance
import colorsys


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
    Hue shift.
    strength: 0.0 – 1.0 (wraps around)
    """
    if strength == 0:
        return img

    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            h, s, v = colorsys.rgb_to_hsv(
                r / 255.0,
                g / 255.0,
                b / 255.0
            )

            h = (h + strength) % 1.0

            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
            pixels[x, y] = (
                int(r2 * 255),
                int(g2 * 255),
                int(b2 * 255)
            )

    return img


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
