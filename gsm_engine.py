"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Scientific reimplementation of the established MATLAB Canopy GSM workflow.
Reference implementation: Canopy GSM MATLAB v2.1.

The software concept, scientific design, methodological decisions,
project direction, and overall development were led by Abbas Haghshenas;
the Python code was developed with coding assistance from OpenAI's GPT-5.6 Luna.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

from st3 import st3_reference
from curve_fitting import ExpFitResult, fit_exp1

try:
    import cv2
except ImportError:  # pragma: no cover - only required for HSV segmentation
    cv2 = None


VERSION = "1.0.0"
GREEN_LEVELS = np.arange(1, 256, dtype=np.int16)
BACKGROUND_RGB = (150, 0, 150)
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


class GSMInputError(ValueError):
    """Raised for invalid image or GSM configuration input."""


@dataclass(frozen=True)
class ST1Config:
    method: str = "G>R"
    hsv_h_min: int = 25
    hsv_h_max: int = 95
    hsv_s_min: int = 40
    hsv_s_max: int = 255
    hsv_v_min: int = 30
    hsv_v_max: int = 255
    custom_path: Optional[Path] = None


@dataclass
class GSMResult:
    """Scientific result for one RGB image."""

    levels: np.ndarray
    mean_red: np.ndarray
    green: np.ndarray
    mean_blue: np.ndarray
    var_red: np.ndarray
    var_blue: np.ndarray
    number_of_pixels: np.ndarray
    red_auc: np.ndarray
    blue_auc: np.ndarray
    rb_abc: np.ndarray
    red_slope: np.ndarray
    blue_slope: np.ndarray
    red_st3_class: np.ndarray
    blue_st3_class: np.ndarray
    exp_red: ExpFitResult
    exp_blue: ExpFitResult
    st1_mask: np.ndarray
    processed_image: np.ndarray

    @property
    def columns(self) -> list[str]:
        return [
            "Green_level", "Mean_Red", "Green", "Mean_Blue",
            "Var_Red", "Var_Blue", "Number_of_pixels", "Red_AUC",
            "Blue_AUC", "RB_ABC", "Red_Slope", "Blue_slope",
            "Red_ST3_class", "Blue_ST3_class", "R2_exp_Red",
            "RMSE_exp_Red", "exp_a_Red", "exp_b_Red", "R2_exp_Blue",
            "RMSE_exp_Blue", "exp_a_Blue", "exp_b_Blue",
        ]

    def as_records(self) -> list[dict[str, float | int | None]]:
        """Return the 255 scientific Green-level rows only."""
        rows: list[dict[str, float | int | None]] = []
        for i, level in enumerate(self.levels):
            rows.append({
                "Green_level": int(level),
                "Mean_Red": _scalar_or_nan(self.mean_red[i]),
                "Green": int(level),
                "Mean_Blue": _scalar_or_nan(self.mean_blue[i]),
                "Var_Red": _scalar_or_nan(self.var_red[i]),
                "Var_Blue": _scalar_or_nan(self.var_blue[i]),
                "Number_of_pixels": int(self.number_of_pixels[i]),
                "Red_AUC": _scalar_or_nan(self.red_auc[i]),
                "Blue_AUC": _scalar_or_nan(self.blue_auc[i]),
                "RB_ABC": _scalar_or_nan(self.rb_abc[i]),
                "Red_Slope": _scalar_or_nan(self.red_slope[i]),
                "Blue_slope": _scalar_or_nan(self.blue_slope[i]),
                "Red_ST3_class": int(self.red_st3_class[i]),
                "Blue_ST3_class": int(self.blue_st3_class[i]),
                "R2_exp_Red": np.nan,
                "RMSE_exp_Red": np.nan,
                "exp_a_Red": np.nan,
                "exp_b_Red": np.nan,
                "R2_exp_Blue": np.nan,
                "RMSE_exp_Blue": np.nan,
                "exp_a_Blue": np.nan,
                "exp_b_Blue": np.nan,
            })
        return rows

    def as_matlab_compat_records(self) -> list[dict[str, float | int | None]]:
        """Return rows matching the MATLAB single-image CSV layout.

        MATLAB writes a leading summary row containing only the exponential-fit
        statistics, followed by the 255 Green-level rows.
        """
        summary = {
            "Green_level": np.nan,
            "Mean_Red": np.nan,
            "Green": np.nan,
            "Mean_Blue": np.nan,
            "Var_Red": np.nan,
            "Var_Blue": np.nan,
            "Number_of_pixels": np.nan,
            "Red_AUC": np.nan,
            "Blue_AUC": np.nan,
            "RB_ABC": np.nan,
            "Red_Slope": np.nan,
            "Blue_slope": np.nan,
            "Red_ST3_class": 0,
            "Blue_ST3_class": 0,
            "R2_exp_Red": _scalar_or_nan(self.exp_red.rsquare),
            "RMSE_exp_Red": _scalar_or_nan(self.exp_red.rmse),
            "exp_a_Red": _scalar_or_nan(self.exp_red.a),
            "exp_b_Red": _scalar_or_nan(self.exp_red.b),
            "R2_exp_Blue": _scalar_or_nan(self.exp_blue.rsquare),
            "RMSE_exp_Blue": _scalar_or_nan(self.exp_blue.rmse),
            "exp_a_Blue": _scalar_or_nan(self.exp_blue.a),
            "exp_b_Blue": _scalar_or_nan(self.exp_blue.b),
        }
        return [summary, *self.as_records()]



