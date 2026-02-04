# grid size, ranges
# =========================
# GRID CONFIGURATION
# =========================

GRID_WIDTH = 5
GRID_HEIGHT = 5

THUMB_SIZE = 180


# =========================
# FILTER SELECTION
# =========================
# Import filters here so config defines "genetics"

from filters import (
    blur,
    hue_shift,
    contrast,
    brightness,
    sharpen
)

# Choose active filters
FILTER_A = blur
FILTER_B = hue_shift


# =========================
# PARAMETER RANGES
# =========================
# Each axis range should match perceptual usefulness

FILTER_A_RANGE = (0.0, 6.0)     # blur radius
FILTER_B_RANGE = (0.0, 0.5)     # hue shift amount


# =========================
# ADVANCED (OPTIONAL)
# =========================

# Use nonlinear spacing (perceptual)
USE_NONLINEAR = True

# Gamma curve for spacing (higher = more subtle near zero)
NONLINEAR_GAMMA = 2.2


# =========================
# RENDERING
# =========================

# Render grid at reduced resolution for speed
RENDER_SCALE = 0.5
DEFAULT_IMAGE_PATH = "default.png"
