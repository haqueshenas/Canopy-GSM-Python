"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Batch Processing user interface.

The GUI calls the independent batch-processing application layer, which in
turn calls the validated GSM scientific engine.

The scientific GSM engine itself is not implemented in this module.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

from pathlib import Path
from threading import Event

import numpy as np

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import (
    QColor,
    QBrush,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from batch_processor import BatchConfig, BatchWorker

from gsm_engine import (
    GSMInputError,
    ST1Config,
    hex_to_rgb,
)

from io_utils import (
    find_image_files,
    load_rgb_uint8,
)


# ============================================================================
# Visual identity
# ============================================================================

EPL_GREEN = "#57863c"
WINDOW_BACKGROUND = "#f5f6f4"
CARD_BACKGROUND = "#ffffff"
TEXT_PRIMARY = "#202520"
TEXT_SECONDARY = "#5f665f"
BORDER = "#d9ded6"

LIVE_IMAGE_BACKGROUND = "#ffffff"


# ============================================================================
# Qt worker wrapper
# ============================================================================

class QtBatchWorker(QObject):
    """
    Qt wrapper around the application-level BatchWorker.
    """

    progress = Signal(int)

    image_started = Signal(
        int,
        int,
        str,
    )

    image_finished = Signal(
        int,
        int,
        str,
        float,
        str,
    )

    log = Signal(str)

    live_initialized = Signal(
        object,
        object,
        object,
        object,
        str,
    )

    live_level = Signal(
        int,
        float,
        float,
        int,
    )

    finished = Signal(
        int,
        int,
        bool,
    )

    fatal_error = Signal(str)

    def __init__(
        self,
        config: BatchConfig,
        cancel_event: Event,
    ):
        super().__init__()

        self.config = config
        self.cancel_event = cancel_event

    @Slot()
    def run(self) -> None:

        try:

            worker = BatchWorker(
                config=self.config,
                cancel_event=self.cancel_event,
                progress_callback=self.progress.emit,
                image_started_callback=self.image_started.emit,
                image_finished_callback=self.image_finished.emit,
                log_callback=self.log.emit,
                live_initialized_callback=self.live_initialized.emit,
                live_level_callback=self.live_level.emit,
            )

            total, successful, cancelled = worker.run()

            self.finished.emit(
                total,
                successful,
                cancelled,
            )

        except Exception as exc:

            self.fatal_error.emit(
                str(exc)
            )


# ============================================================================
# Live GSM graph widget
# ============================================================================

class GSMGraphWidget(QWidget):
    """
    Lightweight Qt-painted live GSM graph.

    Only one graph is displayed:

        Mean Red / Green / Blue versus Green Level.

    The actual plotting rectangle is always exactly square.

    Data are displayed as filled points only.
    No connecting vectors or lines are drawn.
    """

    RED = "#d13d3d"
    GREEN = EPL_GREEN
    BLUE = "#356bd8"
    AXIS = "#707770"

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(
            parent
        )

        self.setMinimumSize(
            300,
            300,
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.reset()

    # ========================================================================
    # Data
    # ========================================================================

    def reset(self) -> None:

        self.green = np.full(
            256,
            np.nan,
            dtype=np.float64,
        )

        self.red = np.full(
            256,
            np.nan,
            dtype=np.float64,
        )

        self.blue = np.full(
            256,
            np.nan,
            dtype=np.float64,
        )

        self.current_level = 0

        self.update()

    def add_level(
        self,
        level: int,
        red_mean: float,
        blue_mean: float,
        count: int,
    ) -> None:
        """
        Add one Green-level observation.

        'count' is intentionally not plotted, but is accepted to preserve
        the existing live signal/API contract.
        """

        del count

        level = int(level)

        if not 1 <= level <= 255:
            return

        self.current_level = level

        self.green[level] = float(level)
        self.red[level] = float(red_mean)
        self.blue[level] = float(blue_mean)

        self.update()

    # ========================================================================
    # Geometry
    # ========================================================================

    def _plot_rect(
        self,
    ) -> tuple[int, int, int, int]:
        """
        Return an exactly square plotting rectangle.

        The width and height are always identical.
        """

        widget_width = max(
            1,
            self.width(),
        )

        widget_height = max(
            1,
            self.height(),
        )

        left_margin = 58
        right_margin = 18
        top_margin = 38
        bottom_margin = 48

        available_width = (
            widget_width
            - left_margin
            - right_margin
        )

        available_height = (
            widget_height
            - top_margin
            - bottom_margin
        )

        side = int(
            min(
                available_width,
                available_height,
            )
        )

        side = max(
            180,
            side,
        )

        left = (
            widget_width
            - side
        ) // 2

        top = (
            widget_height
            - side
            - bottom_margin
        ) // 2

        top = max(
            top_margin,
            top,
        )

        return (
            left,
            top,
            side,
            side,
        )

    # ========================================================================
    # Coordinate mapping
    # ========================================================================

    @staticmethod
    def _map_x(
        x: float,
        rect: tuple[int, int, int, int],
    ) -> float:

        left, _, width, _ = rect

        return (
            left
            + (
                (float(x) - 1.0)
                / 254.0
            )
            * width
        )

    @staticmethod
    def _map_y(
        y: float,
        rect: tuple[int, int, int, int],
    ) -> float:

        _, top, _, height = rect

        y = max(
            0.0,
            min(
                255.0,
                float(y),
            ),
        )

        return (
            top
            + (
                1.0
                - y / 255.0
            )
            * height
        )

    # ========================================================================
    # Drawing
    # ========================================================================

    def _draw_axes(
        self,
        painter: QPainter,
        rect: tuple[int, int, int, int],
    ) -> None:

        left, top, width, height = rect

        # Scientific display invariant:
        # the physical x and y dimensions of the plotting area are equal.
        assert width == height

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    self.AXIS
                ),
                1,
            )
        )

        painter.drawRect(
            left,
            top,
            width,
            height,
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                8,
            )
        )

        painter.setPen(
            QColor(
                TEXT_SECONDARY
            )
        )

        # X-axis labels.
        painter.drawText(
            left - 4,
            top + height + 17,
            "1",
        )

        painter.drawText(
            left + width - 25,
            top + height + 17,
            "255",
        )

        painter.drawText(
            left
            + width // 2
            - 28,
            top + height + 32,
            "Green Level",
        )

        # Y-axis label.
        painter.save()

        painter.translate(
            left - 40,
            top + height // 2,
        )

        painter.rotate(
            -90
        )

        painter.drawText(
            0,
            0,
            "Mean RGB",
        )

        painter.restore()

    def _draw_legend(
        self,
        painter: QPainter,
        rect: tuple[int, int, int, int],
    ) -> None:
        """
        Draw the color legend above the plotting rectangle.

        The legend is outside the data area and therefore cannot cover
        the plotted observations.
        """

        left, top, width, _ = rect

        items = (
            ("Red", self.RED),
            ("Green", self.GREEN),
            ("Blue", self.BLUE),
        )

        legend_width = 174

        legend_left = (
            left
            + (
                width
                - legend_width
            ) // 2
        )

        legend_y = max(
            12,
            top - 20,
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                8,
            )
        )

        x = legend_left

        for label, color in items:

            painter.setBrush(
                QBrush(
                    QColor(
                        color
                    )
                )
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.drawEllipse(
                x,
                legend_y - 5,
                8,
                8,
            )

            painter.setPen(
                QColor(
                    TEXT_SECONDARY
                )
            )

            painter.drawText(
                x + 11,
                legend_y + 3,
                label,
            )

            x += 58

    def _draw_filled_points(
        self,
        painter: QPainter,
        x,
        y,
        rect: tuple[int, int, int, int],
        color: str,
        radius: int = 2,
    ) -> None:

        finite = (
            np.isfinite(x)
            & np.isfinite(y)
        )

        if not np.any(
            finite
        ):
            return

        painter.setBrush(
            QBrush(
                QColor(
                    color
                )
            )
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        diameter = (
            radius * 2
        )

        for px, py in zip(
            x[finite],
            y[finite],
        ):

            sx = self._map_x(
                float(px),
                rect,
            )

            sy = self._map_y(
                float(py),
                rect,
            )

            painter.drawEllipse(
                int(
                    sx - radius
                ),
                int(
                    sy - radius
                ),
                diameter,
                diameter,
            )

    # ========================================================================
    # Paint
    # ========================================================================

    def paintEvent(
        self,
        event,
    ) -> None:

        del event

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        # Graph canvas itself is white.
        painter.fillRect(
            self.rect(),
            QColor(
                CARD_BACKGROUND
            ),
        )

        plot_rect = (
            self._plot_rect()
        )

        self._draw_axes(
            painter,
            plot_rect,
        )

        self._draw_legend(
            painter,
            plot_rect,
        )

        x_values = np.arange(
            1,
            256,
            dtype=np.float64,
        )

        # Red points.
        self._draw_filled_points(
            painter,
            x_values,
            self.red[1:],
            plot_rect,
            self.RED,
        )

        # Green points.
        self._draw_filled_points(
            painter,
            x_values,
            self.green[1:],
            plot_rect,
            self.GREEN,
        )

        # Blue points.
        self._draw_filled_points(
            painter,
            x_values,
            self.blue[1:],
            plot_rect,
            self.BLUE,
        )

        # Current level indicator.
        painter.setPen(
            QColor(
                TEXT_SECONDARY
            )
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                8,
            )
        )

        painter.drawText(
            8,
            self.height() - 7,
            f"Live level: {self.current_level}/255",
        )

        painter.end()


# ============================================================================
# Batch Processing page
# ============================================================================

class BatchPage(QWidget):
    """
    Batch Processing workflow page.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(
            parent
        )

        self.input_files: list[Path] = []

        self.thread: QThread | None = None
        self.worker: QtBatchWorker | None = None
        self.cancel_event: Event | None = None

        self._preview_pixmap: QPixmap | None = None

        self._live_original: np.ndarray | None = None
        self._live_mask: np.ndarray | None = None
        self._live_green: np.ndarray | None = None
        self._live_rgb: np.ndarray | None = None

        self._live_background = (
            150,
            0,
            150,
        )

        self._batch_background = (
            150,
            0,
            150,
        )

        self._log_history: list[str] = []

        self._pending_completion: tuple[
            int,
            int,
            bool,
        ] | None = None

        self._settings_visible = False

        self._build_ui()

        self._update_start_state()

    # ========================================================================
    # Main UI
    # ========================================================================

    def _build_ui(
        self,
    ) -> None:

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            20,
            12,
            20,
            12,
        )

        outer.setSpacing(
            7
        )

        # ---------------------------------------------------------------
        # Header
        # ---------------------------------------------------------------

        header_row = QHBoxLayout()

        self.back_button = QPushButton(
            "← Back"
        )

        self.back_button.setObjectName(
            "backButton"
        )

        header_row.addWidget(
            self.back_button
        )

        header_row.addSpacing(
            10
        )

        title = QLabel(
            "Canopy GSM — Batch Processing"
        )

        title.setObjectName(
            "pageTitle"
        )

        header_row.addWidget(
            title
        )

        header_row.addStretch()

        outer.addLayout(
            header_row
        )

        description = QLabel(
            "Process multiple supported RGB images while observing "
            "the progressive image and GSM graph in real time."
        )

        description.setObjectName(
            "pageDescription"
        )

        description.setWordWrap(
            True
        )

        outer.addWidget(
            description
        )

        # ---------------------------------------------------------------
        # Compact control bar
        # ---------------------------------------------------------------

        control_frame = QFrame()

        control_frame.setObjectName(
            "controlFrame"
        )

        control_layout = QHBoxLayout(
            control_frame
        )

        control_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        control_layout.setSpacing(
            6
        )

        input_label = QLabel(
            "Input:"
        )

        input_label.setObjectName(
            "compactLabel"
        )

        control_layout.addWidget(
            input_label
        )

        self.input_edit = QLineEdit()

        self.input_edit.setReadOnly(
            True
        )

        self.input_edit.setPlaceholderText(
            "Select input folder..."
        )

        self.input_edit.setMinimumWidth(
            160
        )

        control_layout.addWidget(
            self.input_edit,
            2,
        )

        self.input_browse = QPushButton(
            "Browse"
        )

        self.input_browse.setObjectName(
            "secondaryButton"
        )

        self.input_browse.clicked.connect(
            self._choose_input_folder
        )

        control_layout.addWidget(
            self.input_browse
        )

        separator = QLabel(
            "│"
        )

        separator.setObjectName(
            "separatorLabel"
        )

        control_layout.addWidget(
            separator
        )

        output_label = QLabel(
            "Output:"
        )

        output_label.setObjectName(
            "compactLabel"
        )

        control_layout.addWidget(
            output_label
        )

        self.output_edit = QLineEdit()

        self.output_edit.setPlaceholderText(
            "Select output folder..."
        )

        self.output_edit.setMinimumWidth(
            160
        )

        control_layout.addWidget(
            self.output_edit,
            2,
        )

        self.output_browse = QPushButton(
            "Browse"
        )

        self.output_browse.setObjectName(
            "secondaryButton"
        )

        self.output_browse.clicked.connect(
            self._choose_output_folder
        )

        control_layout.addWidget(
            self.output_browse
        )

        self.settings_button = QPushButton(
            "⚙ Settings ▼"
        )

        self.settings_button.setObjectName(
            "secondaryButton"
        )

        self.settings_button.setCheckable(
            True
        )

        self.settings_button.clicked.connect(
            self._toggle_settings
        )

        control_layout.addWidget(
            self.settings_button
        )

        self.start_button = QPushButton(
            "Start Batch"
        )

        self.start_button.setObjectName(
            "startButton"
        )

        self.start_button.clicked.connect(
            self._start_batch
        )

        control_layout.addWidget(
            self.start_button
        )

        self.stop_button = QPushButton(
            "Stop"
        )

        self.stop_button.setObjectName(
            "dangerButton"
        )

        self.stop_button.setEnabled(
            False
        )

        self.stop_button.clicked.connect(
            self._stop_batch
        )

        control_layout.addWidget(
            self.stop_button
        )

        outer.addWidget(
            control_frame
        )

        # ---------------------------------------------------------------
        # Collapsible settings
        # ---------------------------------------------------------------

        self.settings_scroll = QScrollArea()

        self.settings_scroll.setObjectName(
            "settingsScroll"
        )

        self.settings_scroll.setWidgetResizable(
            True
        )

        self.settings_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.settings_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.settings_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.settings_scroll.setMaximumHeight(
            230
        )

        self.settings_scroll.setVisible(
            False
        )

        settings_content = QWidget()

        settings_layout = QHBoxLayout(
            settings_content
        )

        settings_layout.setContentsMargins(
            2,
            2,
            2,
            2,
        )

        settings_layout.setSpacing(
            8
        )

        settings_layout.addWidget(
            self._build_settings_left(),
            1,
        )

        settings_layout.addWidget(
            self._build_settings_right(),
            1,
        )

        self.settings_scroll.setWidget(
            settings_content
        )

        outer.addWidget(
            self.settings_scroll
        )

        # ---------------------------------------------------------------
        # Main visualization
        # ---------------------------------------------------------------

        self.live_splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.live_splitter.setChildrenCollapsible(
            False
        )

        self.live_splitter.setObjectName(
            "liveSplitter"
        )

        self.live_panel = (
            self._build_visual_panel(
                "Live Processed Image"
            )
        )

        self.graph_panel = (
            self._build_visual_panel(
                "Live GSM Graph"
            )
        )

        self.live_splitter.addWidget(
            self.live_panel
        )

        self.live_splitter.addWidget(
            self.graph_panel
        )

        self.live_splitter.setStretchFactor(
            0,
            1,
        )

        self.live_splitter.setStretchFactor(
            1,
            1,
        )

        outer.addWidget(
            self.live_splitter,
            1,
        )

        # ---------------------------------------------------------------
        # Live status
        # ---------------------------------------------------------------

        status_frame = QFrame()

        status_frame.setObjectName(
            "statusFrame"
        )

        status_layout = QHBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            10,
            6,
            10,
            6,
        )

        status_layout.setSpacing(
            16
        )

        self.live_level_label = QLabel(
            "Green level: 0 / 255"
        )

        self.live_level_label.setObjectName(
            "liveMetric"
        )

        self.live_pixel_label = QLabel(
            "Pixels at level: —"
        )

        self.live_pixel_label.setObjectName(
            "liveMetric"
        )

        self.live_stage_label = QLabel(
            "Waiting for Batch Processing."
        )

        self.live_stage_label.setObjectName(
            "mutedLabel"
        )

        status_layout.addWidget(
            self.live_level_label
        )

        status_layout.addWidget(
            self.live_pixel_label
        )

        status_layout.addWidget(
            self.live_stage_label,
            1,
        )

        outer.addWidget(
            status_frame
        )

        # ---------------------------------------------------------------
        # Progress
        # ---------------------------------------------------------------

        progress_frame = QFrame()

        progress_frame.setObjectName(
            "progressFrame"
        )

        progress_layout = QVBoxLayout(
            progress_frame
        )

        progress_layout.setContentsMargins(
            8,
            4,
            8,
            4,
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        progress_layout.addWidget(
            self.progress_bar
        )

        outer.addWidget(
            progress_frame
        )

        # ---------------------------------------------------------------
        # Compact log
        # ---------------------------------------------------------------

        log_header = QHBoxLayout()

        log_title = QLabel(
            "Batch Log"
        )

        log_title.setObjectName(
            "sectionTitle"
        )

        log_header.addWidget(
            log_title
        )

        log_header.addStretch()

        self.view_log_button = QPushButton(
            "View Full Log"
        )

        self.view_log_button.setObjectName(
            "secondaryButton"
        )

        self.view_log_button.clicked.connect(
            self._show_full_log
        )

        log_header.addWidget(
            self.view_log_button
        )

        outer.addLayout(
            log_header
        )

        self.log_output = QPlainTextEdit()

        self.log_output.setObjectName(
            "batchLog"
        )

        self.log_output.setReadOnly(
            True
        )

        self.log_output.setFixedHeight(
            44
        )

        self.log_output.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.log_output.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        outer.addWidget(
            self.log_output
        )

        self._apply_style()

    # ========================================================================
    # Settings builders
    # ========================================================================

    def _build_settings_left(
        self,
    ) -> QWidget:

        panel = QFrame()

        panel.setObjectName(
            "settingsCard"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            6
        )

        # ---------------------------------------------------------------
        # ST1
        # ---------------------------------------------------------------

        st1_group = QGroupBox(
            "ST1 Vegetation Segmentation"
        )

        st1_layout = QVBoxLayout(
            st1_group
        )

        st1_layout.setContentsMargins(
            8,
            7,
            8,
            7,
        )

        st1_layout.setSpacing(
            4
        )

        self.st1_combo = QComboBox()

        self.st1_combo.addItem(
            "G > R",
            "G>R",
        )

        self.st1_combo.addItem(
            "G > R  &  G > B",
            "G>R&G>B",
        )

        self.st1_combo.addItem(
            "2G − R − B > 0",
            "2G-R-B>0",
        )

        self.st1_combo.addItem(
            "HSV",
            "HSV",
        )

        self.st1_combo.addItem(
            "Custom Python segmentation",
            "CUSTOM",
        )

        self.st1_combo.currentIndexChanged.connect(
            self._update_st1_controls
        )

        st1_layout.addWidget(
            self.st1_combo
        )

        # ---------------------------------------------------------------
        # HSV
        # ---------------------------------------------------------------

        self.hsv_group = QGroupBox(
            "HSV parameters"
        )

        hsv_form = QFormLayout(
            self.hsv_group
        )

        hsv_form.setContentsMargins(
            8,
            5,
            8,
            5,
        )

        hsv_form.setHorizontalSpacing(
            10
        )

        hsv_form.setVerticalSpacing(
            2
        )

        self.h_min = QSpinBox()
        self.h_max = QSpinBox()
        self.s_min = QSpinBox()
        self.s_max = QSpinBox()
        self.v_min = QSpinBox()
        self.v_max = QSpinBox()

        self.h_min.setRange(0, 179)
        self.h_max.setRange(0, 179)
        self.s_min.setRange(0, 255)
        self.s_max.setRange(0, 255)
        self.v_min.setRange(0, 255)
        self.v_max.setRange(0, 255)

        self.h_min.setValue(25)
        self.h_max.setValue(95)
        self.s_min.setValue(40)
        self.s_max.setValue(255)
        self.v_min.setValue(30)
        self.v_max.setValue(255)

        hsv_form.addRow(
            "H min",
            self.h_min,
        )

        hsv_form.addRow(
            "H max",
            self.h_max,
        )

        hsv_form.addRow(
            "S min",
            self.s_min,
        )

        hsv_form.addRow(
            "S max",
            self.s_max,
        )

        hsv_form.addRow(
            "V min",
            self.v_min,
        )

        hsv_form.addRow(
            "V max",
            self.v_max,
        )

        st1_layout.addWidget(
            self.hsv_group
        )

        # ---------------------------------------------------------------
        # Custom ST1
        # ---------------------------------------------------------------

        self.custom_group = QGroupBox(
            "Custom ST1"
        )

        custom_layout = QHBoxLayout(
            self.custom_group
        )

        custom_layout.setContentsMargins(
            8,
            5,
            8,
            5,
        )

        custom_layout.setSpacing(
            5
        )

        self.custom_edit = QLineEdit()

        self.custom_edit.setReadOnly(
            True
        )

        self.custom_edit.setPlaceholderText(
            "Python file defining create_mask(image)"
        )

        custom_button = QPushButton(
            "Browse"
        )

        custom_button.setObjectName(
            "secondaryButton"
        )

        custom_button.clicked.connect(
            self._choose_custom_st1
        )

        custom_layout.addWidget(
            self.custom_edit,
            1,
        )

        custom_layout.addWidget(
            custom_button
        )

        st1_layout.addWidget(
            self.custom_group
        )

        layout.addWidget(
            st1_group
        )

        # ---------------------------------------------------------------
        # ST3
        # ---------------------------------------------------------------

        st3_group = QGroupBox(
            "ST3 parameters"
        )

        st3_form = QFormLayout(
            st3_group
        )

        st3_form.setContentsMargins(
            8,
            5,
            8,
            5,
        )

        st3_form.setVerticalSpacing(
            2
        )

        self.st3_m = QSpinBox()
        self.st3_p = QSpinBox()

        self.st3_m.setRange(
            0,
            1000,
        )

        self.st3_p.setRange(
            0,
            1000,
        )

        self.st3_m.setValue(
            12
        )

        self.st3_p.setValue(
            50
        )

        st3_form.addRow(
            "St3_m",
            self.st3_m,
        )

        st3_form.addRow(
            "St3_P",
            self.st3_p,
        )

        layout.addWidget(
            st3_group
        )

        # ---------------------------------------------------------------
        # Background
        # ---------------------------------------------------------------

        background_group = QGroupBox(
            "Processed-image background"
        )

        background_layout = QVBoxLayout(
            background_group
        )

        background_layout.setContentsMargins(
            8,
            5,
            8,
            5,
        )

        background_layout.setSpacing(
            4
        )

        self.background_combo = QComboBox()

        self.background_combo.addItem(
            "Purple (150, 0, 150)",
            (150, 0, 150),
        )

        self.background_combo.addItem(
            "White (255, 255, 255)",
            (255, 255, 255),
        )

        self.background_combo.addItem(
            "Black (0, 0, 0)",
            (0, 0, 0),
        )

        self.background_combo.addItem(
            "Gray (128, 128, 128)",
            (128, 128, 128),
        )

        self.background_combo.addItem(
            "Custom HEX",
            None,
        )

        self.background_combo.currentIndexChanged.connect(
            self._update_background_controls
        )

        background_layout.addWidget(
            self.background_combo
        )

        background_hex_row = QHBoxLayout()

        self.custom_hex_edit = QLineEdit(
            "#960096"
        )

        self.custom_hex_edit.setEnabled(
            False
        )

        self.custom_hex_edit.textChanged.connect(
            self._update_background_preview_from_text
        )

        self.background_preview = QLabel()

        self.background_preview.setFixedSize(
            44,
            24,
        )

        background_hex_row.addWidget(
            self.custom_hex_edit,
            1,
        )

        background_hex_row.addWidget(
            self.background_preview
        )

        background_layout.addLayout(
            background_hex_row
        )

        layout.addWidget(
            background_group
        )

        self._update_st1_controls()
        self._update_background_controls()

        return panel

    def _build_settings_right(
        self,
    ) -> QWidget:

        panel = QFrame()

        panel.setObjectName(
            "settingsCard"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            6
        )

        options_group = QGroupBox(
            "Output options"
        )

        options_layout = QVBoxLayout(
            options_group
        )

        options_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        options_layout.setSpacing(
            4
        )

        self.save_processed_check = QCheckBox(
            "Save processed RGB images"
        )

        self.save_processed_check.setChecked(
            True
        )

        options_layout.addWidget(
            self.save_processed_check
        )

        format_row = QHBoxLayout()

        format_row.addWidget(
            QLabel(
                "Processed image format:"
            )
        )

        self.processed_format_combo = QComboBox()

        self.processed_format_combo.addItem(
            "PNG — Recommended",
            "png",
        )

        self.processed_format_combo.addItem(
            "JPEG — MATLAB v2.1 compatible",
            "jpg",
        )

        format_row.addWidget(
            self.processed_format_combo,
            1,
        )

        options_layout.addLayout(
            format_row
        )

        self.save_graphs_check = QCheckBox(
            "Save GSM graph PDFs"
        )

        self.save_graphs_check.setChecked(
            True
        )

        options_layout.addWidget(
            self.save_graphs_check
        )

        layout.addWidget(
            options_group
        )

        layout.addStretch()

        return panel

    # ========================================================================
    # Visual panels
    # ========================================================================

    def _build_visual_panel(
        self,
        title: str,
    ) -> QWidget:

        panel = QGroupBox(
            title
        )

        panel.setObjectName(
            "visualPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            8,
            12,
            8,
            8,
        )

        layout.setSpacing(
            4
        )

        if title == "Live Processed Image":

            self.live_image_label = QLabel(
                "Ready for Batch Processing."
            )

            self.live_image_label.setObjectName(
                "liveImageLabel"
            )

            self.live_image_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.live_image_label.setMinimumSize(
                280,
                280,
            )

            self.live_image_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            widget = self.live_image_label

        else:

            self.graph_widget = GSMGraphWidget()

            widget = self.graph_widget

        layout.addWidget(
            widget,
            1,
        )

        return panel

    # ========================================================================
    # Styling
    # ========================================================================

    def _apply_style(
        self,
    ) -> None:

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {WINDOW_BACKGROUND};
                color: {TEXT_PRIMARY};
                font-family: "Segoe UI";
            }}

            QLabel#pageTitle {{
                font-size: 23px;
                font-weight: 700;
                color: {TEXT_PRIMARY};
            }}

            QLabel#pageDescription {{
                font-size: 12px;
                color: {TEXT_SECONDARY};
            }}

            QLabel#compactLabel {{
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-size: 12px;
            }}

            QLabel#separatorLabel {{
                color: {BORDER};
            }}

            QLabel#sectionTitle {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
            }}

            QLabel#liveMetric {{
                color: {EPL_GREEN};
                font-weight: 700;
                font-size: 12px;
            }}

            QLabel#mutedLabel {{
                color: {TEXT_SECONDARY};
                font-size: 11px;
            }}

            QLabel#liveImageLabel {{
                background: {LIVE_IMAGE_BACKGROUND};
                border: none;
                border-radius: 0px;
            }}

            QFrame#controlFrame,
            QFrame#statusFrame,
            QFrame#settingsCard {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}

            QScrollArea#settingsScroll {{
                background: {WINDOW_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}

            QGroupBox#visualPanel {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 9px;
                margin-top: 7px;
                padding-top: 8px;
                font-weight: 700;
            }}

            QGroupBox#visualPanel::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                background: {CARD_BACKGROUND};
            }}

            QGroupBox {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 7px;
                margin-top: 7px;
                padding-top: 7px;
                font-size: 11px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 9px;
                padding: 0 4px;
                background: {CARD_BACKGROUND};
            }}

            QLineEdit,
            QComboBox,
            QSpinBox {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 4px 7px;
                min-height: 24px;
                color: {TEXT_PRIMARY};
            }}

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus {{
                border: 2px solid {EPL_GREEN};
            }}

            QPushButton {{
                background: white;
                color: {EPL_GREEN};
                border: 1px solid {EPL_GREEN};
                border-radius: 6px;
                padding: 6px 11px;
                font-size: 12px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: #eef3eb;
            }}

            QPushButton#startButton {{
                background: {EPL_GREEN};
                color: white;
                border: none;
                padding: 7px 14px;
                font-weight: 700;
            }}

            QPushButton#startButton:hover {{
                background: #496f32;
            }}

            QPushButton#startButton:disabled {{
                background: #aeb8a8;
            }}

            QPushButton#dangerButton {{
                color: #a42f2f;
                border-color: #a42f2f;
            }}

            QPushButton#dangerButton:hover {{
                background: #f8eeee;
            }}

            QPushButton#dangerButton:disabled {{
                color: #a9aaa9;
                border-color: #c9cbc9;
            }}

            QPushButton#secondaryButton {{
                padding-left: 9px;
                padding-right: 9px;
            }}

            QPushButton#backButton {{
                padding-left: 8px;
                padding-right: 8px;
            }}

            QCheckBox {{
                color: {TEXT_PRIMARY};
                spacing: 5px;
            }}

            QProgressBar {{
                background: #e9ece7;
                border: 1px solid {BORDER};
                border-radius: 5px;
                text-align: center;
                min-height: 16px;
            }}

            QProgressBar::chunk {{
                background: {EPL_GREEN};
                border-radius: 4px;
            }}

            QPlainTextEdit#batchLog {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-family: Consolas, "Courier New";
                font-size: 10px;
            }}
            """
        )

    # ========================================================================
    # Input folder
    # ========================================================================

    def _choose_input_folder(
        self,
    ) -> None:

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Image Folder",
        )

        if folder:

            self._set_input_folder(
                Path(folder)
            )

    def _set_input_folder(
        self,
        folder: Path,
    ) -> None:

        try:

            files = find_image_files(
                folder
            )

        except GSMInputError as exc:

            self.input_files = []

            self.input_edit.clear()

            self._clear_input_preview()

            self._show_error(
                "Invalid Input Folder",
                str(exc),
            )

            self._update_start_state()

            return

        self.input_files = files

        self.input_edit.setText(
            str(folder)
        )

        if files:

            self._load_first_input_preview(
                files[0]
            )

        else:

            self._clear_input_preview()

        default_output = (
            folder
            / "CanopyGSM_Output"
        )

        self.output_edit.setText(
            str(default_output)
        )

        self._update_start_state()

    # ========================================================================
    # Input preview
    # ========================================================================

    def _load_first_input_preview(
        self,
        image_path: Path,
    ) -> None:

        try:

            image = load_rgb_uint8(
                image_path
            )

            image = np.ascontiguousarray(
                image,
                dtype=np.uint8,
            )

            height, width = (
                image.shape[:2]
            )

            qimage = QImage(
                image.data,
                width,
                height,
                width * 3,
                QImage.Format.Format_RGB888,
            ).copy()

            self._preview_pixmap = (
                QPixmap.fromImage(
                    qimage
                )
            )

            self._render_input_preview()

            self.live_stage_label.setText(
                f"Ready — preview: {image_path.name}  "
                f"({width} × {height} pixels)"
            )

        except Exception as exc:

            self._preview_pixmap = None

            self.live_image_label.clear()

            self.live_image_label.setText(
                "Preview unavailable."
            )

            self.live_stage_label.setText(
                f"Preview unavailable: {exc}"
            )

    def _clear_input_preview(
        self,
    ) -> None:

        self._preview_pixmap = None

        if self._live_rgb is None:

            self.live_image_label.clear()

            self.live_image_label.setText(
                "Ready for Batch Processing."
            )

    def _render_input_preview(
        self,
    ) -> None:

        if (
            self._preview_pixmap is None
            or self._live_rgb is not None
        ):
            return

        available_width = max(
            180,
            self.live_image_label.width() - 14,
        )

        available_height = max(
            180,
            self.live_image_label.height() - 14,
        )

        scaled = self._preview_pixmap.scaled(
            available_width,
            available_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # White background around the displayed image.
        self.live_image_label.setStyleSheet(
            f"""
            QLabel#liveImageLabel {{
                background: {LIVE_IMAGE_BACKGROUND};
                border: none;
                border-radius: 0px;
            }}
            """
        )

        self.live_image_label.setPixmap(
            scaled
        )

    # ========================================================================
    # Output folder
    # ========================================================================

    def _choose_output_folder(
        self,
    ) -> None:

        current = (
            self.output_edit
            .text()
            .strip()
        )

        start = (
            current
            if current
            else str(
                Path.home()
            )
        )

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            start,
        )

        if folder:

            self.output_edit.setText(
                folder
            )

        self._update_start_state()

    # ========================================================================
    # Custom ST1
    # ========================================================================

    def _choose_custom_st1(
        self,
    ) -> None:

        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Select Custom ST1 Python File",
                "",
                "Python files (*.py)",
            )
        )

        if file_path:

            self.custom_edit.setText(
                file_path
            )

    # ========================================================================
    # ST1 controls
    # ========================================================================

    def _update_st1_controls(
        self,
    ) -> None:

        method = (
            self.st1_combo.currentData()
        )

        self.hsv_group.setVisible(
            method == "HSV"
        )

        self.custom_group.setVisible(
            method == "CUSTOM"
        )

    # ========================================================================
    # Background controls
    # ========================================================================

    def _update_background_controls(
        self,
    ) -> None:

        custom = (
            self.background_combo.currentData()
            is None
        )

        self.custom_hex_edit.setEnabled(
            custom
        )

        if not custom:

            rgb = (
                self.background_combo.currentData()
            )

            self._set_background_preview(
                rgb
            )

        else:

            self._update_background_preview_from_text()

    def _update_background_preview_from_text(
        self,
        *_args,
    ) -> None:

        if (
            self.background_combo.currentData()
            is not None
        ):
            return

        try:

            rgb = hex_to_rgb(
                self.custom_hex_edit.text()
            )

            self._set_background_preview(
                rgb
            )

        except GSMInputError:

            self._set_background_preview(
                (200, 200, 200)
            )

    def _set_background_preview(
        self,
        rgb: tuple[int, int, int],
    ) -> None:

        r, g, b = rgb

        self.background_preview.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgb({r}, {g}, {b});
                border: 1px solid #909690;
                border-radius: 4px;
            }}
            """
        )

    def _get_background_rgb(
        self,
    ) -> tuple[int, int, int]:

        data = (
            self.background_combo.currentData()
        )

        if data is not None:

            return tuple(
                int(v)
                for v in data
            )

        return hex_to_rgb(
            self.custom_hex_edit.text()
        )

    # ========================================================================
    # ST1 configuration
    # ========================================================================

    def _build_st1_config(
        self,
    ) -> ST1Config:

        method = (
            self.st1_combo.currentData()
        )

        if method == "CUSTOM":

            custom_path_text = (
                self.custom_edit.text().strip()
            )

            if not custom_path_text:

                raise GSMInputError(
                    "Please select a Custom ST1 Python file."
                )

            custom_path = Path(
                custom_path_text
            )

            if not custom_path.is_file():

                raise GSMInputError(
                    "The selected Custom ST1 file does not exist."
                )

        else:

            custom_path = None

        return ST1Config(
            method=str(
                method
            ),
            hsv_h_min=self.h_min.value(),
            hsv_h_max=self.h_max.value(),
            hsv_s_min=self.s_min.value(),
            hsv_s_max=self.s_max.value(),
            hsv_v_min=self.v_min.value(),
            hsv_v_max=self.v_max.value(),
            custom_path=custom_path,
        )

    # ========================================================================
    # Settings toggle
    # ========================================================================

    def _toggle_settings(
        self,
        checked: bool,
    ) -> None:

        self._settings_visible = bool(
            checked
        )

        self.settings_scroll.setVisible(
            self._settings_visible
        )

        self.settings_button.setText(
            "⚙ Settings ▲"
            if self._settings_visible
            else "⚙ Settings ▼"
        )

    # ========================================================================
    # Run state
    # ========================================================================

    def _update_start_state(
        self,
    ) -> None:

        running = (
            self.thread is not None
            and self.thread.isRunning()
        )

        ready = (
            bool(
                self.input_files
            )
            and bool(
                self.output_edit
                .text()
                .strip()
            )
        )

        self.start_button.setEnabled(
            ready
            and not running
        )

        self.stop_button.setEnabled(
            running
        )

        for widget in (
            self.input_browse,
            self.output_browse,
            self.settings_button,
        ):

            widget.setEnabled(
                not running
            )

    # ========================================================================
    # Start Batch
    # ========================================================================

    def _start_batch(
        self,
    ) -> None:

        if not self.input_files:

            self._show_error(
                "No Images",
                (
                    "Please select a folder containing "
                    "supported RGB image files."
                ),
            )

            return

        output_text = (
            self.output_edit
            .text()
            .strip()
        )

        if not output_text:

            self._show_error(
                "No Output Folder",
                "Please select an output folder.",
            )

            return

        try:

            st1_config = (
                self._build_st1_config()
            )

            background_rgb = (
                self._get_background_rgb()
            )

            output_root = Path(
                output_text
            )

            output_root.mkdir(
                parents=True,
                exist_ok=True,
            )

        except Exception as exc:

            self._show_error(
                "Invalid Batch Settings",
                str(exc),
            )

            return

        # ---------------------------------------------------------------
        # Existing output warning
        # ---------------------------------------------------------------

        results_dir = (
            output_root
            / "Results"
        )

        processed_dir = (
            output_root
            / "Processed images"
        )

        graphs_dir = (
            output_root
            / "Graphs"
        )

        existing_output = (
            results_dir.is_dir()
            and any(
                results_dir.iterdir()
            )
        ) or (
            processed_dir.is_dir()
            and any(
                processed_dir.iterdir()
            )
        ) or (
            graphs_dir.is_dir()
            and any(
                graphs_dir.iterdir()
            )
        )

        if existing_output:

            answer = QMessageBox.question(
                self,
                "Existing Output",
                (
                    "The selected output folder already "
                    "contains Canopy GSM output files.\n\n"
                    "Files with the same names may be overwritten.\n\n"
                    "Continue?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )

            if (
                answer
                != QMessageBox.StandardButton.Yes
            ):
                return

        processed_image_format = (
            self.processed_format_combo.currentData()
        )

        if processed_image_format not in {
            "png",
            "jpg",
        }:

            self._show_error(
                "Invalid Output Format",
                "Please select PNG or JPEG.",
            )

            return

        # ---------------------------------------------------------------
        # Batch configuration
        # ---------------------------------------------------------------

        config = BatchConfig(
            input_files=list(
                self.input_files
            ),
            output_root=output_root,
            st1_config=st1_config,
            st3_m=self.st3_m.value(),
            st3_p=self.st3_p.value(),
            background_rgb=background_rgb,
            save_processed_images=(
                self.save_processed_check.isChecked()
            ),
            processed_image_format=str(
                processed_image_format
            ),
            jpeg_quality=75,
            save_graphs=(
                self.save_graphs_check.isChecked()
            ),
        )

        self.settings_button.setChecked(False)
        self._toggle_settings(False)

        self._batch_background = tuple(
            int(v)
            for v in background_rgb
        )

        # ---------------------------------------------------------------
        # Reset UI
        # ---------------------------------------------------------------

        self.progress_bar.setValue(
            0
        )

        self.live_level_label.setText(
            "Green level: 0 / 255"
        )

        self.live_pixel_label.setText(
            "Pixels at level: —"
        )

        self.live_stage_label.setText(
            "Starting Batch Processing..."
        )

        self.graph_widget.reset()

        self._clear_live_processed_image(
            restore_preview=False
        )

        self._log_history = []

        self._refresh_compact_log()

        self._pending_completion = None

        # ---------------------------------------------------------------
        # Cancellation
        # ---------------------------------------------------------------

        self.cancel_event = Event()

        # ---------------------------------------------------------------
        # Thread
        # ---------------------------------------------------------------

        self.thread = QThread(
            self
        )

        self.worker = QtBatchWorker(
            config=config,
            cancel_event=self.cancel_event,
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.progress_bar.setValue
        )

        self.worker.image_started.connect(
            self._on_image_started
        )

        self.worker.image_finished.connect(
            self._on_image_finished
        )

        self.worker.log.connect(
            self._append_log
        )

        self.worker.live_initialized.connect(
            self._on_live_initialized
        )

        self.worker.live_level.connect(
            self._on_live_level
        )

        self.worker.finished.connect(
            self._on_batch_finished
        )

        self.worker.fatal_error.connect(
            self._on_fatal_error
        )

        # Thread shutdown
        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.fatal_error.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.fatal_error.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self._on_thread_finished
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self._update_start_state()

        self.thread.start()

    # ========================================================================
    # Stop Batch
    # ========================================================================

    def _stop_batch(
        self,
    ) -> None:

        if self.cancel_event is None:
            return

        if (
            self.thread is None
            or not self.thread.isRunning()
        ):
            return

        answer = QMessageBox.question(
            self,
            "Stop Batch",
            (
                "Stop the current Batch Processing run?\n\n"
                "The current image may stop at its next "
                "GSM processing checkpoint."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.cancel_event.set()

        self.live_stage_label.setText(
            "Stopping Batch..."
        )

        self.stop_button.setEnabled(
            False
        )

    # ========================================================================
    # Worker callbacks
    # ========================================================================

    @Slot(
        int,
        int,
        str,
    )
    def _on_image_started(
        self,
        index: int,
        total: int,
        name: str,
    ) -> None:

        self.live_stage_label.setText(
            f"Processing image {index}/{total}: {name}"
        )

        self.live_level_label.setText(
            "Green level: 0 / 255"
        )

        self.live_pixel_label.setText(
            "Pixels at level: —"
        )

        self.graph_widget.reset()

        self._show_solid_live_background()

    @Slot(
        object,
        object,
        object,
        object,
        str,
    )
    def _on_live_initialized(
        self,
        preview_rgb,
        preview_mask,
        preview_green,
        background_rgb,
        image_name: str,
    ) -> None:

        self._live_original = np.ascontiguousarray(
            preview_rgb,
            dtype=np.uint8,
        )

        self._live_mask = np.asarray(
            preview_mask,
            dtype=bool,
        )

        self._live_green = np.asarray(
            preview_green,
            dtype=np.uint8,
        )

        self._live_background = tuple(
            int(v)
            for v in background_rgb
        )

        # Entire image starts as background.
        self._live_rgb = np.empty_like(
            self._live_original,
            dtype=np.uint8,
        )

        self._live_rgb[:, :] = np.asarray(
            self._live_background,
            dtype=np.uint8,
        )

        self._render_live_processed()

        self.graph_widget.reset()

        self.live_level_label.setText(
            "Green level: 0 / 255"
        )

        self.live_pixel_label.setText(
            "Pixels at level: 0"
        )

        self.live_stage_label.setText(
            f"ST1 complete — progressive ST2 visualization: "
            f"{image_name}"
        )

    @Slot(
        int,
        float,
        float,
        int,
    )
    def _on_live_level(
        self,
        level: int,
        red_mean: float,
        blue_mean: float,
        count: int,
    ) -> None:

        level = int(level)

        if (
            self._live_rgb is not None
            and self._live_mask is not None
            and self._live_green is not None
            and self._live_original is not None
        ):

            new_pixels = (
                self._live_mask
                & (
                    self._live_green
                    == level
                )
            )

            if np.any(
                new_pixels
            ):

                self._live_rgb[
                    new_pixels
                ] = self._live_original[
                    new_pixels
                ]

                # Mirror MATLAB ChangeBackColor behavior for display only.
                for channel, background_value in enumerate(
                    self._live_background
                ):

                    if background_value != 0:

                        channel_data = (
                            self._live_rgb[
                                :,
                                :,
                                channel,
                            ]
                        )

                        zero_indices = (
                            new_pixels
                            & (
                                channel_data == 0
                            )
                        )

                        channel_data[
                            zero_indices
                        ] = background_value

                self._render_live_processed()

        self.graph_widget.add_level(
            level,
            red_mean,
            blue_mean,
            count,
        )

        self.live_level_label.setText(
            f"Green level: {level} / 255"
        )

        self.live_pixel_label.setText(
            f"Pixels at level: {count:,}"
        )

        self.live_stage_label.setText(
            f"ST2 — Green level {level}"
        )

    @Slot(
        int,
        int,
        str,
        float,
        str,
    )
    def _on_image_finished(
        self,
        index: int,
        total: int,
        status: str,
        duration: float,
        message: str,
    ) -> None:

        del duration
        del message

        if status == "OK":

            self.live_stage_label.setText(
                f"Image {index}/{total} complete"
            )

        elif status == "ERROR":

            self.live_stage_label.setText(
                f"Error in image {index}/{total}"
            )

        elif status == "CANCELLED":

            self.live_stage_label.setText(
                f"Cancelled at image {index}/{total}"
            )

    @Slot(str)
    def _append_log(
        self,
        message: str,
    ) -> None:

        self._log_history.append(
            message
        )

        self._refresh_compact_log()

    def _refresh_compact_log(
        self,
    ) -> None:

        visible = [
            line
            for line in self._log_history
            if line.strip()
        ]

        self.log_output.setPlainText(
            "\n".join(
                visible[-2:]
            )
        )

    @Slot(
        int,
        int,
        bool,
    )
    def _on_batch_finished(
        self,
        total: int,
        successful: int,
        cancelled: bool,
    ) -> None:

        self._pending_completion = (
            total,
            successful,
            cancelled,
        )

        if cancelled:

            self.live_stage_label.setText(
                "Batch cancelled."
            )

        elif successful == total:

            self.progress_bar.setValue(
                100
            )

            self.live_stage_label.setText(
                "Batch completed successfully."
            )

        else:

            self.live_stage_label.setText(
                "Batch completed with errors."
            )

    @Slot(str)
    def _on_fatal_error(
        self,
        message: str,
    ) -> None:

        self.live_stage_label.setText(
            "Batch failed."
        )

        self._append_log(
            f"FATAL ERROR: {message}"
        )

        self._show_error(
            "Batch Processing Error",
            message,
        )

    @Slot()
    def _on_thread_finished(
        self,
    ) -> None:

        self.thread = None
        self.worker = None
        self.cancel_event = None

        self._update_start_state()

        if self._pending_completion is not None:

            total, successful, cancelled = (
                self._pending_completion
            )

            self._pending_completion = None

            self._show_completion_message(
                total,
                successful,
                cancelled,
            )

    # ========================================================================
    # Live image rendering
    # ========================================================================

    def _show_solid_live_background(
        self,
    ) -> None:
        """
        Prepare the live image area for the next image.

        The actual full-size Purple image is created immediately after
        live initialization. The surrounding area remains white.
        """

        self.live_image_label.clear()

        self.live_image_label.setStyleSheet(
            f"""
            QLabel#liveImageLabel {{
                background: {LIVE_IMAGE_BACKGROUND};
                border: none;
                border-radius: 0px;
            }}
            """
        )

        self.live_image_label.setText(
            "Preparing image..."
        )

    def _render_live_processed(
        self,
    ) -> None:

        if self._live_rgb is None:
            return

        self._set_label_from_rgb(
            self.live_image_label,
            self._live_rgb,
        )

    def _clear_live_processed_image(
        self,
        restore_preview: bool = True,
    ) -> None:

        self._live_original = None
        self._live_mask = None
        self._live_green = None
        self._live_rgb = None

        self.live_image_label.clear()

        if (
            restore_preview
            and self._preview_pixmap is not None
        ):

            self._render_input_preview()

        else:

            self.live_image_label.setStyleSheet(
                f"""
                QLabel#liveImageLabel {{
                    background: {LIVE_IMAGE_BACKGROUND};
                    border: none;
                    border-radius: 0px;
                }}
                """
            )

            self.live_image_label.setText(
                "Ready for Batch Processing."
            )

    def _set_label_from_rgb(
        self,
        label: QLabel,
        rgb_image: np.ndarray,
    ) -> None:

        image = np.ascontiguousarray(
            rgb_image,
            dtype=np.uint8,
        )

        height, width = (
            image.shape[:2]
        )

        qimage = QImage(
            image.data,
            width,
            height,
            width * 3,
            QImage.Format.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(
            qimage
        )

        available_width = max(
            180,
            label.width() - 14,
        )

        available_height = max(
            180,
            label.height() - 14,
        )

        scaled = pixmap.scaled(
            available_width,
            available_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        label.setStyleSheet(
            f"""
            QLabel#liveImageLabel {{
                background: {LIVE_IMAGE_BACKGROUND};
                border: none;
                border-radius: 0px;
            }}
            """
        )

        label.setPixmap(
            scaled
        )

    # ========================================================================
    # Resize / responsive layout
    # ========================================================================

    def resizeEvent(
        self,
        event,
    ) -> None:

        super().resizeEvent(
            event
        )

        if self.width() < 1080:

            new_orientation = (
                Qt.Orientation.Vertical
            )

        else:

            new_orientation = (
                Qt.Orientation.Horizontal
            )

        if (
            self.live_splitter.orientation()
            != new_orientation
        ):

            self.live_splitter.setOrientation(
                new_orientation
            )

        if self._live_rgb is not None:

            self._render_live_processed()

        else:

            self._render_input_preview()

        self.graph_widget.update()

    # ========================================================================
    # Full log
    # ========================================================================

    def _show_full_log(
        self,
    ) -> None:

        dialog = QMessageBox(
            self
        )

        dialog.setWindowTitle(
            "Canopy GSM — Full Batch Log"
        )

        dialog.setIcon(
            QMessageBox.Icon.Information
        )

        log_text = (
            "\n".join(
                self._log_history
            )
            if self._log_history
            else "No log entries yet."
        )

        dialog.setText(
            "The complete processing log is also saved as the "
            "CanopyGSM_Batch_*.log file in the output folder."
        )

        dialog.setDetailedText(
            log_text
        )

        window = self.window()

        if window is not None:

            dialog.setWindowIcon(
                window.windowIcon()
            )

        dialog.exec()

    # ========================================================================
    # Completion dialog
    # ========================================================================

    def _show_completion_message(
        self,
        total: int,
        successful: int,
        cancelled: bool,
    ) -> None:

        if cancelled:

            title = (
                "Batch Processing Cancelled"
            )

            message = (
                "The Batch Processing run was cancelled.\n\n"
                f"Images successfully analyzed: "
                f"{successful}/{total}"
            )

            icon = (
                QMessageBox.Icon.Warning
            )

        elif successful == total:

            title = (
                "Batch Processing Completed"
            )

            message = (
                "Batch Processing completed successfully.\n\n"
                f"Images successfully analyzed: "
                f"{successful}/{total}\n\n"
                "The output files have been created in the "
                "selected output folder."
            )

            icon = (
                QMessageBox.Icon.Information
            )

        else:

            title = (
                "Batch Processing Completed with Errors"
            )

            message = (
                "Batch Processing finished, but not all "
                "images were successfully analyzed.\n\n"
                f"Images successfully analyzed: "
                f"{successful}/{total}\n"
                f"Images not successfully analyzed: "
                f"{total - successful}"
            )

            icon = (
                QMessageBox.Icon.Warning
            )

        dialog = QMessageBox(
            self
        )

        dialog.setIcon(
            icon
        )

        dialog.setWindowTitle(
            f"Canopy GSM — {title}"
        )

        dialog.setText(
            message
        )

        window = self.window()

        if window is not None:

            dialog.setWindowIcon(
                window.windowIcon()
            )

        dialog.exec()

    # ========================================================================
    # Error dialog
    # ========================================================================

    def _show_error(
        self,
        title: str,
        message: str,
    ) -> None:

        dialog = QMessageBox(
            self
        )

        dialog.setIcon(
            QMessageBox.Icon.Critical
        )

        dialog.setWindowTitle(
            f"Canopy GSM — {title}"
        )

        dialog.setText(
            message
        )

        window = self.window()

        if window is not None:

            dialog.setWindowIcon(
                window.windowIcon()
            )

        dialog.exec()