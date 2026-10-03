"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Batch-processing application layer.

This module orchestrates multiple RGB images through the validated
Canopy GSM scientific engine.

Scientific processing remains in:
    gsm_engine.py
    st3.py
    curve_fitting.py
    io_utils.py

This module is responsible only for:
    - batch orchestration
    - output artifacts
    - aggregate CSV files
    - graph generation
    - processing log
    - live display observation data

The live display callbacks do not modify scientific calculations or
scientific outputs.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Callable

import cv2
import numpy as np

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from gsm_engine import (
    GSMInputError,
    ST1Config,
    VERSION,
    GSMResult,
    process_image,
    segment_st1,
)

from io_utils import (
    load_rgb_uint8,
    save_rgb_uint8,
)


class BatchCancelled(Exception):
    """Raised internally when the user requests Batch cancellation."""


# ============================================================================
# Configuration
# ============================================================================

@dataclass(frozen=True)
class BatchConfig:
    """
    Complete configuration for one Batch Processing run.
    """

    input_files: list[Path]
    output_root: Path
    st1_config: ST1Config

    st3_m: int = 12
    st3_p: int = 50

    background_rgb: tuple[int, int, int] = (
        150,
        0,
        150,
    )

    save_processed_images: bool = True

    # PNG is the normal user-facing output.
    # JPG/JPEG remains available for MATLAB v2.1 compatibility.
    processed_image_format: str = "png"

    # Used only when processed_image_format is JPG/JPEG.
    jpeg_quality: int = 75

    save_graphs: bool = True


# ============================================================================
# CSV helpers
# ============================================================================

def csv_value(value):
    """
    Convert scientific values to stable CSV text.

    None -> empty
    NaN  -> 'NaN'
    Inf  -> 'Inf'
    """

    if value is None:
        return ""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if np.isnan(value):
        return "NaN"

    if np.isinf(value):
        return (
            "Inf"
            if value > 0
            else "-Inf"
        )

    return format(
        value,
        ".17g",
    )