def _scalar_or_nan(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def validate_rgb_uint8_image(image: np.ndarray) -> np.ndarray:
    if not isinstance(image, np.ndarray):
        raise GSMInputError("Image must be a NumPy array.")
    if image.ndim != 3 or image.shape[2] != 3:
        raise GSMInputError("Image must have shape (height, width, 3).")
    if image.dtype != np.uint8:
        raise GSMInputError("Reference GSM processing expects an RGB uint8 image.")
    return image


def segment_st1(image: np.ndarray, config: ST1Config) -> np.ndarray:
    """Create an ST1 vegetation mask using a built-in or custom method."""
    image = validate_rgb_uint8_image(image)
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    method = config.method.strip().upper()

    if method == "G>R":
        return g > r
    if method == "G>R&G>B":
        return (g > r) & (g > b)
    if method == "2G-R-B>0":
        return (2 * g.astype(np.int16) - r.astype(np.int16) - b.astype(np.int16)) > 0
    if method == "HSV":
        return _segment_hsv(image, config)
    if method == "CUSTOM":
        return _segment_custom(image, config.custom_path)
    raise GSMInputError(f"Unknown ST1 method: {config.method}")


def _segment_hsv(image: np.ndarray, config: ST1Config) -> np.ndarray:
    if cv2 is None:
        raise GSMInputError("OpenCV is required for HSV segmentation.")
    ranges = [
        ("H_min", config.hsv_h_min, 0, 179),
        ("H_max", config.hsv_h_max, 0, 179),
        ("S_min", config.hsv_s_min, 0, 255),
        ("S_max", config.hsv_s_max, 0, 255),
        ("V_min", config.hsv_v_min, 0, 255),
        ("V_max", config.hsv_v_max, 0, 255),
    ]
    for name, value, low, high in ranges:
        if not low <= value <= high:
            raise GSMInputError(f"{name} must be between {low} and {high}.")
    if config.hsv_h_min > config.hsv_h_max:
        raise GSMInputError("H_min cannot exceed H_max.")
    if config.hsv_s_min > config.hsv_s_max:
        raise GSMInputError("S_min cannot exceed S_max.")
    if config.hsv_v_min > config.hsv_v_max:
        raise GSMInputError("V_min cannot exceed V_max.")

    # OpenCV consumes RGB only after an explicit conversion to BGR.
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([config.hsv_h_min, config.hsv_s_min, config.hsv_v_min], dtype=np.uint8)
    upper = np.array([config.hsv_h_max, config.hsv_s_max, config.hsv_v_max], dtype=np.uint8)
    return cv2.inRange(hsv, lower, upper) != 0


def _segment_custom(image: np.ndarray, custom_path: Optional[Path]) -> np.ndarray:
    if custom_path is None:
        raise GSMInputError("No Custom ST1 segmentation file has been selected.")
    path = Path(custom_path)
    if not path.is_file() or path.suffix.lower() != ".py":
        raise GSMInputError("Custom ST1 must be an existing Python .py file.")

    import importlib.util

    spec = importlib.util.spec_from_file_location("_canopygsm_custom_st1", str(path))
    if spec is None or spec.loader is None:
        raise GSMInputError("Could not load the Custom ST1 file.")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - user code path
        raise GSMInputError(f"Custom ST1 could not be imported: {exc}") from exc
    create_mask = getattr(module, "create_mask", None)
    if not callable(create_mask):
        raise GSMInputError("Custom ST1 file must define create_mask(image).")
    try:
        mask = np.asarray(create_mask(image))
    except Exception as exc:  # pragma: no cover - user code path
        raise GSMInputError(f"Custom ST1 create_mask failed: {exc}") from exc
    if mask.shape != image.shape[:2]:
        raise GSMInputError("Custom ST1 mask has the wrong shape.")
    return mask.astype(bool, copy=False)


def validate_background_rgb(background_rgb: Sequence[int]) -> tuple[int, int, int]:
    """Validate and normalize a user-selectable RGB background color."""
    if len(background_rgb) != 3:
        raise GSMInputError("Background color must contain exactly three RGB values.")
    values = tuple(int(v) for v in background_rgb)
    if any(v < 0 or v > 255 for v in values):
        raise GSMInputError("Each background RGB value must be between 0 and 255.")
    return values


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convert #RRGGBB (or RRGGBB) to an RGB tuple."""
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise GSMInputError("HEX color must have exactly 6 hexadecimal digits.")
    try:
        rgb = tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise GSMInputError("Invalid HEX color code.") from exc
    return validate_background_rgb(rgb)


def make_processed_image(
    image: np.ndarray,
    mask: np.ndarray,
    background_rgb: Sequence[int] = BACKGROUND_RGB,
) -> np.ndarray:
    """
    Create the processed image using the exact MATLAB v2.1 visual logic.

    MATLAB performs:

        ImageForeground = uint8(ST1) .* Image

    followed by:

        ChangeBackColor(ImageForeground, r, g, b)

    ChangeBackColor replaces every zero value independently in each
    RGB channel with the corresponding background-channel value.

    This means that the MATLAB behavior is slightly different from simply
    copying foreground pixels and assigning one background color to all
    non-foreground pixels.

    This function affects only the processed-image visualization artifact.
    It does not alter the scientific GSM calculations.
    """
    image = validate_rgb_uint8_image(image)

    mask = np.asarray(
        mask,
        dtype=bool,
    )

    if mask.shape != image.shape[:2]:
        raise GSMInputError(
            "ST1 mask shape does not match the image."
        )

    background = validate_background_rgb(
        background_rgb
    )

    # ------------------------------------------------------------------
    # MATLAB equivalent of:
    #
    # ImageForgraound(:,:,k) =
    #     uint8(ST1(R,G,B)) .* Image(:,:,k)
    #
    # Multiplication by the binary mask is performed in each channel.
    # ------------------------------------------------------------------

    result = np.zeros_like(
        image,
        dtype=np.uint8,
    )

    result[mask] = image[mask]

    # ------------------------------------------------------------------
    # MATLAB ChangeBackColor equivalent.
    #
    # For each channel independently:
    #
    #   all zero pixels -> corresponding background value
    #
    # This is intentionally NOT limited to pixels outside the ST1 mask.
    # ------------------------------------------------------------------

    for channel, background_value in enumerate(
        background
    ):
        channel_data = result[:, :, channel]

        zero_indices = (
            channel_data == 0
        )

        if background_value != 0:
            channel_data[zero_indices] = (
                background_value
            )

    return result

def _sample_mean(values: np.ndarray) -> float:
    if values.size == 0:
        return np.nan
    return float(np.mean(values, dtype=np.float64))


def _sample_var(values: np.ndarray) -> float:
    # MATLAB var(x) uses N-1 normalization by default. For one observation,
    # MATLAB returns 0; for an empty vector, the result is NaN.
    if values.size == 0:
        return np.nan
    if values.size == 1:
        return 0.0
    return float(np.var(values, ddof=1, dtype=np.float64))


def _compute_st2(
    image: np.ndarray,
    mask: np.ndarray,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> tuple[np.ndarray, ...]:
    r = image[:, :, 0]
    b = image[:, :, 2]
    g = image[:, :, 1]
    masked_g = np.where(mask, g, 0).astype(np.uint8)

    mean_red = np.full(255, np.nan, dtype=np.float64)
    mean_blue = np.full(255, np.nan, dtype=np.float64)
    var_red = np.full(255, np.nan, dtype=np.float64)
    var_blue = np.full(255, np.nan, dtype=np.float64)
    number_of_pixels = np.zeros(255, dtype=np.int64)

    # Prefix sums implement the exact cumulative-sum definition used by MATLAB.
    red_auc = np.zeros(255, dtype=np.float64)
    blue_auc = np.zeros(255, dtype=np.float64)

    for j in range(1, 256):
        selected = masked_g == j
        red_values = r[selected].astype(np.float64)
        blue_values = b[selected].astype(np.float64)

        idx = j - 1
        mean_red[idx] = _sample_mean(red_values)
        mean_blue[idx] = _sample_mean(blue_values)
        var_red[idx] = _sample_var(red_values)
        var_blue[idx] = _sample_var(blue_values)
        number_of_pixels[idx] = int(red_values.size)

        red_auc[idx] = (red_auc[idx - 1] if idx else 0.0) + (
            0.0 if np.isnan(mean_red[idx]) else mean_red[idx]
        )
        blue_auc[idx] = (blue_auc[idx - 1] if idx else 0.0) + (
            0.0 if np.isnan(mean_blue[idx]) else mean_blue[idx]
        )

        if progress_callback is not None:
            progress_callback(j)

    rb_abc = red_auc - blue_auc
    return mean_red, mean_blue, var_red, var_blue, number_of_pixels, red_auc, blue_auc, rb_abc


def _reference_slope_series(
    red_values: np.ndarray,
    blue_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Translate the MATLAB local-slope control flow.

    MATLAB stores slope results in cells. A cell can be genuinely empty when
    the current mean curve value is NaN, and ST3 distinguishes an empty cell
    from a cell containing numeric data. Therefore this function returns both
    numeric slope arrays and boolean masks describing populated slope cells.
    """
    red_values = np.asarray(red_values, dtype=np.float64)
    blue_values = np.asarray(blue_values, dtype=np.float64)
    if red_values.shape != (255,) or blue_values.shape != (255,):
        raise ValueError("GSM slope vectors must each contain 255 Green levels.")

    red = np.full(257, np.nan, dtype=np.float64)
    blue = np.full(257, np.nan, dtype=np.float64)
    red[2:] = red_values
    blue[2:] = blue_values

    # In the MATLAB source Data(j,11/12) is populated exactly when j>2 and
    # the corresponding mean value is not NaN. The first populated slope cell
    # can therefore correspond to Green level 1.
    red_defined = np.zeros(257, dtype=bool)
    blue_defined = np.zeros(257, dtype=bool)
    red_defined[2:] = np.isfinite(red_values)
    blue_defined[2:] = np.isfinite(blue_values)

    out_red = np.full(257, np.nan, dtype=np.float64)
    out_blue = np.full(257, np.nan, dtype=np.float64)

    for j in range(3, 258):  # MATLAB j = 3:257
        if not np.isnan(red[j - 1]):
            if j < 257:
                beforind = 1
                afterind = 1
                temp = red[j - 1]

                while (
                    np.isnan(red[j + afterind - 1])
                    and j < (j + afterind) - 1
                ):
                    afterind += 1

                while (
                    np.isnan(red[j - beforind - 1])
                    and j > (j - beforind) + 1
                ):
                    beforind += 1

                if (j - beforind) > 2 and not np.isnan(red[j - beforind - 1]):
                    mat1 = red[j - beforind - 1]
                else:
                    beforind = -1
                    mat1 = temp

                if (j + afterind) <= 257 and not np.isnan(red[j + afterind - 1]):
                    mat2 = red[j + afterind - 1]
                else:
                    afterind = -1
                    mat2 = temp

                if afterind == -1:
                    out_red[j - 1] = (temp - mat1) / beforind
                elif beforind == -1:
                    out_red[j - 1] = (mat2 - temp) / afterind
                else:
                    out_red[j - 1] = np.mean([
                        (mat2 - temp) / afterind,
                        (temp - mat1) / beforind,
                    ])

                # Reuse beforind/afterind for Blue exactly as in MATLAB.
                if (j - beforind) > 2 and not np.isnan(blue[j - beforind - 1]):
                    mat1 = blue[j - beforind - 1]
                else:
                    beforind = -1
                    mat1 = blue[j - 1]

                if (j + afterind) <= 257 and not np.isnan(blue[j + afterind - 1]):
                    mat2 = blue[j + afterind - 1]
                else:
                    afterind = -1
                    mat2 = blue[j - 1]

                temp = blue[j - 1]
                if afterind == -1:
                    out_blue[j - 1] = (temp - mat1) / beforind
                elif beforind == -1:
                    out_blue[j - 1] = (mat2 - temp) / afterind
                else:
                    out_blue[j - 1] = np.mean([
                        (mat2 - temp) / afterind,
                        (temp - mat1) / beforind,
                    ])
            else:
                # MATLAB j=257 branch: backward difference only.
                beforind = 1
                temp = red[j - 1]
                while np.isnan(red[j - beforind - 1]):
                    beforind += 1

                if (j - beforind) > 2 and not np.isnan(red[j - beforind - 1]):
                    mat1 = red[j - beforind - 1]
                else:
                    mat1 = temp
                out_red[j - 1] = (temp - mat1) / beforind

                if (j - beforind) > 2 and not np.isnan(blue[j - beforind - 1]):
                    mat1 = blue[j - beforind - 1]
                else:
                    mat1 = blue[j - 1]
                temp = blue[j - 1]
                out_blue[j - 1] = (temp - mat1) / beforind

    return (
        out_red[2:].copy(),
        out_blue[2:].copy(),
        red_defined[2:].copy(),
        blue_defined[2:].copy(),
    )

def process_image(
    image: np.ndarray,
    st1_config: ST1Config = ST1Config(),
    st3_m: int = 12,
    st3_p: int = 50,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    background_rgb: Sequence[int] = BACKGROUND_RGB,
) -> GSMResult:
    """Process one RGB image through the provisional GSM v2.1 reference path."""
    image = validate_rgb_uint8_image(image)
    if st3_m < 0 or st3_p < 0:
        raise GSMInputError("ST3 m and p must be non-negative.")

    mask = segment_st1(image, st1_config)
    processed = make_processed_image(image, mask, background_rgb=background_rgb)

    def on_level(level: int) -> None:
        if progress_callback is not None:
            progress_callback("ST2", level)

    (
        mean_red,
        mean_blue,
        var_red,
        var_blue,
        number_of_pixels,
        red_auc,
        blue_auc,
        rb_abc,
    ) = _compute_st2(image, mask, on_level)

    red_slope, blue_slope, red_defined, blue_defined = _reference_slope_series(
        mean_red, mean_blue
    )

    # MATLAB passes Data(2:end,11/12) to ST3. Preserve genuine empty cells
    # rather than representing every missing slope as a numeric NaN.
    red_st3_input = [None] + [
        value if defined else None
        for value, defined in zip(red_slope, red_defined)
    ]
    blue_st3_input = [None] + [
        value if defined else None
        for value, defined in zip(blue_slope, blue_defined)
    ]

    red_st3 = st3_reference(red_st3_input, st3_m, st3_p)[1:]
    blue_st3 = st3_reference(blue_st3_input, st3_m, st3_p)[1:]

    exp_red = fit_exp1(GREEN_LEVELS.astype(np.float64), mean_red)
    exp_blue = fit_exp1(GREEN_LEVELS.astype(np.float64), mean_blue)

    return GSMResult(
        levels=GREEN_LEVELS.copy(),
        mean_red=mean_red,
        green=GREEN_LEVELS.astype(np.float64),
        mean_blue=mean_blue,
        var_red=var_red,
        var_blue=var_blue,
        number_of_pixels=number_of_pixels,
        red_auc=red_auc,
        blue_auc=blue_auc,
        rb_abc=rb_abc,
        red_slope=red_slope,
        blue_slope=blue_slope,
        red_st3_class=np.asarray(red_st3, dtype=np.int16),
        blue_st3_class=np.asarray(blue_st3, dtype=np.int16),
        exp_red=exp_red,
        exp_blue=exp_blue,
        st1_mask=mask,
        processed_image=processed,
    )
