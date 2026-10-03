"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Standard image input/output helpers.

Canopy GSM requires genuine 3-channel RGB images.
Grayscale, RGBA/multi-channel-alpha, and non-8-bit images are rejected.
No image is converted or reshaped to make an invalid input acceptable.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from gsm_engine import (
    GSMInputError,
    SUPPORTED_IMAGE_EXTENSIONS,
    validate_rgb_uint8_image,
)

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


def is_supported_image_file(path: str | Path) -> bool:
    """
    Return True when the filename extension is supported by Canopy GSM.
    """
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def find_image_files(folder: str | Path) -> list[Path]:
    """
    Return supported image files in a folder, sorted case-insensitively.

    File extension matching is case-insensitive.
    """
    directory = Path(folder)

    if not directory.is_dir():
        raise GSMInputError(
            f"Input folder does not exist: {directory}"
        )

    return sorted(
        (
            p
            for p in directory.iterdir()
            if p.is_file()
            and is_supported_image_file(p)
        ),
        key=lambda p: p.name.casefold(),
    )


def load_rgb_uint8(path: str | Path) -> np.ndarray:
    """
    Load a genuine 8-bit, 3-channel RGB image.

    Scientific input requirements
    ------------------------------
    Accepted:
        - 8-bit, 3-channel color image

    Rejected:
        - grayscale image
        - RGBA / 4-channel image
        - multi-channel image with any channel count other than 3
        - non-8-bit image
        - unreadable image
        - unsupported file extension

    No resizing, grayscale-to-RGB conversion, alpha removal, or other
    scientific image transformation is performed.

    OpenCV decodes ordinary color images internally as BGR. The final
    channel-order conversion BGR -> RGB only restores the declared RGB
    representation required by the GSM scientific engine.
    """
    if cv2 is None:
        raise GSMInputError(
            "OpenCV is required for image loading."
        )

    file_path = Path(path)

    if not file_path.is_file():
        raise GSMInputError(
            f"Image file does not exist: {file_path}"
        )

    if not is_supported_image_file(file_path):
        raise GSMInputError(
            f"Unsupported image format: {file_path.suffix}"
        )

    # Read without forcing a color conversion.
    # This allows us to inspect the actual decoded channel structure
    # before deciding whether the image is a valid GSM input.
    raw = cv2.imread(
        str(file_path),
        cv2.IMREAD_UNCHANGED,
    )

    if raw is None:
        raise GSMInputError(
            f"Could not read image: {file_path.name}"
        )

    # GSM v2.1 reference path currently operates on 8-bit RGB data.
    if raw.dtype != np.uint8:
        raise GSMInputError(
            f"Unsupported pixel depth in {file_path.name}: {raw.dtype}. "
            "Canopy GSM requires an 8-bit RGB image."
        )

    # A two-dimensional array is a grayscale image.
    if raw.ndim == 2:
        raise GSMInputError(
            f"{file_path.name} is grayscale. "
            "Canopy GSM requires a genuine 3-channel RGB image."
        )

    # Canopy GSM accepts exactly three channels.
    #
    # In particular, do NOT silently drop an alpha channel from RGBA.
    if raw.ndim != 3:
        raise GSMInputError(
            f"{file_path.name} has an unsupported image structure. "
            "Canopy GSM requires a 3-channel RGB image."
        )

    if raw.shape[2] != 3:
        if raw.shape[2] == 4:
            raise GSMInputError(
                f"{file_path.name} has 4 channels (RGBA/BGRA). "
                "Canopy GSM requires a 3-channel RGB image; "
                "alpha channels are not removed or converted."
            )

        raise GSMInputError(
            f"{file_path.name} has {raw.shape[2]} channels. "
            "Canopy GSM requires exactly 3 RGB channels."
        )

    # OpenCV decodes standard 3-channel color images as BGR.
    # Convert only the channel ordering to obtain the RGB array required
    # by the GSM engine. This does not convert the file format or alter
    # the number/depth of pixels.
    rgb = cv2.cvtColor(
        raw,
        cv2.COLOR_BGR2RGB,
    )

    return validate_rgb_uint8_image(rgb)


def save_rgb_uint8(
    image: np.ndarray,
    path: str | Path,
    jpeg_quality: int = 75,
) -> None:
    """
    Save an RGB uint8 array using an OpenCV-supported image format.

    JPEG output defaults to quality 75 to match the default JPEG quality
    used by MATLAB imwrite() in the MATLAB v2.1 reference workflow.

    Scientific image validation remains strict:
        - 3-channel RGB
        - uint8

    The BGR conversion is only the channel-order adaptation required by
    OpenCV's encoder.
    """
    if cv2 is None:
        raise GSMInputError(
            "OpenCV is required for image saving."
        )

    image = validate_rgb_uint8_image(
        image
    )

    file_path = Path(path)

    if not file_path.suffix:
        raise GSMInputError(
            "Output image filename must include an extension."
        )

    extension = (
        file_path.suffix.lower()
    )

    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        raise GSMInputError(
            f"Unsupported output image format: {file_path.suffix}"
        )

    if not isinstance(
        jpeg_quality,
        int,
    ):
        raise GSMInputError(
            "JPEG quality must be an integer."
        )

    if not 0 <= jpeg_quality <= 100:
        raise GSMInputError(
            "JPEG quality must be between 0 and 100."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # OpenCV image encoders expect BGR.
    bgr = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR,
    )

    parameters = []

    if extension in {
        ".jpg",
        ".jpeg",
    }:
        parameters = [
            cv2.IMWRITE_JPEG_QUALITY,
            jpeg_quality,
        ]

    success = cv2.imwrite(
        str(file_path),
        bgr,
        parameters,
    )

    if not success:
        raise GSMInputError(
            f"Could not write image: {file_path}"
        )