def write_result_csv(
    path: Path,
    records: list[dict],
) -> None:
    """
    Write one MATLAB-compatible per-image scientific CSV.

    MATLAB stores the exponential-fit values only in the first data
    row. The remaining 255 Green-level rows have blank cells in
    columns 15-22.

    Therefore columns 15-22 are deliberately written as blank strings
    from the second data row onward.
    """

    if not records:
        return

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(
        records[0].keys()
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row_index, record in enumerate(
            records
        ):

            output_row = {}

            for column_index, key in enumerate(
                fieldnames
            ):

                if (
                    row_index >= 1
                    and column_index >= 14
                ):

                    output_row[key] = ""

                else:

                    output_row[key] = csv_value(
                        record.get(
                            key,
                            "",
                        )
                    )

            writer.writerow(
                output_row
            )


# ============================================================================
# Aggregate records
# ============================================================================

def _make_total_exp_record(
    image_path: Path,
    result: GSMResult,
) -> dict:
    """
    Create one row of MATLAB's Total GSM Exp.csv.
    """

    return {
        "Image": image_path.name,
        "R2_exp_Red": result.exp_red.rsquare,
        "RMSE_exp_Red": result.exp_red.rmse,
        "Exp_a_Red": result.exp_red.a,
        "Exp_b_Red": result.exp_red.b,
        "R2_exp_Blue": result.exp_blue.rsquare,
        "RMSE_exp_Blue": result.exp_blue.rmse,
        "Exp_a_Blue": result.exp_blue.a,
        "Exp_b_Blue": result.exp_blue.b,
    }


def _make_total_st2_record(
    image_path: Path,
    result: GSMResult,
) -> dict:
    """
    Create one row of MATLAB's Total GSM ST2.csv.
    """

    record = {
        "Image": image_path.name,
    }

    for index in range(255):
        record[
            f"R_G{index + 1}"
        ] = result.mean_red[index]

    for index in range(255):
        record[
            f"B_G{index + 1}"
        ] = result.mean_blue[index]

    return record


def _make_total_num_record(
    image_path: Path,
    result: GSMResult,
) -> dict:
    """
    Create one row of MATLAB's Total GSM Num.csv.
    """

    record = {
        "Image": image_path.name,
    }

    for index in range(255):
        record[
            f"G{index + 1}"
        ] = int(
            result.number_of_pixels[index]
        )

    return record


def write_total_exp_csv(
    path: Path,
    records: list[dict],
) -> None:
    """
    Write MATLAB-compatible Total GSM Exp.csv.
    """

    fieldnames = [
        "Image",
        "R2_exp_Red",
        "RMSE_exp_Red",
        "Exp_a_Red",
        "Exp_b_Red",
        "R2_exp_Blue",
        "RMSE_exp_Blue",
        "Exp_a_Blue",
        "Exp_b_Blue",
    ]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:

            writer.writerow(
                {
                    key: csv_value(
                        record.get(
                            key,
                            "",
                        )
                    )
                    for key in fieldnames
                }
            )


def write_total_st2_csv(
    path: Path,
    records: list[dict],
) -> None:
    """
    Write MATLAB-compatible Total GSM ST2.csv.
    """

    fieldnames = (
        ["Image"]
        + [
            f"R_G{i}"
            for i in range(1, 256)
        ]
        + [
            f"B_G{i}"
            for i in range(1, 256)
        ]
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:

            writer.writerow(
                {
                    key: csv_value(
                        record.get(
                            key,
                            "",
                        )
                    )
                    for key in fieldnames
                }
            )


def write_total_num_csv(
    path: Path,
    records: list[dict],
) -> None:
    """
    Write MATLAB-compatible Total GSM Num.csv.
    """

    fieldnames = (
        ["Image"]
        + [
            f"G{i}"
            for i in range(1, 256)
        ]
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:

            writer.writerow(
                {
                    key: csv_value(
                        record.get(
                            key,
                            "",
                        )
                    )
                    for key in fieldnames
                }
            )


# ============================================================================
# Graph generation
# ============================================================================

def write_gsm_graph(
    result: GSMResult,
    image_path: Path,
    output_path: Path,
) -> None:
    """
    Create the MATLAB-style two-panel GSM graph.

    The graph uses exactly the 255 scientific Green levels represented
    by GSMResult.
    """

    x = result.levels.astype(
        np.float64
    )

    red = np.asarray(
        result.mean_red,
        dtype=np.float64,
    )

    green = np.asarray(
        result.green,
        dtype=np.float64,
    )

    blue = np.asarray(
        result.mean_blue,
        dtype=np.float64,
    )

    number_of_pixels = np.asarray(
        result.number_of_pixels,
        dtype=np.float64,
    )

    if not (
        len(x)
        == len(red)
        == len(green)
        == len(blue)
        == len(number_of_pixels)
        == 255
    ):
        raise ValueError(
            "GSM graph vectors must all contain exactly 255 Green levels."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, (
        ax1,
        ax2,
    ) = plt.subplots(
        2,
        1,
        figsize=(7.5, 9.25),
    )

    ax1.plot(
        x,
        red,
        ".r",
    )

    ax1.plot(
        x,
        green,
        ".g",
    )

    ax1.plot(
        x,
        blue,
        ".b",
    )

    ax1.set_xlim(
        -1,
        256,
    )

    ax1.set_ylim(
        -1,
        256,
    )

    ax1.set_title(
        "GSM Graph"
    )

    ax1.set_ylabel(
        "Mean Red, Green, Mean Blue (0-255)"
    )

    ax1.set_xlabel(
        "Green Level (1-255)"
    )

    if hasattr(
        ax1,
        "set_box_aspect",
    ):
        ax1.set_box_aspect(
            1
        )

    ax2.plot(
        x,
        number_of_pixels,
        ".k",
    )

    ax2.set_xlim(
        -1,
        256,
    )

    ax2.set_title(
        "Number of pixels"
    )

    ax2.set_ylabel(
        "Number of pixels"
    )

    ax2.set_xlabel(
        "Green Level (1-255)"
    )

    if hasattr(
        ax2,
        "set_box_aspect",
    ):
        ax2.set_box_aspect(
            1
        )

    fig.subplots_adjust(
        left=0.14,
        right=0.94,
        top=0.95,
        bottom=0.08,
        hspace=0.32,
    )

    fig.savefig(
        output_path,
        format="pdf",
    )

    plt.close(
        fig
    )


# ============================================================================
# Batch worker
# ============================================================================

class BatchWorker:
    """
    Batch-processing worker independent of the GUI.

    Scientific processing is delegated to process_image().

    The live callbacks are observation-only. They provide display data
    to the GUI without modifying the scientific computation.
    """

    # The live preview is intentionally smaller than the scientific
    # full-resolution image. This prevents transferring multi-megapixel
    # arrays through Qt signals 255 times.
    LIVE_MAX_WIDTH = 1100
    LIVE_MAX_HEIGHT = 800

    def __init__(
        self,
        config: BatchConfig,
        cancel_event: Event,
        progress_callback: Callable[[int], None] | None = None,
        image_started_callback: Callable[
            [int, int, str],
            None,
        ] | None = None,
        image_finished_callback: Callable[
            [int, int, str, float, str],
            None,
        ] | None = None,
        log_callback: Callable[[str], None] | None = None,
        live_initialized_callback: Callable[
            [
                object,
                object,
                object,
                tuple[int, int, int],
                str,
            ],
            None,
        ] | None = None,
        live_level_callback: Callable[
            [int, float, float, int],
            None,
        ] | None = None,
    ):

        self.config = config

        self.cancel_event = cancel_event

        self.progress_callback = (
            progress_callback
        )

        self.image_started_callback = (
            image_started_callback
        )

        self.image_finished_callback = (
            image_finished_callback
        )

        self.log_callback = (
            log_callback
        )

        self.live_initialized_callback = (
            live_initialized_callback
        )

        self.live_level_callback = (
            live_level_callback
        )

        self.results_dir = (
            config.output_root
            / "Results"
        )

        self.processed_dir = (
            config.output_root
            / "Processed images"
        )

        self.graphs_dir = (
            config.output_root
            / "Graphs"
        )

        self.total_exp_path = (
            self.results_dir
            / "Total GSM Exp.csv"
        )

        self.total_st2_path = (
            self.results_dir
            / "Total GSM ST2.csv"
        )

        self.total_num_path = (
            self.results_dir
            / "Total GSM Num.csv"
        )

        self.log_path: Path | None = None
        self._log_file = None

        self.total_exp_records: list[dict] = []
        self.total_st2_records: list[dict] = []
        self.total_num_records: list[dict] = []

        self.start_datetime: datetime | None = None
        self.end_datetime: datetime | None = None

    # ========================================================================
    # Validation
    # ========================================================================

    def _validate_configuration(self) -> None:

        if not self.config.input_files:

            raise GSMInputError(
                "No input images were selected."
            )

        if self.config.st3_m < 0:

            raise GSMInputError(
                "ST3 m must be non-negative."
            )

        if self.config.st3_p < 0:

            raise GSMInputError(
                "ST3 P must be non-negative."
            )

        fmt = (
            self.config.processed_image_format
            .strip()
            .lower()
            .lstrip(".")
        )

        if fmt not in {
            "jpg",
            "jpeg",
            "png",
        }:

            raise GSMInputError(
                "Processed image format must be JPG, JPEG, or PNG."
            )

        if not isinstance(
            self.config.jpeg_quality,
            int,
        ):

            raise GSMInputError(
                "JPEG quality must be an integer."
            )

        if not 0 <= self.config.jpeg_quality <= 100:

            raise GSMInputError(
                "JPEG quality must be between 0 and 100."
            )

    # ========================================================================
    # Logging
    # ========================================================================

    def _emit_log(
        self,
        message: str,
    ) -> None:

        if self.log_callback is not None:

            self.log_callback(
                message
            )

        if self._log_file is not None:

            self._log_file.write(
                f"{message}\n"
            )

            self._log_file.flush()

    def _open_log(self) -> None:

        self.config.output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        self.log_path = (
            self.config.output_root
            / f"CanopyGSM_Batch_{stamp}.log"
        )

        self._log_file = (
            self.log_path.open(
                "w",
                encoding="utf-8",
            )
        )

    def _close_log(self) -> None:

        if self._log_file is not None:

            self._log_file.close()

            self._log_file = None

    def _format_duration(
        self,
        seconds: float,
    ) -> str:

        total_seconds = max(
            0,
            int(round(seconds)),
        )

        hours = (
            total_seconds // 3600
        )

        minutes = (
            total_seconds % 3600
        ) // 60

        secs = (
            total_seconds % 60
        )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    def _log_configuration(
        self,
    ) -> None:

        config = self.config

        self._emit_log(
            "Canopy GSM for Python"
        )

        self._emit_log(
            f"Version: {VERSION}"
        )

        self._emit_log(
            "=" * 60
        )

        self._emit_log(
            "PROCESSING SUMMARY"
        )

        self._emit_log(
            "-" * 60
        )

        self._emit_log(
            "Status: Processing started."
        )

        self._emit_log(
            "Start time: "
            + self.start_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        self._emit_log(
            f"Images found / attempted: "
            f"{len(config.input_files)}"
        )

        self._emit_log(
            ""
        )

        self._emit_log(
            "INPUT / OUTPUT"
        )

        self._emit_log(
            "-" * 60
        )

        self._emit_log(
            f"Input folder: "
            f"{self._common_input_folder()}"
        )

        self._emit_log(
            f"Output folder: "
            f"{config.output_root}"
        )

        self._emit_log(
            ""
        )

        self._emit_log(
            "ANALYSIS SETTINGS"
        )

        self._emit_log(
            "-" * 60
        )

        self._emit_log(
            f"Segmentation method: "
            f"{config.st1_config.method}"
        )

        if (
            config.st1_config.method
            .strip()
            .upper()
            == "HSV"
        ):

            self._emit_log(
                "HSV parameters: "
                f"H {config.st1_config.hsv_h_min}-"
                f"{config.st1_config.hsv_h_max}, "
                f"S {config.st1_config.hsv_s_min}-"
                f"{config.st1_config.hsv_s_max}, "
                f"V {config.st1_config.hsv_v_min}-"
                f"{config.st1_config.hsv_v_max}"
            )

        else:

            self._emit_log(
                "HSV parameters: Not used"
            )

        if (
            config.st1_config.method
            .strip()
            .upper()
            == "CUSTOM"
        ):

            self._emit_log(
                f"Custom segmentation: "
                f"{config.st1_config.custom_path}"
            )

        else:

            self._emit_log(
                "Custom segmentation: Not used"
            )

        self._emit_log(
            f"ST3 parameters: "
            f"m={config.st3_m}, "
            f"P={config.st3_p}"
        )

        self._emit_log(
            f"Background RGB: "
            f"{config.background_rgb}"
        )

        processed_format = (
            config.processed_image_format
            .strip()
            .lower()
            .lstrip(".")
        )

        self._emit_log(
            f"Processed image format: "
            f"{processed_format.upper()}"
        )

        if processed_format in {
            "jpg",
            "jpeg",
        }:

            self._emit_log(
                f"JPEG quality: "
                f"{config.jpeg_quality}"
            )

            self._emit_log(
                "Processed image mode: "
                "MATLAB v2.1-compatible JPEG"
            )

        else:

            self._emit_log(
                "Processed image mode: "
                "Lossless PNG for segmentation display"
            )

        self._emit_log(
            f"Save processed images: "
            f"{'Yes' if config.save_processed_images else 'No'}"
        )

        self._emit_log(
            f"Save GSM graphs: "
            f"{'Yes' if config.save_graphs else 'No'}"
        )

        self._emit_log(
            ""
        )

        self._emit_log(
            "IMAGE FILES"
        )

        self._emit_log(
            "-" * 60
        )

        for index, path in enumerate(
            config.input_files,
            start=1,
        ):

            self._emit_log(
                f"{index}. {path.name}"
            )

        self._emit_log(
            ""
        )

    def _common_input_folder(self) -> str:

        try:

            resolved_parents = [
                path.resolve().parent
                for path in self.config.input_files
            ]

            if not resolved_parents:
                return ""

            common = resolved_parents[0]

            for parent in resolved_parents[1:]:

                while (
                    common != common.parent
                    and common != parent
                    and common not in parent.parents
                ):

                    common = common.parent

            return str(
                common
            )

        except Exception:

            return str(
                self.config.input_files[0].parent
            )

    # ========================================================================
    # Live visualization preparation
    # ========================================================================

    def _prepare_live_visualization(
        self,
        image: np.ndarray,
        image_path: Path,
    ) -> None:
        """
        Prepare display-only data for the live visualization.

        Important:
            - The scientific image remains full resolution.
            - The live preview uses a nearest-neighbor sampled display image.
            - The preview is not used by process_image().
            - ST1 is evaluated for observation only.
            - Exact full-resolution per-green-level means/counts are computed
              for the live graph using vectorized binning.
        """

        if (
            self.live_initialized_callback is None
            and self.live_level_callback is None
        ):
            return

        self._check_cancelled()

        # ---------------------------------------------------------------
        # Observation-only ST1 mask
        # ---------------------------------------------------------------

        live_mask = segment_st1(
            image,
            self.config.st1_config,
        )

        live_mask = np.asarray(
            live_mask,
            dtype=bool,
        )

        if live_mask.shape != image.shape[:2]:

            raise GSMInputError(
                "Live ST1 mask shape does not match the input image."
            )

        # ---------------------------------------------------------------
        # Exact per-level display graph statistics.
        #
        # These do not feed the scientific engine. They are only supplied
        # to the live GUI.
        # ---------------------------------------------------------------

        masked_green = image[:, :, 1][
            live_mask
        ].astype(
            np.int16,
            copy=False,
        )

        masked_red = image[:, :, 0][
            live_mask
        ].astype(
            np.float64,
            copy=False,
        )

        masked_blue = image[:, :, 2][
            live_mask
        ].astype(
            np.float64,
            copy=False,
        )

        counts = np.bincount(
            masked_green,
            minlength=256,
        )

        red_sums = np.bincount(
            masked_green,
            weights=masked_red,
            minlength=256,
        )

        blue_sums = np.bincount(
            masked_green,
            weights=masked_blue,
            minlength=256,
        )

        red_means = np.full(
            256,
            np.nan,
            dtype=np.float64,
        )

        blue_means = np.full(
            256,
            np.nan,
            dtype=np.float64,
        )

        valid = (
            counts > 0
        )

        red_means[valid] = (
            red_sums[valid]
            / counts[valid]
        )

        blue_means[valid] = (
            blue_sums[valid]
            / counts[valid]
        )

        self._live_red_means = (
            red_means
        )

        self._live_blue_means = (
            blue_means
        )

        self._live_counts = (
            counts
        )

        # ---------------------------------------------------------------
        # Create a display-only nearest-neighbor preview.
        #
        # INTER_NEAREST is intentional: it preserves actual sampled
        # RGB/Green values instead of creating interpolated Green values.
        # ---------------------------------------------------------------

        height, width = image.shape[:2]

        scale = min(
            self.LIVE_MAX_WIDTH / width,
            self.LIVE_MAX_HEIGHT / height,
            1.0,
        )

        preview_width = max(
            1,
            int(round(width * scale)),
        )

        preview_height = max(
            1,
            int(round(height * scale)),
        )

        preview_rgb = cv2.resize(
            image,
            (
                preview_width,
                preview_height,
            ),
            interpolation=cv2.INTER_NEAREST,
        )

        preview_mask = cv2.resize(
            live_mask.astype(np.uint8),
            (
                preview_width,
                preview_height,
            ),
            interpolation=cv2.INTER_NEAREST,
        ).astype(
            bool
        )

        preview_green = (
            preview_rgb[:, :, 1]
        )

        if (
            self.live_initialized_callback
            is not None
        ):

            self.live_initialized_callback(
                np.ascontiguousarray(
                    preview_rgb,
                    dtype=np.uint8,
                ),
                np.ascontiguousarray(
                    preview_mask,
                    dtype=bool,
                ),
                np.ascontiguousarray(
                    preview_green,
                    dtype=np.uint8,
                ),
                tuple(
                    int(v)
                    for v in self.config.background_rgb
                ),
                image_path.name,
            )

    def _emit_live_level(
        self,
        level: int,
    ) -> None:
        """
        Emit exact full-resolution statistics for the current Green level.
        """

        if self.live_level_callback is None:
            return

        if not 1 <= int(level) <= 255:
            return

        index = int(level)

        red_mean = float(
            self._live_red_means[index]
        )

        blue_mean = float(
            self._live_blue_means[index]
        )

        count = int(
            self._live_counts[index]
        )

        self.live_level_callback(
            index,
            red_mean,
            blue_mean,
            count,
        )

    # ========================================================================
    # Cancellation / progress
    # ========================================================================

    def _check_cancelled(self) -> None:

        if self.cancel_event.is_set():

            raise BatchCancelled()

    def _progress_callback(
        self,
        image_index_zero_based: int,
        total_images: int,
        stage: str,
        level: int,
    ) -> None:

        self._check_cancelled()

        completed_levels = (
            image_index_zero_based * 255
            + level
        )

        total_levels = (
            total_images * 255
        )

        percentage = int(
            round(
                100.0
                * completed_levels
                / total_levels
            )
        )

        percentage = max(
            0,
            min(
                100,
                percentage,
            ),
        )

        if self.progress_callback is not None:

            self.progress_callback(
                percentage
            )

    # ========================================================================
    # Output paths
    # ========================================================================

    def _result_csv_path(
        self,
        image_path: Path,
    ) -> Path:

        return (
            self.results_dir
            / f"Results of image {image_path.name}.csv"
        )

    def _processed_image_path(
        self,
        image_path: Path,
    ) -> Path:

        fmt = (
            self.config.processed_image_format
            .strip()
            .lower()
            .lstrip(".")
        )

        if fmt in {
            "jpg",
            "jpeg",
        }:

            # Exact MATLAB v2.1 naming convention.
            return (
                self.processed_dir
                / f"Processed_{image_path.name}.jpg"
            )

        return (
            self.processed_dir
            / f"Processed_{image_path.stem}.png"
        )

    def _graph_path(
        self,
        image_path: Path,
    ) -> Path:

        return (
            self.graphs_dir
            / f"Graphs of image {image_path.name}.pdf"
        )

    # ========================================================================
    # Main processing
    # ========================================================================

    def run(
        self,
    ) -> tuple[int, int, bool]:
        """
        Execute the Batch.

        Returns:
            total_processed,
            successful,
            cancelled
        """

        self._validate_configuration()

        total = len(
            self.config.input_files
        )

        successful = 0
        cancelled = False

        start_all = time.perf_counter()

        self.start_datetime = datetime.now()

        self.config.output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.config.save_processed_images:

            self.processed_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

        if self.config.save_graphs:

            self.graphs_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._open_log()

        try:

            self._log_configuration()

            for index_zero, image_path in enumerate(
                self.config.input_files
            ):

                index = index_zero + 1

                start_one = (
                    time.perf_counter()
                )

                try:

                    self._check_cancelled()

                    if (
                        self.image_started_callback
                        is not None
                    ):

                        self.image_started_callback(
                            index,
                            total,
                            image_path.name,
                        )

                    self._emit_log(
                        f"{index}. {image_path.name} "
                        f"[PROCESSING]"
                    )

                    image = load_rgb_uint8(
                        image_path
                    )

                    # ------------------------------------------------------
                    # Live visualization initialization.
                    #
                    # This is an observation-only path. The actual
                    # scientific call below still receives the original
                    # full-resolution image exactly as before.
                    # ------------------------------------------------------

                    self._prepare_live_visualization(
                        image,
                        image_path,
                    )

                    self._check_cancelled()

                    def scientific_progress(
                        stage,
                        level,
                        image_index_zero=index_zero,
                        total_images=total,
                    ):

                        self._progress_callback(
                            image_index_zero,
                            total_images,
                            stage,
                            level,
                        )

                        try:
                            level_int = int(
                                level
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            return

                        if (
                            1
                            <= level_int
                            <= 255
                        ):

                            self._emit_live_level(
                                level_int
                            )

                    # ------------------------------------------------------
                    # Scientific processing.
                    #
                    # This remains the validated scientific engine.
                    # ------------------------------------------------------

                    result = process_image(
                        image,
                        st1_config=(
                            self.config.st1_config
                        ),
                        st3_m=(
                            self.config.st3_m
                        ),
                        st3_p=(
                            self.config.st3_p
                        ),
                        progress_callback=(
                            scientific_progress
                        ),
                        background_rgb=(
                            self.config.background_rgb
                        ),
                    )

                    self._check_cancelled()

                    # ------------------------------------------------------
                    # Scientific per-image CSV
                    # ------------------------------------------------------

                    result_csv = (
                        self._result_csv_path(
                            image_path
                        )
                    )

                    write_result_csv(
                        result_csv,
                        result.as_matlab_compat_records(),
                    )

                    # ------------------------------------------------------
                    # Processed image
                    # ------------------------------------------------------

                    processed_path = None

                    if (
                        self.config.save_processed_images
                    ):

                        processed_path = (
                            self._processed_image_path(
                                image_path
                            )
                        )

                        save_rgb_uint8(
                            result.processed_image,
                            processed_path,
                            jpeg_quality=(
                                self.config.jpeg_quality
                            ),
                        )

                    # ------------------------------------------------------
                    # GSM graph
                    # ------------------------------------------------------

                    graph_path = None

                    if self.config.save_graphs:

                        graph_path = (
                            self._graph_path(
                                image_path
                            )
                        )

                        write_gsm_graph(
                            result,
                            image_path,
                            graph_path,
                        )

                    self._check_cancelled()

                    elapsed = (
                        time.perf_counter()
                        - start_one
                    )

                    successful += 1

                    # ------------------------------------------------------
                    # Aggregate records
                    # ------------------------------------------------------

                    self.total_exp_records.append(
                        _make_total_exp_record(
                            image_path,
                            result,
                        )
                    )

                    self.total_st2_records.append(
                        _make_total_st2_record(
                            image_path,
                            result,
                        )
                    )

                    self.total_num_records.append(
                        _make_total_num_record(
                            image_path,
                            result,
                        )
                    )

                    # ------------------------------------------------------
                    # Log
                    # ------------------------------------------------------

                    self._emit_log(
                        "    Status: OK"
                    )

                    self._emit_log(
                        f"    Duration: "
                        f"{elapsed:.3f} s"
                    )

                    self._emit_log(
                        f"    Result: "
                        f"{result_csv.name}"
                    )

                    if processed_path is not None:

                        self._emit_log(
                            f"    Processed: "
                            f"{processed_path.name}"
                        )

                    if graph_path is not None:

                        self._emit_log(
                            f"    Graph: "
                            f"{graph_path.name}"
                        )

                    self._emit_log(
                        ""
                    )

                    if (
                        self.image_finished_callback
                        is not None
                    ):

                        self.image_finished_callback(
                            index,
                            total,
                            "OK",
                            elapsed,
                            "",
                        )

                except BatchCancelled:

                    elapsed = (
                        time.perf_counter()
                        - start_one
                    )

                    cancelled = True

                    self._emit_log(
                        "    Status: CANCELLED"
                    )

                    self._emit_log(
                        f"    Duration: "
                        f"{elapsed:.3f} s"
                    )

                    self._emit_log(
                        ""
                    )

                    if (
                        self.image_finished_callback
                        is not None
                    ):

                        self.image_finished_callback(
                            index,
                            total,
                            "CANCELLED",
                            elapsed,
                            "Cancelled by user.",
                        )

                    break

                except Exception as exc:

                    elapsed = (
                        time.perf_counter()
                        - start_one
                    )

                    error_text = str(
                        exc
                    )

                    self._emit_log(
                        "    Status: ERROR"
                    )

                    self._emit_log(
                        f"    Duration: "
                        f"{elapsed:.3f} s"
                    )

                    self._emit_log(
                        f"    Error: "
                        f"{error_text}"
                    )

                    if isinstance(
                        exc,
                        GSMInputError,
                    ):

                        self._emit_log(
                            "    The image was rejected "
                            "by the RGB uint8 input contract."
                        )

                    self._emit_log(
                        ""
                    )

                    if (
                        self.image_finished_callback
                        is not None
                    ):

                        self.image_finished_callback(
                            index,
                            total,
                            "ERROR",
                            elapsed,
                            error_text,
                        )

                    continue

            # ----------------------------------------------------------------
            # Aggregate files
            # ----------------------------------------------------------------

            if self.total_exp_records:

                write_total_exp_csv(
                    self.total_exp_path,
                    self.total_exp_records,
                )

                write_total_st2_csv(
                    self.total_st2_path,
                    self.total_st2_records,
                )

                write_total_num_csv(
                    self.total_num_path,
                    self.total_num_records,
                )

                self._emit_log(
                    "AGGREGATE RESULTS"
                )

                self._emit_log(
                    "-" * 60
                )

                self._emit_log(
                    "Total GSM Exp.csv"
                )

                self._emit_log(
                    "Total GSM ST2.csv"
                )

                self._emit_log(
                    "Total GSM Num.csv"
                )

                self._emit_log(
                    ""
                )

            # ----------------------------------------------------------------
            # Final summary
            # ----------------------------------------------------------------

            elapsed_all = (
                time.perf_counter()
                - start_all
            )

            self.end_datetime = datetime.now()

            error_count = (
                total - successful
            )

            if cancelled:

                status_text = (
                    "Processing cancelled by user."
                )

            elif successful == total:

                status_text = (
                    "Completed successfully."
                )

            else:

                status_text = (
                    "Completed with errors."
                )

            self._emit_log(
                "=" * 60
            )

            self._emit_log(
                "PROCESSING SUMMARY"
            )

            self._emit_log(
                "-" * 60
            )

            self._emit_log(
                f"Status: {status_text}"
            )

            self._emit_log(
                "Start time: "
                + self.start_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            self._emit_log(
                "End time: "
                + self.end_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            self._emit_log(
                "Processing duration: "
                + self._format_duration(
                    elapsed_all
                )
            )

            self._emit_log(
                f"Images found / attempted: "
                f"{total}"
            )

            self._emit_log(
                f"Images successfully analyzed: "
                f"{successful}"
            )

            self._emit_log(
                f"Images not successfully analyzed: "
                f"{error_count}"
            )

            self._emit_log(
                ""
            )

            self._emit_log(
                "=" * 60
            )

            self._emit_log(
                "Canopy GSM for Python — processing log"
            )

            if (
                total > 0
                and not cancelled
                and self.progress_callback is not None
            ):

                self.progress_callback(
                    100
                )

            return (
                total,
                successful,
                cancelled,
            )

        finally:

            self._close_log()