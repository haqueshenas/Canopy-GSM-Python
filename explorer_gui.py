
"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Interactive Canopy GSM Explorer.

The Explorer is an application-level analytical workspace for inspecting
a single RGB image. It uses the same scientific GSM engine as the Batch
Processing workflow.

Scientific calculations are performed by gsm_engine.py.
Interactive Green-range selection, image filtering, visualization, and
optional exploratory curve fitting are presentation/analysis-layer
operations and do not modify the frozen GSM scientific result.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from PySide6.QtCore import (
    QObject,
    QPoint,
    QMarginsF,
    QPointF,
    QRectF,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPageLayout,
    QPageSize,
    QPixmap,
    QPdfWriter,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from curve_fitting import fit_exp1
from gsm_engine import (
    BACKGROUND_RGB,
    GSMInputError,
    GSMResult,
    ST1Config,
    make_processed_image,
    process_image,
    segment_st1,
    VERSION,
)
from io_utils import load_rgb_uint8, save_rgb_uint8


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

LOGO_PNG = PROJECT_ROOT / "CanopyGSM.png"
LOGO_ICO = PROJECT_ROOT / "CanopyGSM.ico"


# ---------------------------------------------------------------------------
# Visual identity
# ---------------------------------------------------------------------------

EPL_GREEN = "#57863c"

WINDOW_BACKGROUND = "#f5f6f4"
CARD_BACKGROUND = "#ffffff"

TEXT_PRIMARY = "#202520"
TEXT_SECONDARY = "#5f665f"

BORDER = "#d9ded6"

RED_POINT = "#c43b3b"
GREEN_POINT = "#57863c"
BLUE_POINT = "#3f6fb5"

ST3_RED_MARKER = "#d88c8c"
ST3_BLUE_MARKER = "#8fb0dc"

SELECTED_POINT = "#202520"
OUTSIDE_POINT = "#c8ccc8"

SELECTION_FILL = QColor(
    120,
    120,
    120,
    22,
)

REVERSE_FILL = QColor(
    120,
    120,
    120,
    22,
)


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------

def application_icon() -> QIcon:
    """
    Return the Canopy GSM application icon.
    """
    if LOGO_ICO.is_file():
        icon = QIcon(
            str(LOGO_ICO)
        )

        if not icon.isNull():
            return icon

    if LOGO_PNG.is_file():
        icon = QIcon(
            str(LOGO_PNG)
        )

        if not icon.isNull():
            return icon

    return QIcon()


def show_error(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """
    Display a branded application error dialog.
    """
    dialog = QMessageBox(parent)

    dialog.setIcon(
        QMessageBox.Icon.Critical
    )

    dialog.setWindowTitle(
        title
    )

    dialog.setText(
        message
    )

    icon = application_icon()

    if not icon.isNull():
        dialog.setWindowIcon(
            icon
        )

    dialog.exec()


def show_warning(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """
    Display a branded application warning dialog.
    """
    dialog = QMessageBox(parent)

    dialog.setIcon(
        QMessageBox.Icon.Warning
    )

    dialog.setWindowTitle(
        title
    )

    dialog.setText(
        message
    )

    icon = application_icon()

    if not icon.isNull():
        dialog.setWindowIcon(
            icon
        )

    dialog.exec()


def show_information(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """
    Display a branded information dialog.
    """
    dialog = QMessageBox(parent)

    dialog.setIcon(
        QMessageBox.Icon.Information
    )

    dialog.setWindowTitle(
        title
    )

    dialog.setText(
        message
    )

    icon = application_icon()

    if not icon.isNull():
        dialog.setWindowIcon(
            icon
        )

    dialog.exec()


# ---------------------------------------------------------------------------
# Dual-handle Green-range slider
# ---------------------------------------------------------------------------

class RangeSlider(QWidget):
    """
    A two-handle slider for selecting an inclusive integer range 1..255.

    The lower and upper handles can be moved independently.
    """

    rangeChanged = Signal(int, int)

    def __init__(
        self,
        minimum: int = 1,
        maximum: int = 255,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        if minimum >= maximum:
            raise ValueError(
                "RangeSlider minimum must be smaller than maximum."
            )

        self._minimum = int(minimum)
        self._maximum = int(maximum)

        self._lower = self._minimum
        self._upper = self._maximum

        self._handle_radius = 7
        self._track_height = 6

        self._track_left = (
            self._handle_radius + 4
        )
        self._track_right = None

        self._active_handle: Optional[str] = None

        self.setMinimumHeight(42)
        self.setMaximumHeight(48)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setMouseTracking(True)

        self.setToolTip(
            "Drag the two handles to select the Green-value range."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def lower(self) -> int:
        return self._lower

    @property
    def upper(self) -> int:
        return self._upper

    def set_track_bounds(
        self,
        left: float,
        right: float,
    ) -> None:
        """
        Set the track bounds in widget coordinates to match the GSM plot.
        """
        available_left = float(
            self._handle_radius
        )

        available_right = max(
            available_left + 1.0,
            float(self.width())
            - self._handle_radius,
        )

        self._track_left = max(
            available_left,
            min(
                float(left),
                available_right - 1.0,
            ),
        )

        self._track_right = min(
            available_right,
            max(
                self._track_left + 1.0,
                float(right),
            ),
        )

        self.update()

    def set_range(
        self,
        lower: int,
        upper: int,
        emit_signal: bool = True,
    ) -> None:

        lower = max(
            self._minimum,
            min(
                self._maximum,
                int(lower),
            ),
        )

        upper = max(
            self._minimum,
            min(
                self._maximum,
                int(upper),
            ),
        )

        if lower > upper:
            lower, upper = upper, lower

        changed = (
            lower != self._lower
            or upper != self._upper
        )

        self._lower = lower
        self._upper = upper

        self.update()

        if changed and emit_signal:
            self.rangeChanged.emit(
                self._lower,
                self._upper,
            )

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def _track_rect(self) -> QRectF:
        left = self._track_left

        if self._track_right is None:
            right = (
                self.width()
                - self._handle_radius
                - 4
            )
        else:
            right = self._track_right

        y = self.height() / 2

        return QRectF(
            left,
            y - self._track_height / 2,
            max(
                1.0,
                right - left,
            ),
            self._track_height,
        )

    def _value_to_x(
        self,
        value: int,
    ) -> float:

        rect = self._track_rect()

        fraction = (
            value - self._minimum
        ) / (
            self._maximum
            - self._minimum
        )

        return (
            rect.left()
            + fraction * rect.width()
        )

    def _x_to_value(
        self,
        x: float,
    ) -> int:

        rect = self._track_rect()

        if rect.width() <= 0:
            return self._minimum

        fraction = (
            x - rect.left()
        ) / rect.width()

        fraction = max(
            0.0,
            min(
                1.0,
                fraction,
            ),
        )

        value = (
            self._minimum
            + fraction
            * (
                self._maximum
                - self._minimum
            )
        )

        return int(
            round(value)
        )

    def _handle_distance(
        self,
        x: float,
        value: int,
    ) -> float:

        return abs(
            x
            - self._value_to_x(
                value
            )
        )

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(
        self,
        event,
    ):
        del event

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        rect = self._track_rect()

        # --------------------------------------------------------------
        # Full track
        # --------------------------------------------------------------

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QColor("#d9ddd8")
        )

        painter.drawRoundedRect(
            rect,
            3,
            3,
        )

        # --------------------------------------------------------------
        # Selected segment
        # --------------------------------------------------------------

        x1 = self._value_to_x(
            self._lower
        )

        x2 = self._value_to_x(
            self._upper
        )

        selected_rect = QRectF(
            x1,
            rect.top(),
            max(
                0.0,
                x2 - x1,
            ),
            rect.height(),
        )

        painter.setBrush(
            QColor(EPL_GREEN)
        )

        painter.drawRoundedRect(
            selected_rect,
            3,
            3,
        )

        # --------------------------------------------------------------
        # Handles
        # --------------------------------------------------------------

        for value in (
            self._lower,
            self._upper,
        ):
            x = self._value_to_x(
                value
            )

            painter.setBrush(
                QColor("white")
            )

            handle_pen = QPen(
                QColor(EPL_GREEN)
            )
            handle_pen.setWidth(2)

            painter.setPen(
                handle_pen
            )

            painter.drawEllipse(
                QPointF(x, rect.center().y()),
                self._handle_radius,
                self._handle_radius,
            )

        # --------------------------------------------------------------
        # Labels
        # --------------------------------------------------------------

        label_font = QFont(
            "Segoe UI",
            8,
        )

        painter.setFont(
            label_font
        )

        painter.setPen(
            QColor(TEXT_SECONDARY)
        )

        painter.drawText(
            int(x1 - 18),
            2,
            36,
            15,
            Qt.AlignmentFlag.AlignCenter,
            str(self._lower),
        )

        painter.drawText(
            int(x2 - 18),
            2,
            36,
            15,
            Qt.AlignmentFlag.AlignCenter,
            str(self._upper),
        )

        painter.end()

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def mousePressEvent(
        self,
        event,
    ):
        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        x = event.position().x()

        lower_distance = self._handle_distance(
            x,
            self._lower,
        )

        upper_distance = self._handle_distance(
            x,
            self._upper,
        )

        handle_threshold = 14

        if (
            lower_distance <= handle_threshold
            and upper_distance <= handle_threshold
        ):
            self._active_handle = (
                "lower"
                if lower_distance <= upper_distance
                else
                "upper"
            )

        elif lower_distance <= handle_threshold:
            self._active_handle = "lower"

        elif upper_distance <= handle_threshold:
            self._active_handle = "upper"

        else:
            value = self._x_to_value(
                x
            )

            if (
                abs(value - self._lower)
                <= abs(value - self._upper)
            ):
                self._active_handle = "lower"
            else:
                self._active_handle = "upper"

            self._set_active_from_value(
                value
            )

        self.update()

    def mouseMoveEvent(
        self,
        event,
    ):
        if self._active_handle is None:
            return

        value = self._x_to_value(
            event.position().x()
        )

        if self._active_handle == "lower":
            value = min(
                value,
                self._upper,
            )

            self.set_range(
                value,
                self._upper,
            )

        else:
            value = max(
                value,
                self._lower,
            )

            self.set_range(
                self._lower,
                value,
            )

    def mouseReleaseEvent(
        self,
        event,
    ):
        del event

        self._active_handle = None
        self.update()

    def _set_active_from_value(
        self,
        value: int,
    ) -> None:

        if self._active_handle == "lower":
            self.set_range(
                value,
                self._upper,
            )
        else:
            self.set_range(
                self._lower,
                value,
            )


# ---------------------------------------------------------------------------
# Image display
# ---------------------------------------------------------------------------

class ImagePreview(QLabel):
    """
    Responsive image preview with independent, cursor-centred zoom and pan.

    Zoom is a presentation-only transform. The underlying RGB image array is
    never resized or modified by this widget.
    """

    ZOOM_MIN = 1.0
    ZOOM_MAX = 16.0
    ZOOM_STEP = 1.18
    PAN_KEY_FRACTION = 0.10

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None

        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._panning = False
        self._pan_start_pos = QPointF(0.0, 0.0)
        self._pan_start_offset = QPointF(0.0, 0.0)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(280, 280)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setToolTip(
            "Ctrl+Wheel: zoom · Middle-drag: pan · Right-click: keyboard focus · Arrow keys: pan · +/-: zoom · 0: reset zoom"
        )
        self.setStyleSheet(
            """
            QLabel {
                background: white;
                border: none;
            }
            """
        )

    # ------------------------------------------------------------------
    # Image state
    # ------------------------------------------------------------------

    def set_image(
        self,
        image: Optional[np.ndarray],
        *,
        reset_view: bool = True,
    ) -> None:
        if image is None:
            self._image = None
            self._pixmap = None
            self._zoom = 1.0
            self._pan = QPointF(0.0, 0.0)
            self.update()
            return

        image = np.asarray(image)
        if (
            image.ndim != 3
            or image.shape[2] != 3
            or image.dtype != np.uint8
        ):
            self._image = None
            self._pixmap = None
            self._zoom = 1.0
            self._pan = QPointF(0.0, 0.0)
            self.update()
            return

        self._image = image.copy()
        height, width = self._image.shape[:2]
        qimage = QImage(
            self._image.data,
            width,
            height,
            width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        self._pixmap = QPixmap.fromImage(qimage)
        if reset_view:
            self._zoom = 1.0
            self._pan = QPointF(0.0, 0.0)
        self._clamp_pan()
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._clamp_pan()
        self.update()

    # ------------------------------------------------------------------
    # Geometry / transform helpers
    # ------------------------------------------------------------------

    def _fit_scale(self) -> float:
        if self._pixmap is None or self._pixmap.isNull():
            return 1.0
        available_width = max(1.0, float(self.width() - 12))
        available_height = max(1.0, float(self.height() - 12))
        return min(
            available_width / float(self._pixmap.width()),
            available_height / float(self._pixmap.height()),
        )

    def _display_size(self) -> tuple[float, float]:
        if self._pixmap is None or self._pixmap.isNull():
            return 0.0, 0.0
        scale = self._fit_scale() * self._zoom
        return (
            float(self._pixmap.width()) * scale,
            float(self._pixmap.height()) * scale,
        )

    def _clamp_pan(self) -> None:
        display_width, display_height = self._display_size()
        max_x = max(0.0, (display_width - float(self.width())) / 2.0)
        max_y = max(0.0, (display_height - float(self.height())) / 2.0)
        self._pan.setX(max(-max_x, min(max_x, self._pan.x())))
        self._pan.setY(max(-max_y, min(max_y, self._pan.y())))

    def _image_position_from_widget(
        self,
        position: QPointF,
    ) -> tuple[float, float]:
        if self._pixmap is None or self._pixmap.isNull():
            return 0.0, 0.0

        display_width, display_height = self._display_size()
        center_x = float(self.width()) / 2.0 + self._pan.x()
        center_y = float(self.height()) / 2.0 + self._pan.y()
        left = center_x - display_width / 2.0
        top = center_y - display_height / 2.0

        u = (float(position.x()) - left) / max(1.0, display_width)
        v = (float(position.y()) - top) / max(1.0, display_height)
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        return (
            u * float(self._pixmap.width()),
            v * float(self._pixmap.height()),
        )

    def _set_zoom_at(
        self,
        factor: float,
        position: Optional[QPointF] = None,
    ) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            return

        old_zoom = self._zoom
        new_zoom = max(
            self.ZOOM_MIN,
            min(self.ZOOM_MAX, old_zoom * float(factor)),
        )
        if abs(new_zoom - old_zoom) < 1.0e-9:
            return

        if position is None:
            position = QPointF(
                float(self.width()) / 2.0,
                float(self.height()) / 2.0,
            )

        image_x, image_y = self._image_position_from_widget(position)
        self._zoom = new_zoom

        display_width, display_height = self._display_size()
        base_scale = self._fit_scale()
        image_display_x = image_x * base_scale * self._zoom
        image_display_y = image_y * base_scale * self._zoom
        desired_center_x = float(position.x()) - (
            image_display_x - display_width / 2.0
        )
        desired_center_y = float(position.y()) - (
            image_display_y - display_height / 2.0
        )

        self._pan = QPointF(
            desired_center_x - float(self.width()) / 2.0,
            desired_center_y - float(self.height()) / 2.0,
        )
        self._clamp_pan()
        self.update()

    # ------------------------------------------------------------------
    # Mouse / keyboard interaction
    # ------------------------------------------------------------------

    def wheelEvent(self, event) -> None:
        if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            event.ignore()
            return

        delta = float(event.angleDelta().y())
        if abs(delta) < 1.0:
            delta = float(event.pixelDelta().y()) * 4.0
        if abs(delta) < 1.0:
            event.ignore()
            return

        factor = math.pow(self.ZOOM_STEP, delta / 120.0)
        self._set_zoom_at(factor, event.position())
        event.accept()

    def mousePressEvent(self, event) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start_pos = event.position()
            self._pan_start_offset = QPointF(
                self._pan.x(),
                self._pan.y(),
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return
        event.accept()

    def contextMenuEvent(self, event) -> None:
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.position() - self._pan_start_pos
            self._pan = QPointF(
                self._pan_start_offset.x() + delta.x(),
                self._pan_start_offset.y() + delta.y(),
            )
            self._clamp_pan()
            self.update()
            event.accept()
            return
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.unsetCursor()
            event.accept()
            return
        event.accept()

    def _pan_by_keyboard(self, key: Qt.Key) -> bool:
        if self._pixmap is None or self._pixmap.isNull() or self._zoom <= self.ZOOM_MIN + 1.0e-9:
            return False

        step_x = max(1.0, float(self.width()) * self.PAN_KEY_FRACTION)
        step_y = max(1.0, float(self.height()) * self.PAN_KEY_FRACTION)

        if key == Qt.Key.Key_Left:
            self._pan.setX(self._pan.x() + step_x)
        elif key == Qt.Key.Key_Right:
            self._pan.setX(self._pan.x() - step_x)
        elif key == Qt.Key.Key_Up:
            self._pan.setY(self._pan.y() + step_y)
        elif key == Qt.Key.Key_Down:
            self._pan.setY(self._pan.y() - step_y)
        else:
            return False

        self._clamp_pan()
        self.update()
        return True

    def keyPressEvent(self, event) -> None:
        if event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            if self._pan_by_keyboard(event.key()):
                event.accept()
            else:
                event.accept()
            return
        if (
            event.key() == Qt.Key.Key_Plus
            or (
                event.key() == Qt.Key.Key_Equal
                and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            )
        ):
            self._set_zoom_at(self.ZOOM_STEP)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Minus:
            self._set_zoom_at(1.0 / self.ZOOM_STEP)
            event.accept()
            return
        if event.key() == Qt.Key.Key_0:
            self.reset_zoom()
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._clamp_pan()
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("white"))

        if self._pixmap is None or self._pixmap.isNull():
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                (
                    "Open an RGB image to begin."
                    if self._image is None
                    else "Invalid image for display."
                ),
            )
            painter.end()
            return

        display_width, display_height = self._display_size()
        center_x = float(self.width()) / 2.0 + self._pan.x()
        center_y = float(self.height()) / 2.0 + self._pan.y()
        target = QRectF(
            center_x - display_width / 2.0,
            center_y - display_height / 2.0,
            display_width,
            display_height,
        )
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
        painter.end()


# ---------------------------------------------------------------------------
# Explorer fit result
# ---------------------------------------------------------------------------

@dataclass
class ExplorerFitResult:
    """
    One optional Explorer fitting result.
    """

    model: str
    channel: str

    x: np.ndarray
    y: np.ndarray
    y_fit: np.ndarray

    rsquare: float
    rmse: float

    coefficients: tuple[float, ...]
    equation: str

    valid: bool = True
    message: str = ""


# ---------------------------------------------------------------------------
# Fitting helpers
# ---------------------------------------------------------------------------

def _compute_r2_rmse(
    y: np.ndarray,
    y_fit: np.ndarray,
) -> tuple[float, float]:

    y = np.asarray(
        y,
        dtype=np.float64,
    )

    y_fit = np.asarray(
        y_fit,
        dtype=np.float64,
    )

    finite = (
        np.isfinite(y)
        & np.isfinite(y_fit)
    )

    y = y[finite]
    y_fit = y_fit[finite]

    if y.size == 0:
        return np.nan, np.nan

    residual = (
        y - y_fit
    )

    sse = float(
        np.sum(
            residual * residual
        )
    )

    rmse = float(
        np.sqrt(
            np.mean(
                residual * residual
            )
        )
    )

    centered = (
        y - np.mean(y)
    )

    sst = float(
        np.sum(
            centered * centered
        )
    )

    if sst <= 0:
        rsquare = np.nan
    else:
        rsquare = float(
            1.0 - sse / sst
        )

    return rsquare, rmse


def fit_exponential_selected(
    x: np.ndarray,
    y: np.ndarray,
    channel: str,
) -> ExplorerFitResult:

    valid = (
        np.isfinite(x)
        & np.isfinite(y)
    )

    x_valid = np.asarray(
        x[valid],
        dtype=np.float64,
    )

    y_valid = np.asarray(
        y[valid],
        dtype=np.float64,
    )

    if x_valid.size < 3:
        return ExplorerFitResult(
            model="Exponential",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=np.empty(0),
            rsquare=np.nan,
            rmse=np.nan,
            coefficients=(),
            equation="",
            valid=False,
            message="At least three valid points are required.",
        )

    try:
        result = fit_exp1(
            x_valid,
            y_valid,
        )

        a = float(
            result.a
        )

        b = float(
            result.b
        )

        y_fit = (
            a
            * np.exp(
                b * x_valid
            )
        )

        rsquare, rmse = (
            _compute_r2_rmse(
                y_valid,
                y_fit,
            )
        )

        equation = (
            "y = "
            f"{a:.8g}"
            " · exp("
            f"{b:.8g}"
            " · x)"
        )

        return ExplorerFitResult(
            model="Exponential",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=y_fit,
            rsquare=rsquare,
            rmse=rmse,
            coefficients=(
                a,
                b,
            ),
            equation=equation,
        )

    except Exception as exc:
        return ExplorerFitResult(
            model="Exponential",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=np.empty(0),
            rsquare=np.nan,
            rmse=np.nan,
            coefficients=(),
            equation="",
            valid=False,
            message=str(exc),
        )


def fit_polynomial_selected(
    x: np.ndarray,
    y: np.ndarray,
    channel: str,
) -> ExplorerFitResult:

    valid = (
        np.isfinite(x)
        & np.isfinite(y)
    )

    x_valid = np.asarray(
        x[valid],
        dtype=np.float64,
    )

    y_valid = np.asarray(
        y[valid],
        dtype=np.float64,
    )

    if x_valid.size < 3:
        return ExplorerFitResult(
            model="Polynomial degree 2",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=np.empty(0),
            rsquare=np.nan,
            rmse=np.nan,
            coefficients=(),
            equation="",
            valid=False,
            message="At least three valid points are required.",
        )

    try:
        coefficients = np.polyfit(
            x_valid,
            y_valid,
            2,
        )

        a2 = float(
            coefficients[0]
        )

        a1 = float(
            coefficients[1]
        )

        a0 = float(
            coefficients[2]
        )

        y_fit = np.polyval(
            coefficients,
            x_valid,
        )

        rsquare, rmse = (
            _compute_r2_rmse(
                y_valid,
                y_fit,
            )
        )

        equation = (
            "y = "
            f"{a2:.8g}"
            "x² + "
            f"{a1:.8g}"
            "x + "
            f"{a0:.8g}"
        )

        return ExplorerFitResult(
            model="Polynomial degree 2",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=y_fit,
            rsquare=rsquare,
            rmse=rmse,
            coefficients=(
                a2,
                a1,
                a0,
            ),
            equation=equation,
        )

    except Exception as exc:
        return ExplorerFitResult(
            model="Polynomial degree 2",
            channel=channel,
            x=x_valid,
            y=y_valid,
            y_fit=np.empty(0),
            rsquare=np.nan,
            rmse=np.nan,
            coefficients=(),
            equation="",
            valid=False,
            message=str(exc),
        )


# ---------------------------------------------------------------------------
# GSM Graph
# ---------------------------------------------------------------------------

class GSMGraphWidget(QWidget):
    """
    Interactive GSM visualization.

    The scientific result is supplied by GSMResult. This widget is only
    responsible for rendering and interaction.

    The square plot uses equal X/Y physical dimensions. The vertical legend
    occupies unused horizontal space beside the square plot when available.
    """

    plotBoundsChanged = Signal(float, float)
    cursorChanged = Signal(object)

    PLOT_LEFT_MARGIN = 54
    PLOT_RIGHT_MARGIN = 116
    PLOT_TOP_MARGIN = 34
    PLOT_BOTTOM_MARGIN = 42
    ZOOM_MIN = 1.0
    ZOOM_MAX = 16.0
    ZOOM_STEP = 1.18
    PAN_KEY_FRACTION = 0.10

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._result: Optional[GSMResult] = None
        self._range_min = 1
        self._range_max = 255
        self._reverse = False
        self._show_fit = False
        self._fit_model = "Exponential"
        self._show_gsm_data = True
        self._show_st3 = False
        self._show_st3_labels = False
        self._show_cursor_details = True
        self._cursor_level: Optional[int] = None
        self._red_fit: Optional[ExplorerFitResult] = None
        self._blue_fit: Optional[ExplorerFitResult] = None
        self._build_in_progress = False

        self._zoom = 1.0
        self._view_center_x = 128.0
        self._view_center_y = 127.5
        self._panning = False
        self._pan_start_pos = QPointF(0.0, 0.0)
        self._pan_start_center = QPointF(128.0, 127.5)

        self.setMinimumSize(300, 280)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setMouseTracking(True)
        self.setToolTip(
            "Ctrl+Wheel: zoom · Middle-drag: pan · Right-click: keyboard focus · Arrow keys: pan · +/-: zoom · 0: reset zoom"
        )
        self.setStyleSheet(
            """
            QWidget {
                background: white;
                border: none;
            }
            """
        )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def set_result(self, result: Optional[GSMResult]) -> None:
        self._result = result
        self._build_in_progress = False
        if result is None:
            self._cursor_level = None
            self.reset_zoom()
        else:
            self._clamp_view_center()
        self.update()

    def set_build_in_progress(self, building: bool) -> None:
        """Show or hide the temporary GSM-build wait overlay."""
        self._build_in_progress = bool(building)
        self.update()

    def set_selection(self, range_min: int, range_max: int, reverse: bool) -> None:
        self._range_min = int(range_min)
        self._range_max = int(range_max)
        self._reverse = bool(reverse)
        self.update()

    def set_data_visibility(self, show_data: bool) -> None:
        self._show_gsm_data = bool(show_data)
        self.update()

    def set_st3_visibility(self, show_st3: bool) -> None:
        self._show_st3 = bool(show_st3)
        self.update()

    def set_st3_labels_visibility(self, show_labels: bool) -> None:
        self._show_st3_labels = bool(show_labels)
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._view_center_x = 128.0
        self._view_center_y = 127.5
        self._clamp_view_center()
        self._cursor_level = None
        self.update()

    def set_zoom_factor(self, factor: float) -> None:
        if self._result is None:
            return
        self._zoom = max(
            self.ZOOM_MIN,
            min(self.ZOOM_MAX, float(factor)),
        )
        self._clamp_view_center()
        self.update()

    def set_cursor_visibility(self, show_cursor: bool) -> None:
        self._show_cursor_details = bool(show_cursor)
        if not self._show_cursor_details:
            self._cursor_level = None
        self.update()

    def set_fit(
        self,
        show_fit: bool,
        model: str,
        red_fit: Optional[ExplorerFitResult],
        blue_fit: Optional[ExplorerFitResult],
    ) -> None:
        self._show_fit = bool(show_fit)
        self._fit_model = model
        self._red_fit = red_fit
        self._blue_fit = blue_fit
        self.update()

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def _plot_rect(self) -> tuple[float, float, float]:
        left_margin = float(self.PLOT_LEFT_MARGIN)
        right_margin = float(self.PLOT_RIGHT_MARGIN)
        top_margin = float(self.PLOT_TOP_MARGIN)
        bottom_margin = float(self.PLOT_BOTTOM_MARGIN)

        available_width = max(
            1.0,
            float(self.width()) - left_margin - right_margin,
        )
        available_height = max(
            1.0,
            float(self.height()) - top_margin - bottom_margin,
        )

        side = min(available_width, available_height)

        left = left_margin + max(
            0.0,
            (available_width - side) / 2.0,
        )
        top = top_margin + max(
            0.0,
            (available_height - side) / 2.0,
        )

        return left, top, side

    def plot_x_bounds(self) -> tuple[float, float]:
        left, _top, side = self._plot_rect()
        return left, left + side

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        left, right = self.plot_x_bounds()
        self.plotBoundsChanged.emit(left, right)

    def _view_ranges(self) -> tuple[float, float, float, float]:
        x_span = 254.0 / self._zoom
        y_span = 255.0 / self._zoom
        x_min = self._view_center_x - x_span / 2.0
        x_max = self._view_center_x + x_span / 2.0
        y_min = self._view_center_y - y_span / 2.0
        y_max = self._view_center_y + y_span / 2.0
        return x_min, x_max, y_min, y_max

    def _clamp_view_center(self) -> None:
        x_span = 254.0 / self._zoom
        y_span = 255.0 / self._zoom
        half_x = x_span / 2.0
        half_y = y_span / 2.0
        self._view_center_x = max(
            1.0 + half_x,
            min(255.0 - half_x, self._view_center_x),
        )
        self._view_center_y = max(
            0.0 + half_y,
            min(255.0 - half_y, self._view_center_y),
        )

    def _x_to_pixel(self, value: float, left: float, side: float) -> float:
        x_min, x_max, _y_min, _y_max = self._view_ranges()
        return left + (
            (float(value) - x_min) / max(1.0e-12, x_max - x_min)
        ) * side

    def _y_to_pixel(self, value: float, top: float, side: float) -> float:
        _x_min, _x_max, y_min, y_max = self._view_ranges()
        value = max(y_min, min(y_max, float(value)))
        return top + (
            1.0 - (value - y_min) / max(1.0e-12, y_max - y_min)
        ) * side

    def _pixel_to_data(
        self,
        x: float,
        y: float,
        left: float,
        top: float,
        side: float,
    ) -> tuple[float, float]:
        x_min, x_max, y_min, y_max = self._view_ranges()
        u = max(0.0, min(1.0, (x - left) / max(1.0, side)))
        v = max(0.0, min(1.0, (y - top) / max(1.0, side)))
        data_x = x_min + u * (x_max - x_min)
        data_y = y_min + (1.0 - v) * (y_max - y_min)
        return data_x, data_y

    def _zoom_at_position(
        self,
        factor: float,
        position: Optional[QPointF] = None,
    ) -> None:
        if self._result is None:
            return
        left, top, side = self._plot_rect()
        if position is None:
            position = QPointF(
                float(left + side / 2.0),
                float(top + side / 2.0),
            )

        old_zoom = self._zoom
        new_zoom = max(
            self.ZOOM_MIN,
            min(self.ZOOM_MAX, old_zoom * float(factor)),
        )
        if abs(new_zoom - old_zoom) < 1.0e-9:
            return

        data_x, data_y = self._pixel_to_data(
            float(position.x()),
            float(position.y()),
            left,
            top,
            side,
        )
        u = (float(position.x()) - left) / max(1.0, side)
        v = (float(position.y()) - top) / max(1.0, side)

        new_x_span = 254.0 / new_zoom
        new_y_span = 255.0 / new_zoom
        self._zoom = new_zoom
        self._view_center_x = data_x - (u - 0.5) * new_x_span
        self._view_center_y = data_y + (v - 0.5) * new_y_span
        self._clamp_view_center()
        self._cursor_level = None
        self.update()

    @staticmethod
    def _nice_ticks(
        minimum: float,
        maximum: float,
        target_count: int = 5,
    ) -> list[int]:
        if maximum <= minimum:
            return [int(round(minimum))]

        span = maximum - minimum
        raw_step = span / max(1, target_count - 1)
        magnitude = 10.0 ** math.floor(math.log10(raw_step))
        normalized = raw_step / magnitude
        if normalized <= 1.0:
            multiplier = 1.0
        elif normalized <= 2.0:
            multiplier = 2.0
        elif normalized <= 5.0:
            multiplier = 5.0
        else:
            multiplier = 10.0
        step = max(1.0, multiplier * magnitude)

        first = int(math.ceil(minimum / step) * step)
        last = int(math.floor(maximum / step) * step)
        ticks = list(range(first, last + 1, max(1, int(round(step)))))

        for endpoint in (int(round(minimum)), int(round(maximum))):
            if 0 <= endpoint <= 255 and endpoint not in ticks:
                ticks.append(endpoint)

        ticks = sorted(set(max(0, min(255, value)) for value in ticks))
        if len(ticks) > 6:
            indices = np.linspace(0, len(ticks) - 1, 6).round().astype(int)
            ticks = [ticks[i] for i in sorted(set(indices.tolist()))]
        return ticks

    def _cursor_level_from_position(
        self,
        x: float,
        y: float,
    ) -> Optional[int]:
        if self._result is None:
            return None

        left, top, side = self._plot_rect()

        if not (
            left <= x <= left + side
            and top <= y <= top + side
        ):
            return None

        data_x, _data_y = self._pixel_to_data(
            x,
            y,
            left,
            top,
            side,
        )
        level = int(round(data_x))
        return max(1, min(255, level))

    def _set_cursor_level(
        self,
        level: Optional[int],
    ) -> None:
        if level == self._cursor_level:
            return

        self._cursor_level = level
        self.cursorChanged.emit(level)
        self.update()

    def _draw_cursor_overlay(
        self,
        painter: QPainter,
        left: float,
        top: float,
        side: float,
    ) -> None:
        if (
            not self._show_cursor_details
            or self._cursor_level is None
            or self._result is None
        ):
            return

        index = self._cursor_level - 1

        red = float(self._result.mean_red[index])
        green = float(self._result.green[index])
        blue = float(self._result.mean_blue[index])
        red_slope = float(self._result.red_slope[index])
        blue_slope = float(self._result.blue_slope[index])

        red_st3 = int(self._result.red_st3_class[index])
        blue_st3 = int(self._result.blue_st3_class[index])

        x = self._x_to_pixel(
            self._cursor_level,
            left,
            side,
        )

        painter.save()

        cursor_pen = QPen(QColor(120, 120, 120, 150))
        cursor_pen.setWidthF(0.9)
        cursor_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(cursor_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(
            int(round(x)),
            int(round(top)),
            int(round(x)),
            int(round(top + side)),
        )

        # The readout sits below the legend so it remains outside the plot.
        readout_x = left + side + 48.0
        readout_width = max(1.0, float(self.width()) - readout_x - 8.0)
        readout_y = top + 142.0

        heading_font = QFont("Segoe UI", 8)
        heading_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(heading_font)
        painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(
            QRectF(readout_x, readout_y, readout_width, 18.0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"Cursor · Green {self._cursor_level}",
        )

        value_font = QFont("Segoe UI", 8)
        painter.setFont(value_font)
        painter.setPen(QColor(TEXT_SECONDARY))

        lines = [
            f"R  {self._format_value(red)}",
            f"G  {self._format_value(green)}",
            f"B  {self._format_value(blue)}",
            f"dR/dG  {self._format_value(red_slope)}",
            f"dB/dG  {self._format_value(blue_slope)}",
            f"Red-ST3  {red_st3 if red_st3 > 0 else '—'}",
            f"Blue-ST3  {blue_st3 if blue_st3 > 0 else '—'}",
        ]

        y = readout_y + 18.0
        for text in lines:
            painter.drawText(
                QRectF(readout_x, y, readout_width, 16.0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
            y += 16.0

        painter.restore()

    @staticmethod
    def _format_value(value: float) -> str:
        if not np.isfinite(value):
            return "—"
        if abs(value) >= 1000.0 or (0.0 < abs(value) < 0.001):
            return f"{value:.4e}"
        return f"{value:.4f}"

    # ------------------------------------------------------------------
    # Axes
    # ------------------------------------------------------------------

    def _draw_axes(self, painter: QPainter, left: float, top: float, side: float) -> None:
        right = left + side
        bottom = top + side

        axis_pen = QPen(QColor("#303530"))
        axis_pen.setWidthF(1.15)
        painter.setPen(axis_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawLine(int(round(left)), int(round(bottom)), int(round(right)), int(round(bottom)))
        painter.drawLine(int(round(left)), int(round(top)), int(round(left)), int(round(bottom)))

        x_min, x_max, y_min, y_max = self._view_ranges()
        x_ticks = (
            [1, 64, 128, 192, 255]
            if abs(self._zoom - 1.0) < 1.0e-9
            else self._nice_ticks(max(1.0, x_min), min(255.0, x_max))
        )
        y_ticks = (
            [0, 64, 128, 192, 255]
            if abs(self._zoom - 1.0) < 1.0e-9
            else self._nice_ticks(max(0.0, y_min), min(255.0, y_max))
        )

        tick_font = QFont("Segoe UI", 8)
        painter.setFont(tick_font)
        painter.setPen(QColor(TEXT_PRIMARY))

        for tick in x_ticks:
            x = self._x_to_pixel(tick, left, side)
            painter.drawLine(
                int(round(x)),
                int(round(bottom)),
                int(round(x)),
                int(round(bottom + 5)),
            )
            painter.drawText(
                int(round(x - 18)),
                int(round(bottom + 7)),
                36,
                17,
                Qt.AlignmentFlag.AlignCenter,
                str(tick),
            )

        for tick in y_ticks:
            y = self._y_to_pixel(tick, top, side)
            painter.drawLine(
                int(round(left - 5)),
                int(round(y)),
                int(round(left)),
                int(round(y)),
            )
            painter.drawText(
                int(round(left - 47)),
                int(round(y - 8)),
                39,
                17,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(tick),
            )

        label_font = QFont("Segoe UI", 9)
        label_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(label_font)

        painter.drawText(
            int(round(left)),
            int(round(bottom + 28)),
            int(round(side)),
            18,
            Qt.AlignmentFlag.AlignCenter,
            "Green level",
        )

        painter.save()
        painter.translate(left - 52, top + side / 2.0)
        painter.rotate(-90)
        painter.drawText(
            int(round(-side / 2.0)),
            0,
            int(round(side)),
            18,
            Qt.AlignmentFlag.AlignCenter,
            "Mean RGB value",
        )
        painter.restore()

    # ------------------------------------------------------------------
    # Selection shading
    # ------------------------------------------------------------------

    def _draw_selection_shading(self, painter: QPainter, left: float, top: float, side: float) -> None:
        x1 = self._x_to_pixel(self._range_min, left, side)
        x2 = self._x_to_pixel(self._range_max, left, side)

        painter.setPen(Qt.PenStyle.NoPen)

        if self._reverse:
            painter.setBrush(QBrush(QColor(120, 120, 120, 18)))
            painter.drawRect(QRectF(left, top, max(0.0, x1 - left), side))
            painter.drawRect(QRectF(x2, top, max(0.0, left + side - x2), side))
        else:
            # Keep the live UI selection shading identical to the approved
            # neutral-gray PDF shading. This is purely visual and does not
            # affect any scientific data or calculations.
            painter.setBrush(QBrush(SELECTION_FILL))
            painter.drawRect(QRectF(x1, top, max(0.0, x2 - x1), side))

        painter.setBrush(Qt.BrushStyle.NoBrush)
        boundary_pen = QPen(QColor(EPL_GREEN))
        boundary_pen.setWidthF(1.0)
        boundary_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(boundary_pen)
        painter.drawLine(int(round(x1)), int(round(top)), int(round(x1)), int(round(top + side)))
        painter.drawLine(int(round(x2)), int(round(top)), int(round(x2)), int(round(top + side)))

    # ------------------------------------------------------------------
    # Legend
    # ------------------------------------------------------------------

    def _draw_legend(self, painter: QPainter, left: float, top: float, side: float) -> None:
        entries = []

        if self._show_gsm_data:
            entries.extend(
                [
                    ("Mean Red", QColor(RED_POINT), False),
                    ("Green", QColor(GREEN_POINT), False),
                    ("Mean Blue", QColor(BLUE_POINT), False),
                ]
            )

        if self._show_fit:
            entries.extend(
                [
                    ("Red fit", QColor(RED_POINT), True),
                    ("Blue fit", QColor(BLUE_POINT), True),
                ]
            )

        if not entries:
            return

        legend_x = left + side + 48.0
        legend_y = top + 8.0

        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for text, color, is_fit in entries:
            if is_fit:
                halo = QPen(QColor("white"))
                halo.setWidthF(4.0)
                halo.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(halo)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(
                    int(round(legend_x)),
                    int(round(legend_y + 6)),
                    int(round(legend_x + 13)),
                    int(round(legend_y + 6)),
                )

                pen = QPen(color)
                pen.setWidthF(1.8)
                pen.setStyle(Qt.PenStyle.DashDotLine)
                painter.setPen(pen)
                painter.drawLine(
                    int(round(legend_x)),
                    int(round(legend_y + 6)),
                    int(round(legend_x + 13)),
                    int(round(legend_y + 6)),
                )
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(
                    int(round(legend_x + 2)),
                    int(round(legend_y + 2)),
                    8,
                    8,
                )

            painter.setPen(QColor(TEXT_PRIMARY))
            painter.drawText(
                int(round(legend_x + 20)),
                int(round(legend_y - 1)),
                max(1, int(round(self.width() - legend_x - 8))),
                18,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

            legend_y += 24.0

    # ------------------------------------------------------------------
    # Points
    # ------------------------------------------------------------------

    def _selection_level(self, level: int) -> bool:
        inside = self._range_min <= level <= self._range_max
        return (not inside) if self._reverse else inside

    def _draw_points(
        self,
        painter: QPainter,
        x: np.ndarray,
        y: np.ndarray,
        color: QColor,
        left: float,
        top: float,
        side: float,
    ) -> None:
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        painter.setPen(Qt.PenStyle.NoPen)

        for xv, yv in zip(x, y):
            if not np.isfinite(yv):
                continue

            level = int(round(xv))
            selected = self._selection_level(level)
            point_color = color if selected else QColor(OUTSIDE_POINT)
            radius = 2.9 if selected else 1.9

            px = self._x_to_pixel(float(xv), left, side)
            py = self._y_to_pixel(float(yv), top, side)

            painter.setBrush(QBrush(point_color))
            painter.drawEllipse(
                int(round(px - radius)),
                int(round(py - radius)),
                int(round(2.0 * radius)),
                int(round(2.0 * radius)),
            )


    # ------------------------------------------------------------------
    # ST3 region boundaries
    # ------------------------------------------------------------------

    @staticmethod
    def _st3_boundary_levels(classes: np.ndarray) -> np.ndarray:
        """
        Return Green levels at which a positive ST3 region ends.

        ST3 classes are scientific output already computed by GSMResult.
        This method only identifies visual region endpoints; it does not
        calculate or alter ST3 classifications.
        """
        values = np.asarray(classes, dtype=np.int64)

        if values.ndim != 1 or values.size != 255:
            return np.empty(0, dtype=np.int16)

        boundaries: list[int] = []

        for index in range(values.size):
            current = int(values[index])

            if current <= 0:
                continue

            next_value = (
                int(values[index + 1])
                if index + 1 < values.size
                else 0
            )

            if next_value != current:
                boundaries.append(index + 1)

        return np.asarray(boundaries, dtype=np.int16)

    def _draw_st3_boundary_marker(
        self,
        painter: QPainter,
        level: int,
        y_value: float,
        marker_color: QColor,
        left: float,
        top: float,
        side: float,
    ) -> None:
        """
        Draw one open ST3 endpoint marker without covering the data point.
        """
        if not np.isfinite(y_value):
            return

        px = self._x_to_pixel(
            float(level),
            left,
            side,
        )
        py = self._y_to_pixel(
            float(y_value),
            top,
            side,
        )

        radius = 5.4

        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # White halo keeps the marker legible over both the curve and the
        # neutral-gray selection shading.
        halo_pen = QPen(QColor("white"))
        halo_pen.setWidthF(4.0)
        halo_pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(halo_pen)
        painter.drawEllipse(
            QPointF(px, py),
            radius,
            radius,
        )

        marker_pen = QPen(marker_color)
        marker_pen.setWidthF(1.7)
        marker_pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(marker_pen)
        painter.drawEllipse(
            QPointF(px, py),
            radius,
            radius,
        )

        painter.restore()

    def _draw_st3_boundaries(
        self,
        painter: QPainter,
        left: float,
        top: float,
        side: float,
    ) -> None:
        """
        Render red and blue open-circle markers at ST3 region endpoints.
        """
        if not self._show_st3 or self._result is None:
            return

        red_boundaries = self._st3_boundary_levels(
            self._result.red_st3_class
        )
        blue_boundaries = self._st3_boundary_levels(
            self._result.blue_st3_class
        )

        for level in red_boundaries:
            index = int(level) - 1
            self._draw_st3_boundary_marker(
                painter,
                int(level),
                float(self._result.mean_red[index]),
                QColor(ST3_RED_MARKER),
                left,
                top,
                side,
            )

        for level in blue_boundaries:
            index = int(level) - 1
            self._draw_st3_boundary_marker(
                painter,
                int(level),
                float(self._result.mean_blue[index]),
                QColor(ST3_BLUE_MARKER),
                left,
                top,
                side,
            )

        if self._show_st3_labels:
            self._draw_st3_labels(
                painter,
                red_boundaries,
                blue_boundaries,
                left,
                top,
                side,
            )

    def _draw_st3_label_path(
        self,
        painter: QPainter,
        text: str,
        x: float,
        baseline_y: float,
        color: QColor,
        font: QFont,
    ) -> None:
        path = QPainterPath()
        path.addText(
            float(x),
            float(baseline_y),
            font,
            text,
        )

        halo = QPen(QColor("white"))
        halo.setWidthF(3.0)
        halo.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(halo)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawPath(path)

        text_pen = QPen(color)
        text_pen.setWidthF(0.7)
        painter.setPen(text_pen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)

    def _draw_st3_labels(
        self,
        painter: QPainter,
        red_boundaries: np.ndarray,
        blue_boundaries: np.ndarray,
        left: float,
        top: float,
        side: float,
    ) -> None:
        if self._result is None:
            return

        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Weight.DemiBold)
        painter.save()
        painter.setFont(font)
        metrics = painter.fontMetrics()
        occupied: list[QRectF] = []
        label_height = max(12.0, float(metrics.height()))

        items: list[tuple[int, float, QColor, bool]] = []
        for level in red_boundaries:
            index = int(level) - 1
            y_value = float(self._result.mean_red[index])
            if np.isfinite(y_value):
                items.append((int(level), y_value, QColor(ST3_RED_MARKER), True))
        for level in blue_boundaries:
            index = int(level) - 1
            y_value = float(self._result.mean_blue[index])
            if np.isfinite(y_value):
                items.append((int(level), y_value, QColor(ST3_BLUE_MARKER), False))

        items.sort(key=lambda item: (item[0], 0 if item[3] else 1))

        for level, y_value, color, above in items:
            px = self._x_to_pixel(float(level), left, side)
            py = self._y_to_pixel(y_value, top, side)
            text = str(level)
            width = float(metrics.horizontalAdvance(text))
            pad = 3.0

            preferred_x = px - width / 2.0
            preferred_y = (
                py - 5.4 - label_height - 3.0
                if above
                else py + 5.4 + 3.0
            )

            candidate_offsets = [
                (0.0, 0.0),
                (-12.0, 0.0),
                (12.0, 0.0),
                (-24.0, 0.0),
                (24.0, 0.0),
                (0.0, -label_height - 3.0),
                (0.0, label_height + 3.0),
            ]

            chosen = None
            for dx, dy in candidate_offsets:
                x = preferred_x + dx
                y = preferred_y + dy
                x = max(left + pad, min(left + side - width - pad, x))
                y = max(top + pad, min(top + side - label_height - pad, y))
                rect = QRectF(x - pad, y - pad, width + 2 * pad, label_height + 2 * pad)
                if all(not rect.intersects(existing) for existing in occupied):
                    chosen = (x, y, rect)
                    break

            if chosen is None:
                x = max(left + pad, min(left + side - width - pad, preferred_x))
                y = max(top + pad, min(top + side - label_height - pad, preferred_y))
                chosen = (
                    x,
                    y,
                    QRectF(x - pad, y - pad, width + 2 * pad, label_height + 2 * pad),
                )

            x, y, rect = chosen
            self._draw_st3_label_path(
                painter,
                text,
                x,
                y + label_height - 2.0,
                color.darker(125),
                font,
            )
            occupied.append(rect)

        painter.restore()

    # ------------------------------------------------------------------
    # Fit curves
    # ------------------------------------------------------------------

    @staticmethod
    def _fit_curve_values(fit: ExplorerFitResult) -> tuple[np.ndarray, np.ndarray]:
        curve_x = np.linspace(
            float(np.min(fit.x)),
            float(np.max(fit.x)),
            350,
        )

        if fit.model == "Exponential":
            a, b = fit.coefficients
            curve_y = a * np.exp(b * curve_x)
        else:
            curve_y = np.polyval(
                np.asarray(fit.coefficients, dtype=np.float64),
                curve_x,
            )

        finite = np.isfinite(curve_y)
        return curve_x[finite], curve_y[finite]

    def _draw_fit_curve(
        self,
        painter: QPainter,
        fit: Optional[ExplorerFitResult],
        color: QColor,
        left: float,
        top: float,
        side: float,
    ) -> None:
        if fit is None or not fit.valid or fit.x.size < 2:
            return

        curve_x, curve_y = self._fit_curve_values(fit)
        if curve_x.size < 2:
            return

        path = QPainterPath()
        path.moveTo(
            self._x_to_pixel(curve_x[0], left, side),
            self._y_to_pixel(curve_y[0], top, side),
        )

        for cx, cy in zip(curve_x[1:], curve_y[1:]):
            path.lineTo(
                self._x_to_pixel(cx, left, side),
                self._y_to_pixel(cy, top, side),
            )

        painter.setBrush(Qt.BrushStyle.NoBrush)

        halo = QPen(QColor("white"))
        halo.setWidthF(4.4)
        halo.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(halo)
        painter.drawPath(path)

        fit_pen = QPen(color)
        fit_pen.setWidthF(1.8)
        fit_pen.setStyle(Qt.PenStyle.DashDotLine)
        painter.setPen(fit_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    # ------------------------------------------------------------------
    # Pre-build instructions / painting
    # ------------------------------------------------------------------

    def _paint_contents(self, painter: QPainter, include_cursor: bool = True) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))

        # The build state is independent of GSMResult. During a fresh GSM
        # calculation _result is intentionally cleared, so the wait overlay
        # must be painted BEFORE the no-result instructional screen can
        # return. This makes "Please wait..." visible immediately after the
        # user starts Build GSM Graph.
        if self._build_in_progress:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 236)))
            painter.drawRect(self.rect())

            wait_font = QFont("Segoe UI", 17)
            wait_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(wait_font)
            painter.setPen(QColor(105, 110, 105))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Please wait...",
            )
            painter.restore()
            return

        if self._result is None:
            painter.setPen(QColor(TEXT_SECONDARY))
            font = QFont("Segoe UI", 9)
            font.setWeight(QFont.Weight.Normal)
            painter.setFont(font)

            instructions = [
                "1. Open an image.",
                "2. Select the ST1 method in Settings and click Apply ST1.",
                "3. Click Build GSM Graph.",
            ]

            line_height = 21
            block_width = min(400.0, max(260.0, self.width() - 48.0))
            block_left = (self.width() - block_width) / 2.0
            total_height = line_height * len(instructions)
            start_y = self.height() / 2.0 - total_height / 2.0

            for index, text in enumerate(instructions):
                painter.drawText(
                    QRectF(
                        block_left,
                        start_y + index * line_height,
                        block_width,
                        line_height,
                    ),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    text,
                )
            return

        left, top, side = self._plot_rect()

        # Clip all plot shading, points, and analytical curves to the
        # square plot. This is especially important for vector PDF output.
        painter.save()
        painter.setClipRect(
            QRectF(left, top, side, side),
            Qt.ClipOperation.IntersectClip,
        )

        self._draw_selection_shading(
            painter,
            left,
            top,
            side,
        )

        levels = np.asarray(
            self._result.levels,
            dtype=np.float64,
        )

        if self._show_gsm_data:
            self._draw_points(
                painter,
                levels,
                self._result.mean_red,
                QColor(RED_POINT),
                left,
                top,
                side,
            )
            self._draw_points(
                painter,
                levels,
                self._result.green,
                QColor(GREEN_POINT),
                left,
                top,
                side,
            )
            self._draw_points(
                painter,
                levels,
                self._result.mean_blue,
                QColor(BLUE_POINT),
                left,
                top,
                side,
            )

        if self._show_fit:
            self._draw_fit_curve(
                painter,
                self._red_fit,
                QColor(RED_POINT),
                left,
                top,
                side,
            )
            self._draw_fit_curve(
                painter,
                self._blue_fit,
                QColor(BLUE_POINT),
                left,
                top,
                side,
            )

        self._draw_st3_boundaries(
            painter,
            left,
            top,
            side,
        )

        painter.restore()

        # Axes and legend are drawn outside the clip so labels remain clear.
        self._draw_axes(
            painter,
            left,
            top,
            side,
        )
        self._draw_legend(
            painter,
            left,
            top,
            side,
        )
        self._draw_cursor_overlay(
            painter,
            left,
            top,
            side,
        )

        # Build wait state is handled at the top of _paint_contents so it is
        # also visible when no GSMResult exists yet.

    def wheelEvent(self, event) -> None:
        if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            event.ignore()
            return

        left, top, side = self._plot_rect()
        position = event.position()
        if not (
            left <= float(position.x()) <= left + side
            and top <= float(position.y()) <= top + side
        ):
            event.ignore()
            return

        delta = float(event.angleDelta().y())
        if abs(delta) < 1.0:
            delta = float(event.pixelDelta().y()) * 4.0
        if abs(delta) < 1.0:
            event.ignore()
            return

        factor = math.pow(self.ZOOM_STEP, delta / 120.0)
        self._zoom_at_position(factor, position)
        event.accept()

    def mousePressEvent(self, event) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start_pos = event.position()
            self._pan_start_center = QPointF(
                self._view_center_x,
                self._view_center_y,
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return
        event.accept()

    def contextMenuEvent(self, event) -> None:
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            left, top, side = self._plot_rect()
            x_span = 254.0 / self._zoom
            y_span = 255.0 / self._zoom
            delta = event.position() - self._pan_start_pos
            self._view_center_x = self._pan_start_center.x() - delta.x() * x_span / max(1.0, side)
            self._view_center_y = self._pan_start_center.y() + delta.y() * y_span / max(1.0, side)
            self._clamp_view_center()
            self._cursor_level = None
            self.update()
            event.accept()
            return

        level = self._cursor_level_from_position(
            float(event.position().x()),
            float(event.position().y()),
        )
        self._set_cursor_level(level)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.unsetCursor()
            event.accept()
            return
        event.accept()

    def _pan_by_keyboard(self, key: Qt.Key) -> bool:
        if self._result is None or self._zoom <= self.ZOOM_MIN + 1.0e-9:
            return False

        x_min, x_max, y_min, y_max = self._view_ranges()
        x_step = max(1.0e-9, (x_max - x_min) * self.PAN_KEY_FRACTION)
        y_step = max(1.0e-9, (y_max - y_min) * self.PAN_KEY_FRACTION)

        if key == Qt.Key.Key_Left:
            self._view_center_x -= x_step
        elif key == Qt.Key.Key_Right:
            self._view_center_x += x_step
        elif key == Qt.Key.Key_Up:
            self._view_center_y += y_step
        elif key == Qt.Key.Key_Down:
            self._view_center_y -= y_step
        else:
            return False

        self._clamp_view_center()
        self._cursor_level = None
        self.update()
        return True

    def keyPressEvent(self, event) -> None:
        if event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            if self._pan_by_keyboard(event.key()):
                event.accept()
            else:
                event.accept()
            return
        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._zoom_at_position(self.ZOOM_STEP)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Minus:
            self._zoom_at_position(1.0 / self.ZOOM_STEP)
            event.accept()
            return
        if event.key() == Qt.Key.Key_0:
            self.reset_zoom()
            event.accept()
            return
        super().keyPressEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._panning:
            self._set_cursor_level(None)
        event.accept()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        self._paint_contents(painter)
        painter.end()

    # ------------------------------------------------------------------
    # Vector PDF export
    # ------------------------------------------------------------------

    def export_pdf(self, path: Path) -> bool:
        """
        Export the current GSM graph as a professionally composed vector PDF.

        The PDF is an independent print layout on A4 portrait. It is not a
        screenshot of the GUI. All plot marks, axes, labels, legend, and
        analytical curves are drawn directly as vector primitives.
        """
        writer = QPdfWriter(str(path))
        writer.setTitle("Canopy GSM Explorer — GSM Graph")
        writer.setCreator("Canopy GSM for Python")
        writer.setResolution(72)

        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(0, 0, 0, 0),
            QPageLayout.Unit.Point,
        )
        writer.setPageLayout(page_layout)

        painter = QPainter()
        if not painter.begin(writer):
            return False

        try:
            page_width = float(writer.width())
            page_height = float(writer.height())

            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(
                0,
                0,
                int(round(page_width)),
                int(round(page_height)),
                QColor("white"),
            )

            margin = 44.0
            center_x = page_width / 2.0

            # ----------------------------------------------------------
            # Title
            # ----------------------------------------------------------
            title_font = QFont("Segoe UI")
            title_font.setPointSizeF(18.0)
            title_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(title_font)
            painter.setPen(QColor(TEXT_PRIMARY))
            painter.drawText(
                QRectF(margin, 26.0, page_width - 2 * margin, 28.0),
                Qt.AlignmentFlag.AlignCenter,
                "GSM Graph",
            )

            # Deliberate blank line after the title. The application identity
            # remains only in the footer, as requested for the printed figure.

            # ----------------------------------------------------------
            # Compact legend band above the graph
            # ----------------------------------------------------------
            legend_entries = []
            if self._show_gsm_data:
                legend_entries.extend(
                    [
                        ("Mean Red", QColor(RED_POINT), False),
                        ("Green", QColor(GREEN_POINT), False),
                        ("Mean Blue", QColor(BLUE_POINT), False),
                    ]
                )
            if self._show_fit:
                legend_entries.extend(
                    [
                        ("Red fit", QColor(RED_POINT), True),
                        ("Blue fit", QColor(BLUE_POINT), True),
                    ]
                )

            legend_font = QFont("Segoe UI")
            legend_font.setPointSizeF(8.5)
            painter.setFont(legend_font)

            widths = []
            total_width = 0.0
            for text, _color, _is_fit in legend_entries:
                width = painter.fontMetrics().horizontalAdvance(text) + 30.0
                widths.append(width)
                total_width += width

            legend_x = center_x - total_width / 2.0
            legend_y = 76.0

            for idx, (text, color, is_fit) in enumerate(legend_entries):
                if is_fit:
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    halo = QPen(QColor("white"))
                    halo.setWidthF(4.0)
                    painter.setPen(halo)
                    painter.drawLine(
                        int(round(legend_x)),
                        int(round(legend_y)),
                        int(round(legend_x + 13)),
                        int(round(legend_y)),
                    )
                    pen = QPen(color)
                    pen.setWidthF(1.8)
                    pen.setStyle(Qt.PenStyle.DashDotLine)
                    painter.setPen(pen)
                    painter.drawLine(
                        int(round(legend_x)),
                        int(round(legend_y)),
                        int(round(legend_x + 13)),
                        int(round(legend_y)),
                    )
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(
                        int(round(legend_x + 2)),
                        int(round(legend_y - 4)),
                        8,
                        8,
                    )

                painter.setPen(QColor(TEXT_PRIMARY))
                painter.drawText(
                    int(round(legend_x + 16)),
                    int(round(legend_y - 9)),
                    int(round(widths[idx] - 16)),
                    18,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    text,
                )
                legend_x += widths[idx]

            # ----------------------------------------------------------
            # Main square plot
            # ----------------------------------------------------------
            plot_side = 420.0
            plot_top = 108.0
            plot_left = center_x - plot_side / 2.0
            plot_right = plot_left + plot_side
            plot_bottom = plot_top + plot_side

            painter.save()
            painter.setClipRect(
                QRectF(plot_left, plot_top, plot_side, plot_side),
                Qt.ClipOperation.IntersectClip,
            )

            # Selection shading only; never allow brush state to leak into
            # subsequent analytical line/path operations.
            x1 = plot_left + ((self._range_min - 1.0) / 254.0) * plot_side
            x2 = plot_left + ((self._range_max - 1.0) / 254.0) * plot_side

            painter.setPen(Qt.PenStyle.NoPen)
            if self._reverse:
                painter.setBrush(QBrush(QColor(120, 120, 120, 18)))
                painter.drawRect(QRectF(plot_left, plot_top, max(0.0, x1 - plot_left), plot_side))
                painter.drawRect(QRectF(x2, plot_top, max(0.0, plot_right - x2), plot_side))
            else:
                painter.setBrush(QBrush(SELECTION_FILL))
                painter.drawRect(QRectF(x1, plot_top, max(0.0, x2 - x1), plot_side))

            painter.setBrush(Qt.BrushStyle.NoBrush)

            def xpix(value: float) -> float:
                return plot_left + ((float(value) - 1.0) / 254.0) * plot_side

            def ypix(value: float) -> float:
                value = max(0.0, min(255.0, float(value)))
                return plot_top + (1.0 - value / 255.0) * plot_side

            # GSM data points
            levels = np.asarray(self._result.levels if self._result is not None else [], dtype=np.float64)

            if self._show_gsm_data and self._result is not None:
                for xvals, yvals, color in (
                    (levels, self._result.mean_red, QColor(RED_POINT)),
                    (levels, self._result.green, QColor(GREEN_POINT)),
                    (levels, self._result.mean_blue, QColor(BLUE_POINT)),
                ):
                    painter.setPen(Qt.PenStyle.NoPen)
                    for xv, yv in zip(xvals, np.asarray(yvals, dtype=np.float64)):
                        if not np.isfinite(yv):
                            continue
                        level = int(round(xv))
                        inside = self._range_min <= level <= self._range_max
                        selected = (not inside) if self._reverse else inside
                        point_color = color if selected else QColor(OUTSIDE_POINT)
                        radius = 2.9 if selected else 1.9
                        painter.setBrush(QBrush(point_color))
                        px = xpix(xv)
                        py = ypix(yv)
                        painter.drawEllipse(
                            int(round(px - radius)),
                            int(round(py - radius)),
                            int(round(2.0 * radius)),
                            int(round(2.0 * radius)),
                        )

            # Fitted curves. The brush is explicitly disabled so a previous
            # fill can never turn an open curve into a filled region in PDF.
            def draw_fit(fit: Optional[ExplorerFitResult], color: QColor) -> None:
                if fit is None or not fit.valid or fit.x.size < 2:
                    return
                curve_x, curve_y = self._fit_curve_values(fit)
                if curve_x.size < 2:
                    return
                path_obj = QPainterPath()
                path_obj.moveTo(xpix(curve_x[0]), ypix(curve_y[0]))
                for cx, cy in zip(curve_x[1:], curve_y[1:]):
                    path_obj.lineTo(xpix(cx), ypix(cy))

                painter.setBrush(Qt.BrushStyle.NoBrush)
                halo = QPen(QColor("white"))
                halo.setWidthF(4.2)
                halo.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(halo)
                painter.drawPath(path_obj)

                fit_pen = QPen(color)
                fit_pen.setWidthF(1.9)
                fit_pen.setStyle(Qt.PenStyle.DashDotLine)
                painter.setPen(fit_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path_obj)

            if self._show_fit:
                draw_fit(self._red_fit, QColor(RED_POINT))
                draw_fit(self._blue_fit, QColor(BLUE_POINT))

            # ST3 region endpoints are already part of GSMResult. The PDF
            # uses the same open-circle visual language as the live Explorer.
            if self._show_st3 and self._result is not None:
                red_boundaries = self._st3_boundary_levels(
                    self._result.red_st3_class
                )
                blue_boundaries = self._st3_boundary_levels(
                    self._result.blue_st3_class
                )

                def draw_pdf_st3_marker(
                    level: int,
                    y_value: float,
                    color: QColor,
                ) -> None:
                    if not np.isfinite(y_value):
                        return
                    px = xpix(float(level))
                    py = ypix(float(y_value))
                    radius = 5.4

                    halo_pen = QPen(QColor("white"))
                    halo_pen.setWidthF(4.0)
                    halo_pen.setStyle(Qt.PenStyle.SolidLine)
                    painter.setPen(halo_pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(QPointF(px, py), radius, radius)

                    marker_pen = QPen(color)
                    marker_pen.setWidthF(1.7)
                    marker_pen.setStyle(Qt.PenStyle.SolidLine)
                    painter.setPen(marker_pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(QPointF(px, py), radius, radius)

                for level in red_boundaries:
                    index = int(level) - 1
                    draw_pdf_st3_marker(
                        int(level),
                        float(self._result.mean_red[index]),
                        QColor(ST3_RED_MARKER),
                    )

                for level in blue_boundaries:
                    index = int(level) - 1
                    draw_pdf_st3_marker(
                        int(level),
                        float(self._result.mean_blue[index]),
                        QColor(ST3_BLUE_MARKER),
                    )

                if self._show_st3_labels:
                    label_font = QFont("Segoe UI")
                    label_font.setPointSizeF(8.0)
                    label_font.setWeight(QFont.Weight.DemiBold)
                    painter.setFont(label_font)
                    metrics = painter.fontMetrics()
                    occupied: list[QRectF] = []
                    label_height = max(12.0, float(metrics.height()))

                    label_items: list[tuple[int, float, QColor, bool]] = []
                    for level in red_boundaries:
                        index = int(level) - 1
                        y_value = float(self._result.mean_red[index])
                        if np.isfinite(y_value):
                            label_items.append((int(level), y_value, QColor(ST3_RED_MARKER), True))
                    for level in blue_boundaries:
                        index = int(level) - 1
                        y_value = float(self._result.mean_blue[index])
                        if np.isfinite(y_value):
                            label_items.append((int(level), y_value, QColor(ST3_BLUE_MARKER), False))
                    label_items.sort(key=lambda item: (item[0], 0 if item[3] else 1))

                    for level, y_value, color, above in label_items:
                        px = xpix(float(level))
                        py = ypix(float(y_value))
                        text_value = str(level)
                        text_width = float(metrics.horizontalAdvance(text_value))
                        pad = 3.0
                        preferred_x = px - text_width / 2.0
                        preferred_y = (
                            py - 5.4 - label_height - 3.0
                            if above
                            else py + 5.4 + 3.0
                        )
                        offsets = [
                            (0.0, 0.0),
                            (-12.0, 0.0),
                            (12.0, 0.0),
                            (-24.0, 0.0),
                            (24.0, 0.0),
                            (0.0, -label_height - 3.0),
                            (0.0, label_height + 3.0),
                        ]
                        chosen = None
                        for dx, dy in offsets:
                            x0 = max(plot_left + pad, min(plot_right - text_width - pad, preferred_x + dx))
                            y0 = max(plot_top + pad, min(plot_bottom - label_height - pad, preferred_y + dy))
                            rect = QRectF(x0 - pad, y0 - pad, text_width + 2 * pad, label_height + 2 * pad)
                            if all(not rect.intersects(existing) for existing in occupied):
                                chosen = (x0, y0, rect)
                                break
                        if chosen is None:
                            x0 = max(plot_left + pad, min(plot_right - text_width - pad, preferred_x))
                            y0 = max(plot_top + pad, min(plot_bottom - label_height - pad, preferred_y))
                            chosen = (
                                x0,
                                y0,
                                QRectF(x0 - pad, y0 - pad, text_width + 2 * pad, label_height + 2 * pad),
                            )

                        x0, y0, rect = chosen
                        path = QPainterPath()
                        path.addText(
                            x0,
                            y0 + label_height - 2.0,
                            label_font,
                            text_value,
                        )
                        halo_pen = QPen(QColor("white"))
                        halo_pen.setWidthF(3.0)
                        painter.setPen(halo_pen)
                        painter.setBrush(QBrush(QColor("white")))
                        painter.drawPath(path)
                        text_pen = QPen(color.darker(125))
                        text_pen.setWidthF(0.7)
                        painter.setPen(text_pen)
                        painter.setBrush(QBrush(color.darker(125)))
                        painter.drawPath(path)
                        occupied.append(rect)

            painter.restore()

            # Axes and ticks, outside plot clip for clean labels.
            axis_pen = QPen(QColor("#303530"))
            axis_pen.setWidthF(1.25)
            painter.setPen(axis_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(int(round(plot_left)), int(round(plot_bottom)), int(round(plot_right)), int(round(plot_bottom)))
            painter.drawLine(int(round(plot_left)), int(round(plot_top)), int(round(plot_left)), int(round(plot_bottom)))

            tick_font = QFont("Segoe UI")
            tick_font.setPointSizeF(8.5)
            painter.setFont(tick_font)
            painter.setPen(QColor(TEXT_PRIMARY))

            for tick in [1, 64, 128, 192, 255]:
                x = xpix(tick)
                painter.drawLine(int(round(x)), int(round(plot_bottom)), int(round(x)), int(round(plot_bottom + 5)))
                painter.drawText(
                    int(round(x - 20)),
                    int(round(plot_bottom + 7)),
                    40,
                    18,
                    Qt.AlignmentFlag.AlignCenter,
                    str(tick),
                )

            for tick in [0, 64, 128, 192, 255]:
                y = ypix(tick)
                painter.drawLine(int(round(plot_left - 5)), int(round(y)), int(round(plot_left)), int(round(y)))
                painter.drawText(
                    int(round(plot_left - 49)),
                    int(round(y - 9)),
                    42,
                    18,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    str(tick),
                )

            axis_label_font = QFont("Segoe UI")
            axis_label_font.setPointSizeF(10.0)
            axis_label_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(axis_label_font)
            painter.setPen(QColor(TEXT_PRIMARY))

            painter.drawText(
                int(round(plot_left)),
                int(round(plot_bottom + 29)),
                int(round(plot_side)),
                20,
                Qt.AlignmentFlag.AlignCenter,
                "Green level",
            )

            painter.save()
            painter.translate(plot_left - 47.0, plot_top + plot_side / 2.0)
            painter.rotate(-90)
            painter.drawText(
                int(round(-plot_side / 2.0)),
                0,
                int(round(plot_side)),
                20,
                Qt.AlignmentFlag.AlignCenter,
                "Mean RGB value",
            )
            painter.restore()

            # Selection boundaries only; no horizontal or vertical grid lines.
            boundary_pen = QPen(QColor(EPL_GREEN))
            boundary_pen.setWidthF(1.15)
            boundary_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(boundary_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(int(round(x1)), int(round(plot_top)), int(round(x1)), int(round(plot_bottom)))
            painter.drawLine(int(round(x2)), int(round(plot_top)), int(round(x2)), int(round(plot_bottom)))

            # ----------------------------------------------------------
            # Information block under plot
            # ----------------------------------------------------------
            info_top = plot_bottom + 76.0
            info_left = margin
            info_width = page_width - 2 * margin

            heading_font = QFont("Segoe UI")
            heading_font.setPointSizeF(11.0)
            heading_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(heading_font)
            painter.setPen(QColor(TEXT_PRIMARY))
            painter.drawText(
                QRectF(info_left, info_top, info_width, 20.0),
                Qt.AlignmentFlag.AlignCenter,
                "Explorer analysis",
            )

            detail_font = QFont("Segoe UI")
            detail_font.setPointSizeF(9.0)
            painter.setFont(detail_font)
            painter.setPen(QColor(TEXT_SECONDARY))

            selection_text = (
                f"Selection: {self._range_min}–{self._range_max}"
                + (" · Reverse: On" if self._reverse else " · Reverse: Off")
                + (" · GSM data: Visible" if self._show_gsm_data else " · GSM data: Hidden")
                + (" · Fit: Visible" if self._show_fit else " · Fit: Hidden")
            )

            painter.drawText(
                QRectF(info_left, info_top + 25.0, info_width, 18.0),
                Qt.AlignmentFlag.AlignCenter,
                selection_text,
            )

            info_y = info_top + 52.0

            if self._show_fit:
                fit_model_name = self._fit_model
                painter.setPen(QColor(TEXT_PRIMARY))
                painter.drawText(
                    QRectF(info_left, info_y, info_width, 18.0),
                    Qt.AlignmentFlag.AlignCenter,
                    f"Fit model: {fit_model_name}",
                )
                info_y += 23.0

                for fit in (self._red_fit, self._blue_fit):
                    if fit is None:
                        continue
                    channel_color = QColor(RED_POINT if fit.channel == "Red" else BLUE_POINT)
                    painter.setPen(channel_color)
                    painter.drawText(
                        QRectF(info_left, info_y, info_width, 18.0),
                        Qt.AlignmentFlag.AlignCenter,
                        (
                            f"{fit.channel}: "
                            f"{fit.equation if fit.valid else 'fit unavailable'}"
                        ),
                    )
                    info_y += 21.0
                    if fit.valid:
                        painter.setPen(QColor(TEXT_SECONDARY))
                        painter.drawText(
                            QRectF(info_left, info_y, info_width, 18.0),
                            Qt.AlignmentFlag.AlignCenter,
                            f"R² = {fit.rsquare:.5f} · RMSE = {fit.rmse:.5f}",
                        )
                        info_y += 23.0

            painter.setPen(QColor(TEXT_SECONDARY))
            footer_font = QFont("Segoe UI")
            footer_font.setPointSizeF(8.0)
            painter.setFont(footer_font)
            painter.drawText(
                QRectF(margin, page_height - 34.0, page_width - 2 * margin, 18.0),
                Qt.AlignmentFlag.AlignCenter,
                "Canopy GSM for Python · Canopy GSM Explorer",
            )

        finally:
            painter.end()

        return True

# ---------------------------------------------------------------------------
# Scientific worker
# ---------------------------------------------------------------------------

class ExplorerProcessThread(QThread):
    """
    Worker thread for one full GSM scientific analysis.
    """

    progress = Signal(str, int)

    result_ready = Signal(
        int,
        object,
    )

    error = Signal(
        int,
        str,
    )

    def __init__(
        self,
        generation: int,
        image: np.ndarray,
        st1_config: ST1Config,
        st3_m: int,
        st3_p: int,
        background_rgb: tuple[int, int, int],
        parent: QObject | None = None,
    ):
        super().__init__(
            parent
        )

        self._generation = generation

        self._image = image

        self._st1_config = st1_config

        self._st3_m = st3_m
        self._st3_p = st3_p

        self._background_rgb = (
            background_rgb
        )

    def run(self) -> None:

        try:

            def callback(
                stage: str,
                level: int,
            ) -> None:

                self.progress.emit(
                    stage,
                    level,
                )

            result = process_image(
                self._image,
                st1_config=self._st1_config,
                st3_m=self._st3_m,
                st3_p=self._st3_p,
                progress_callback=callback,
                background_rgb=self._background_rgb,
            )

            self.result_ready.emit(
                self._generation,
                result,
            )

        except GSMInputError as exc:

            self.error.emit(
                self._generation,
                str(exc),
            )

        except Exception as exc:

            self.error.emit(
                self._generation,
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )


# ---------------------------------------------------------------------------
# Explorer page
# ---------------------------------------------------------------------------

class ExplorerPage(QWidget):
    """
    Interactive Canopy GSM Explorer.

    Workflow:

        Open Image
            ↓
        Apply ST1
            ↓
        Build GSM Graph
            ↓
        Select Green range
            ↓
        Filter image + graph
            ↓
        Optional fitting
            ↓
        Export
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(
            parent
        )

        self._image: Optional[
            np.ndarray
        ] = None

        self._image_path: Optional[
            Path
        ] = None

        self._st1_mask: Optional[
            np.ndarray
        ] = None

        self._result: Optional[
            GSMResult
        ] = None

        self._thread: Optional[
            ExplorerProcessThread
        ] = None

        self._background_rgb = (
            BACKGROUND_RGB
        )

        self._processing_generation = 0

        self._st1_applied = False

        # Exact ST1 configuration used by the last successful Apply ST1.
        # Exported analysis records use this, not merely the current Settings UI.
        self._applied_st1_config: Optional[ST1Config] = None

        self._build_ui()
        self._connect_signals()

        self._on_st1_method_changed(
            self.st1_method.currentText()
        )

        self._update_background_preview()

        self.image_selection_bar.setStyleSheet(
            f"""
            QFrame {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
            """
        )

        self.range_slider_host.setStyleSheet(
            f"""
            QFrame {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
            """
        )

        self.range_controls_frame.setStyleSheet(
            f"""
            QFrame {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
            QLabel#selectedInfoLabel {{
                background: transparent;
            }}
            """
        )

        QTimer.singleShot(
            0,
            self._sync_range_slider_with_graph,
        )

        self._update_state()

    # ------------------------------------------------------------------
    # Explorer window state
    # ------------------------------------------------------------------

    def showEvent(self, event) -> None:
        """Ensure the Explorer host window opens maximized and stays visible above other windows."""
        super().showEvent(event)
        QTimer.singleShot(0, self._prepare_explorer_window)

    def _prepare_explorer_window(self) -> None:
        """Apply the requested Explorer window presentation once the page is visible."""
        window = self.window()

        if window is self:
            return

        current_flags = window.windowFlags()
        if not (current_flags & Qt.WindowType.WindowStaysOnTopHint):
            window.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint,
                True,
            )
            window.show()

        window.showMaximized()
        window.raise_()
        window.activateWindow()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 16, 22, 16)
        root_layout.setSpacing(8)

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(10)

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("backButton")
        header.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)

        title = QLabel("Canopy GSM Explorer")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Interactive inspection and analysis of a single RGB canopy image."
        )
        subtitle.setObjectName("pageDescription")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout, stretch=1)
        root_layout.addLayout(header)

        # --------------------------------------------------------------
        # Main toolbar — all primary actions in one row
        # --------------------------------------------------------------
        toolbar = QFrame()
        toolbar.setObjectName("explorerToolbar")

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(9, 6, 9, 6)
        toolbar_layout.setSpacing(6)

        self.open_button = QPushButton("Open Image")
        self.open_button.setObjectName("secondaryButton")

        self.apply_st1_button = QPushButton("Apply ST1")
        self.apply_st1_button.setObjectName("secondaryButton")

        self.build_graph_button = QPushButton("Build GSM Graph")
        self.build_graph_button.setObjectName("startButton")

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("secondaryButton")

        self.image_path_edit = QLineEdit()
        self.image_path_edit.setReadOnly(True)
        self.image_path_edit.setPlaceholderText("No image selected")
        self.image_path_edit.setMaximumWidth(300)
        self.image_path_edit.setMinimumWidth(180)

        self.settings_button = QPushButton("⚙ Settings ▼")
        self.settings_button.setObjectName("secondaryButton")

        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("startButton")

        toolbar_layout.addWidget(self.open_button)
        toolbar_layout.addWidget(self.apply_st1_button)
        toolbar_layout.addWidget(self.build_graph_button)
        toolbar_layout.addWidget(self.reset_button)
        toolbar_layout.addWidget(self.image_path_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.export_button)

        root_layout.addWidget(toolbar)

        # Hidden status labels are retained for internal compatibility but do
        # not consume layout space.
        self.status_label = QLabel("Ready.")
        self.progress_label = QLabel("")
        self.analysis_status_label = QLabel("")
        self.range_value_label = QLabel("1 ≤ G ≤ 255")
        self.status_label.setVisible(False)
        self.progress_label.setVisible(False)
        self.analysis_status_label.setVisible(False)
        self.range_value_label.setVisible(False)

        # --------------------------------------------------------------
        # Collapsible Settings
        # --------------------------------------------------------------
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.settings_scroll.setMaximumHeight(235)
        self.settings_scroll.setVisible(False)

        settings_container = QWidget()
        settings_layout = QHBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(10)

        left_settings = QVBoxLayout()
        left_settings.setSpacing(7)

        st1_group = QGroupBox("ST1 Segmentation")
        st1_form = QFormLayout(st1_group)
        st1_form.setContentsMargins(10, 10, 10, 10)

        self.st1_method = QComboBox()
        self.st1_method.addItems([
            "G>R",
            "G>R&G>B",
            "2G-R-B>0",
            "HSV",
            "CUSTOM",
        ])
        st1_form.addRow("Method:", self.st1_method)
        left_settings.addWidget(st1_group)

        self.hsv_group = QGroupBox("HSV Thresholds")
        hsv_form = QFormLayout(self.hsv_group)
        hsv_form.setContentsMargins(10, 10, 10, 10)

        self.h_min = QSpinBox(); self.h_min.setRange(0, 179); self.h_min.setValue(25)
        self.h_max = QSpinBox(); self.h_max.setRange(0, 179); self.h_max.setValue(95)
        self.s_min = QSpinBox(); self.s_min.setRange(0, 255); self.s_min.setValue(40)
        self.s_max = QSpinBox(); self.s_max.setRange(0, 255); self.s_max.setValue(255)
        self.v_min = QSpinBox(); self.v_min.setRange(0, 255); self.v_min.setValue(30)
        self.v_max = QSpinBox(); self.v_max.setRange(0, 255); self.v_max.setValue(255)

        hsv_form.addRow("H min:", self.h_min)
        hsv_form.addRow("H max:", self.h_max)
        hsv_form.addRow("S min:", self.s_min)
        hsv_form.addRow("S max:", self.s_max)
        hsv_form.addRow("V min:", self.v_min)
        hsv_form.addRow("V max:", self.v_max)
        left_settings.addWidget(self.hsv_group)

        self.custom_group = QGroupBox("Custom ST1")
        custom_layout = QHBoxLayout(self.custom_group)
        custom_layout.setContentsMargins(10, 8, 10, 8)

        self.custom_path_edit = QLineEdit()
        self.custom_path_edit.setReadOnly(True)
        self.custom_path_edit.setPlaceholderText(
            "Select a .py file defining create_mask(image)"
        )

        self.custom_button = QPushButton("Browse")
        self.custom_button.setObjectName("secondaryButton")
        custom_layout.addWidget(self.custom_path_edit, stretch=1)
        custom_layout.addWidget(self.custom_button)
        left_settings.addWidget(self.custom_group)

        right_settings = QVBoxLayout()
        right_settings.setSpacing(7)

        st3_group = QGroupBox("ST3")
        st3_form = QFormLayout(st3_group)
        st3_form.setContentsMargins(10, 10, 10, 10)

        self.st3_p = QSpinBox(); self.st3_p.setRange(0, 100000); self.st3_p.setValue(50)
        self.st3_m = QSpinBox(); self.st3_m.setRange(0, 100000); self.st3_m.setValue(12)
        st3_form.addRow("P:", self.st3_p)
        st3_form.addRow("m:", self.st3_m)
        right_settings.addWidget(st3_group)

        background_group = QGroupBox("Processed Image Background")
        background_layout = QHBoxLayout(background_group)
        background_layout.setContentsMargins(10, 8, 10, 8)

        self.background_combo = QComboBox()
        self.background_combo.addItem("Purple (150, 0, 150)", BACKGROUND_RGB)
        self.background_combo.addItem("Custom...", None)

        self.background_preview = QLabel()
        self.background_preview.setObjectName("backgroundPreview")
        self.background_preview.setFixedSize(32, 22)

        self.custom_background_button = QPushButton("Choose")
        self.custom_background_button.setObjectName("secondaryButton")

        background_layout.addWidget(self.background_combo, stretch=1)
        background_layout.addWidget(self.background_preview)
        background_layout.addWidget(self.custom_background_button)
        right_settings.addWidget(background_group)

        self.reset_settings_button = QPushButton("Reset Settings")
        self.reset_settings_button.setObjectName("secondaryButton")
        self.reset_settings_button.setToolTip(
            "Restore ST1, HSV, ST3, Custom ST1, and background settings to defaults."
        )
        right_settings.addWidget(
            self.reset_settings_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        right_settings.addStretch()

        settings_layout.addLayout(left_settings, stretch=1)
        settings_layout.addLayout(right_settings, stretch=1)
        self.settings_scroll.setWidget(settings_container)
        root_layout.addWidget(self.settings_scroll)

        # --------------------------------------------------------------
        # Main visual workspace
        # --------------------------------------------------------------
        self.visual_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.visual_splitter.setChildrenCollapsible(False)

        # Image panel
        image_panel = QFrame()
        image_panel.setObjectName("explorerPanel")
        image_layout = QVBoxLayout(image_panel)
        image_layout.setContentsMargins(11, 9, 11, 9)
        image_layout.setSpacing(5)

        self.image_panel_title = QLabel("Canopy Image")
        self.image_panel_title.setObjectName("panelTitle")

        self.image_preview = ImagePreview()

        self.image_selection_bar = QFrame()
        self.image_selection_bar.setObjectName("imageSelectionBar")
        image_selection_layout = QHBoxLayout(self.image_selection_bar)
        image_selection_layout.setContentsMargins(6, 4, 6, 4)
        image_selection_layout.setSpacing(0)

        self.image_selection_label = QLabel("ST1: not applied")
        self.image_selection_label.setObjectName("selectedInfoLabel")
        self.image_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_selection_layout.addWidget(self.image_selection_label)

        image_layout.addWidget(self.image_panel_title)
        image_layout.addWidget(self.image_preview, stretch=1)
        image_layout.addWidget(self.image_selection_bar)

        # Graph panel
        graph_panel = QFrame()
        graph_panel.setObjectName("explorerPanel")
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(11, 9, 11, 8)
        graph_layout.setSpacing(4)

        graph_title = QLabel("Live GSM Graph")
        graph_title.setObjectName("panelTitle")
        graph_layout.addWidget(graph_title)

        self.graph_widget = GSMGraphWidget()
        graph_layout.addWidget(self.graph_widget, stretch=1)

        self.range_slider_host = QFrame()
        self.range_slider_host.setObjectName("rangeSliderHost")
        self.range_slider_host.setFixedHeight(42)
        slider_host_layout = QHBoxLayout(self.range_slider_host)
        slider_host_layout.setContentsMargins(0, 0, 0, 0)
        slider_host_layout.setSpacing(0)

        self.range_slider = RangeSlider()
        slider_host_layout.addWidget(self.range_slider)
        graph_layout.addWidget(self.range_slider_host)

        self.range_controls_frame = QFrame()
        self.range_controls_frame.setObjectName("rangeControlsFrame")
        range_controls_layout = QHBoxLayout(self.range_controls_frame)
        range_controls_layout.setContentsMargins(8, 3, 8, 3)
        range_controls_layout.setSpacing(5)

        range_controls_layout.addStretch(1)

        min_label = QLabel("Min:")
        min_label.setObjectName("mutedLabel")
        self.range_min_spin = QSpinBox()
        self.range_min_spin.setRange(1, 255)
        self.range_min_spin.setValue(1)

        max_label = QLabel("Max:")
        max_label.setObjectName("mutedLabel")
        self.range_max_spin = QSpinBox()
        self.range_max_spin.setRange(1, 255)
        self.range_max_spin.setValue(255)

        self.reverse_check = QCheckBox("Reverse")
        self.selected_pixels_label = QLabel("Selected: —")
        self.selected_pixels_label.setObjectName("selectedInfoLabel")
        self.selected_pixels_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        range_controls_layout.addWidget(min_label)
        range_controls_layout.addWidget(self.range_min_spin)
        range_controls_layout.addWidget(max_label)
        range_controls_layout.addWidget(self.range_max_spin)
        range_controls_layout.addWidget(self.reverse_check)
        range_controls_layout.addSpacing(10)
        range_controls_layout.addWidget(self.selected_pixels_label)
        range_controls_layout.addStretch(1)

        graph_layout.addWidget(self.range_controls_frame)

        self.visual_splitter.addWidget(image_panel)
        self.visual_splitter.addWidget(graph_panel)
        self.visual_splitter.setStretchFactor(0, 1)
        self.visual_splitter.setStretchFactor(1, 1)
        self.visual_splitter.setSizes([1, 1])

        root_layout.addWidget(self.visual_splitter, stretch=1)

        # --------------------------------------------------------------
        # Compact fitting / live-analysis strip
        # --------------------------------------------------------------
        fit_frame = QFrame()
        fit_frame.setObjectName("fitFrame")
        fit_layout = QVBoxLayout(fit_frame)
        fit_layout.setContentsMargins(9, 5, 9, 5)
        fit_layout.setSpacing(3)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(7)

        self.show_gsm_check = QCheckBox("Show GSM data")
        self.show_gsm_check.setChecked(True)

        self.show_st3_check = QCheckBox("Show ST3")
        self.show_st3_check.setChecked(False)
        self.show_st3_check.setToolTip(
            "Mark the last point of each Red-ST3 and Blue-ST3 region on the graph."
        )

        self.show_st3_labels_check = QCheckBox("Show ST3 labels")
        self.show_st3_labels_check.setChecked(False)
        self.show_st3_labels_check.setToolTip(
            "Show the Green level number next to each visible ST3 boundary marker."
        )

        self.fit_check = QCheckBox("Show fitted curve")

        self.fit_model_combo = QComboBox()
        self.fit_model_combo.addItem("Exponential (GSM reference)")
        self.fit_model_combo.addItem("Polynomial degree 2 (Explorer extension)")

        self.show_cursor_check = QCheckBox("Show cursor details")
        self.show_cursor_check.setChecked(True)
        self.show_cursor_check.setToolTip(
            "Show the live Green, RGB, slope, and ST3 readout while the mouse is over the graph."
        )

        controls_row.addWidget(self.show_gsm_check)
        controls_row.addSpacing(8)
        controls_row.addWidget(self.show_st3_check)
        controls_row.addWidget(self.show_st3_labels_check)
        controls_row.addSpacing(8)
        controls_row.addWidget(self.fit_check)
        controls_row.addWidget(self.fit_model_combo)
        controls_row.addWidget(self.show_cursor_check)
        controls_row.addStretch()

        fit_layout.addLayout(controls_row)

        self.fit_equation_label = QLabel("Fit: —")
        self.fit_equation_label.setObjectName("fitEquationLabel")
        self.fit_equation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fit_equation_label.setWordWrap(True)

        self.fit_stats_label = QLabel("Red: —     Blue: —")
        self.fit_stats_label.setObjectName("fitStatsLabel")
        self.fit_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fit_layout.addWidget(self.fit_equation_label)
        fit_layout.addWidget(self.fit_stats_label)

        root_layout.addWidget(fit_frame)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:

        self.open_button.clicked.connect(
            self._open_image
        )

        self.apply_st1_button.clicked.connect(
            self._apply_st1
        )

        self.build_graph_button.clicked.connect(
            self._build_gsm_graph
        )

        self.reset_button.clicked.connect(
            self._reset_explorer
        )

        self.settings_button.clicked.connect(
            self._toggle_settings
        )

        self.reset_settings_button.clicked.connect(
            self._reset_settings
        )

        self.st1_method.currentTextChanged.connect(
            self._on_st1_method_changed
        )

        self.custom_button.clicked.connect(
            self._browse_custom_st1
        )

        for widget in (
            self.h_min,
            self.h_max,
            self.s_min,
            self.s_max,
            self.v_min,
            self.v_max,
        ):
            widget.valueChanged.connect(
                self._mark_st1_stale
            )

        self.st3_p.valueChanged.connect(
            self._mark_gsm_stale
        )

        self.st3_m.valueChanged.connect(
            self._mark_gsm_stale
        )

        self.background_combo.currentIndexChanged.connect(
            self._background_selection_changed
        )

        self.custom_background_button.clicked.connect(
            self._choose_custom_background
        )

        self.range_slider.rangeChanged.connect(
            self._on_range_slider_changed
        )

        self.range_min_spin.valueChanged.connect(
            self._on_min_spin_changed
        )

        self.range_max_spin.valueChanged.connect(
            self._on_max_spin_changed
        )

        self.reverse_check.toggled.connect(
            self._on_filter_changed
        )

        self.show_gsm_check.toggled.connect(
            self._on_show_gsm_changed
        )

        self.show_st3_check.toggled.connect(
            self._on_show_st3_changed
        )

        self.show_st3_labels_check.toggled.connect(
            self._on_show_st3_labels_changed
        )

        self.fit_check.toggled.connect(
            self._on_fit_changed
        )

        self.fit_model_combo.currentIndexChanged.connect(
            self._on_fit_changed
        )

        self.show_cursor_check.toggled.connect(
            self._on_cursor_visibility_changed
        )

        self.export_button.clicked.connect(
            self._export_all
        )

        self.graph_widget.plotBoundsChanged.connect(
            self._sync_range_slider_with_graph
        )

    # ------------------------------------------------------------------
    # Graph / range-slider geometry
    # ------------------------------------------------------------------

    def _sync_range_slider_with_graph(
        self,
        *_args,
    ) -> None:
        """Align the slider track exactly with the graph x-axis."""
        left, right = (
            self.graph_widget.plot_x_bounds()
        )

        global_left = self.graph_widget.mapToGlobal(
            QPoint(
                int(round(left)),
                0,
            )
        )

        global_right = self.graph_widget.mapToGlobal(
            QPoint(
                int(round(right)),
                0,
            )
        )

        slider_left = self.range_slider.mapFromGlobal(
            global_left
        ).x()

        slider_right = self.range_slider.mapFromGlobal(
            global_right
        ).x()

        self.range_slider.set_track_bounds(
            slider_left,
            slider_right,
        )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _set_settings_expanded(
        self,
        expanded: bool,
    ) -> None:
        """Show or hide the Settings panel and keep the arrow state synchronized."""
        visible = bool(expanded)

        self.settings_scroll.setVisible(
            visible
        )

        self.settings_button.setText(
            "⚙ Settings  ▲"
            if visible
            else
            "⚙ Settings  ▼"
        )

    def _toggle_settings(
        self,
    ) -> None:

        self._set_settings_expanded(
            not self.settings_scroll.isVisible()
        )

    def _reset_settings(self) -> None:
        """Restore the Explorer Settings controls to their scientific defaults."""
        widgets = (
            self.st1_method,
            self.h_min,
            self.h_max,
            self.s_min,
            self.s_max,
            self.v_min,
            self.v_max,
            self.custom_path_edit,
            self.st3_p,
            self.st3_m,
            self.background_combo,
        )

        for widget in widgets:
            widget.blockSignals(True)

        self.st1_method.setCurrentText("G>R")

        self.h_min.setValue(25)
        self.h_max.setValue(95)
        self.s_min.setValue(40)
        self.s_max.setValue(255)
        self.v_min.setValue(30)
        self.v_max.setValue(255)

        self.custom_path_edit.clear()

        self.st3_p.setValue(50)
        self.st3_m.setValue(12)

        self.background_combo.setCurrentIndex(0)
        self._background_rgb = tuple(BACKGROUND_RGB)

        for widget in reversed(widgets):
            widget.blockSignals(False)

        self._update_background_preview()

        if self._image is not None:
            self._processing_generation += 1
            self._st1_applied = False
            self._st1_mask = None
            self._result = None
            self._applied_st1_config = None

            self.image_panel_title.setText("Original Image")
            self.image_preview.set_image(self._image)
            self.image_selection_label.setText(
                "ST1 settings reset — Apply ST1 again."
            )
            self.graph_widget.set_result(None)
            self.graph_widget.set_fit(
                False,
                "Exponential",
                None,
                None,
            )
            self.analysis_status_label.setText(
                "Settings restored to defaults. ST1 has not yet been applied."
            )
            self.status_label.setText(
                "Settings reset to defaults."
            )
            self.progress_label.clear()

        self._update_state()

    def _on_st1_method_changed(
        self,
        method: str,
    ) -> None:

        normalized = (
            method
            .strip()
            .upper()
        )

        self.hsv_group.setEnabled(
            normalized == "HSV"
        )

        self.custom_group.setEnabled(
            normalized == "CUSTOM"
        )

        self._mark_st1_stale()

    def _browse_custom_st1(
        self,
    ) -> None:

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom ST1 Python file",
            str(PROJECT_ROOT),
            "Python files (*.py)",
        )

        if not path:
            return

        self.custom_path_edit.setText(
            path
        )

        self._mark_st1_stale()

    def _build_st1_config(
        self,
    ) -> ST1Config:

        method = (
            self.st1_method
            .currentText()
            .strip()
            .upper()
        )

        custom_path_text = (
            self.custom_path_edit
            .text()
            .strip()
        )

        custom_path = (
            Path(custom_path_text)
            if custom_path_text
            else None
        )

        return ST1Config(
            method=method,
            hsv_h_min=self.h_min.value(),
            hsv_h_max=self.h_max.value(),
            hsv_s_min=self.s_min.value(),
            hsv_s_max=self.s_max.value(),
            hsv_v_min=self.v_min.value(),
            hsv_v_max=self.v_max.value(),
            custom_path=custom_path,
        )

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _background_selection_changed(
        self,
        index: int,
    ) -> None:

        data = (
            self.background_combo
            .itemData(index)
        )

        if data is None:
            return

        self._background_rgb = tuple(
            int(value)
            for value in data
        )

        self._update_background_preview()

        self._refresh_filtered_image()

    def _choose_custom_background(
        self,
    ) -> None:

        initial = QColor(
            *self._background_rgb
        )

        color = QColorDialog.getColor(
            initial,
            self,
            "Choose processed-image background",
        )

        if not color.isValid():
            return

        self._background_rgb = (
            color.red(),
            color.green(),
            color.blue(),
        )

        self.background_combo.blockSignals(
            True
        )

        self.background_combo.setCurrentIndex(
            1
        )

        self.background_combo.blockSignals(
            False
        )

        self._update_background_preview()

        self._refresh_filtered_image()

    def _update_background_preview(
        self,
    ) -> None:

        r, g, b = (
            self._background_rgb
        )

        self.background_preview.setStyleSheet(
            f"""
            QLabel {{
                background: rgb({r}, {g}, {b});
                border: 1px solid #909690;
                border-radius: 4px;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Image
    # ------------------------------------------------------------------

    def _open_image(
        self,
    ) -> None:

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open RGB image",
            str(PROJECT_ROOT),
            (
                "Supported images "
                "(*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp)"
            ),
        )

        if not path:
            return

        try:

            image = load_rgb_uint8(
                Path(path)
            )

        except GSMInputError as exc:

            show_error(
                self,
                "Invalid RGB Image",
                str(exc),
            )

            return

        except Exception as exc:

            show_error(
                self,
                "Image Loading Error",
                (
                    "The selected image could not be loaded.\n\n"
                    f"{type(exc).__name__}: {exc}"
                ),
            )

            return

        self._image = np.asarray(
            image
        ).copy()

        self._image_path = Path(
            path
        )

        self._st1_mask = None
        self._result = None
        self._st1_applied = False
        self._applied_st1_config = None

        self._processing_generation += 1

        self.image_path_edit.setText(
            str(self._image_path)
        )

        self.image_panel_title.setText(
            "Original Image"
        )

        self.image_preview.set_image(
            self._image
        )

        self.image_selection_label.setText(
            "ST1: not applied"
        )

        self.graph_widget.set_result(
            None
        )

        self.graph_widget.set_fit(
            False,
            "Exponential",
            None,
            None,
        )

        self.analysis_status_label.setText(
            "Apply ST1 to extract vegetation from the image."
        )

        self.selected_pixels_label.setText(
            "Selected canopy pixels: —"
        )

        self.analysis_status_label.setText(
            "Image loaded. ST1 has not yet been applied."
        )

        self.range_slider.set_range(
            1,
            255,
            emit_signal=False,
        )

        self.range_min_spin.blockSignals(
            True
        )

        self.range_max_spin.blockSignals(
            True
        )

        self.range_min_spin.setValue(
            1
        )

        self.range_max_spin.setValue(
            255
        )

        self.range_min_spin.blockSignals(
            False
        )

        self.range_max_spin.blockSignals(
            False
        )

        self.reverse_check.setChecked(
            False
        )

        self.fit_check.setChecked(
            False
        )

        self.show_st3_check.setChecked(
            False
        )

        self.status_label.setText(
            "Image loaded."
        )

        self.progress_label.clear()

        self._update_range_labels()

        self._update_fit_display()

        self._update_state()

    # ------------------------------------------------------------------
    # ST1
    # ------------------------------------------------------------------

    def _apply_st1(
        self,
    ) -> None:

        if self._image is None:
            show_warning(
                self,
                "No Image",
                "Open an RGB image before applying ST1.",
            )
            return

        if (
            self._thread is not None
            and self._thread.isRunning()
        ):
            return

        try:

            config = (
                self._build_st1_config()
            )

            mask = segment_st1(
                self._image,
                config,
            )

            processed = make_processed_image(
                self._image,
                mask,
                background_rgb=self._background_rgb,
            )

        except GSMInputError as exc:

            show_error(
                self,
                "ST1 Error",
                str(exc),
            )

            return

        except Exception as exc:

            show_error(
                self,
                "ST1 Error",
                (
                    "ST1 segmentation could not be applied.\n\n"
                    f"{type(exc).__name__}: {exc}"
                ),
            )

            return

        self._st1_mask = np.asarray(
            mask,
            dtype=bool,
        )

        self._applied_st1_config = config
        self._st1_applied = True

        self._result = None

        self._processing_generation += 1

        self.image_panel_title.setText(
            "ST1 Vegetation Extraction"
        )

        self.image_preview.set_image(
            processed
        )

        self._refresh_filtered_image()

        foreground_pixels = int(
            np.count_nonzero(
                self._st1_mask
            )
        )

        self.image_selection_label.setText(
            "ST1 = "
            f"{self.st1_method.currentText()}   ·   "
            f"Vegetation pixels: "
            f"{foreground_pixels:,}"
        )

        self.graph_widget.set_result(
            None
        )

        self.analysis_status_label.setText(
            "ST1 applied. Click Build GSM Graph to calculate GSM."
        )

        self.analysis_status_label.setText(
            "ST1 applied successfully. GSM has not yet been built."
        )

        self.status_label.setText(
            "ST1 applied."
        )

        self.progress_label.clear()

        self._update_state()

    # ------------------------------------------------------------------
    # GSM graph build
    # ------------------------------------------------------------------

    def _build_gsm_graph(
        self,
    ) -> None:

        if self._image is None:
            show_warning(
                self,
                "No Image",
                "Open an RGB image first.",
            )
            return

        if not self._st1_applied:

            show_warning(
                self,
                "ST1 Required",
                "Apply ST1 before building the GSM graph.",
            )

            return

        if (
            self._thread is not None
            and self._thread.isRunning()
        ):
            return

        # Building the GSM graph is the transition into the main analytical
        # workspace. Collapse Settings exactly as if the user had pressed
        # the expanded-state arrow, so the image and graph receive the full
        # available vertical space during and after processing.
        self._set_settings_expanded(False)

        self._result = None

        self._processing_generation += 1

        generation = (
            self._processing_generation
        )

        config = (
            self._build_st1_config()
        )

        self.status_label.setText(
            "Building GSM graph..."
        )

        self.graph_widget.set_build_in_progress(True)

        # Force the wait overlay to be painted immediately, before the
        # worker thread starts. A normal update() is asynchronous in Qt,
        # so the worker could otherwise begin before the user ever sees
        # the "Please wait..." message. This is presentation-only.
        self.graph_widget.repaint()

        self.progress_label.setText(
            "ST2: 0 / 255"
        )

        self.analysis_status_label.setText(
            "Calculating GSM scientific values..."
        )

        self.build_graph_button.setEnabled(
            False
        )

        self.apply_st1_button.setEnabled(
            False
        )

        self._thread = ExplorerProcessThread(
            generation=generation,
            image=self._image.copy(),
            st1_config=config,
            st3_m=self.st3_m.value(),
            st3_p=self.st3_p.value(),
            background_rgb=self._background_rgb,
            parent=self,
        )

        self._thread.progress.connect(
            self._on_progress
        )

        self._thread.result_ready.connect(
            self._on_result_ready
        )

        self._thread.error.connect(
            self._on_processing_error
        )

        self._thread.finished.connect(
            self._on_thread_finished
        )

        self._thread.start()

    def _on_progress(
        self,
        stage: str,
        level: int,
    ) -> None:

        self.progress_label.setText(
            f"{stage}: {level} / 255"
        )

    def _on_result_ready(
        self,
        generation: int,
        result: GSMResult,
    ) -> None:

        if generation != (
            self._processing_generation
        ):

            return

        self._result = result

        self.graph_widget.set_build_in_progress(False)

        self.graph_widget.set_result(
            result
        )

        self._refresh_filtered_image()

        self.analysis_status_label.setText(
            "GSM graph built. Green-range filtering is now active."
        )

        self.analysis_status_label.setText(
            "GSM scientific result is available for interactive inspection."
        )

        self.status_label.setText(
            "GSM graph built."
        )

        self.progress_label.setText(
            "ST2: 255 / 255"
        )

        self._update_explorer_analysis()

        self._update_state()

    def _on_processing_error(
        self,
        generation: int,
        message: str,
    ) -> None:

        if generation != (
            self._processing_generation
        ):

            return

        self.graph_widget.set_build_in_progress(False)

        self.status_label.setText(
            "GSM processing failed."
        )

        self.progress_label.clear()

        show_error(
            self,
            "GSM Processing Error",
            message,
        )

    def _on_thread_finished(
        self,
    ) -> None:

        thread = self._thread

        self._thread = None

        if thread is not None:
            thread.deleteLater()

        self._update_state()

    # ------------------------------------------------------------------
    # Staleness
    # ------------------------------------------------------------------

    def _mark_st1_stale(
        self,
        *args,
    ) -> None:

        del args

        if self._image is None:
            return

        self._processing_generation += 1

        self._st1_applied = False
        self._st1_mask = None
        self._result = None
        self._applied_st1_config = None

        self.image_panel_title.setText(
            "Original Image"
        )

        self.image_preview.set_image(
            self._image
        )

        self.image_selection_label.setText(
            "ST1 settings changed — Apply ST1 again."
        )

        self.graph_widget.set_result(
            None
        )

        self.graph_widget.set_fit(
            False,
            "Exponential",
            None,
            None,
        )

        self.analysis_status_label.setText(
            "ST1 settings changed. Apply ST1 to continue."
        )

        self.analysis_status_label.setText(
            "ST1 result is stale."
        )

        self.status_label.setText(
            "ST1 settings changed."
        )

        self.progress_label.clear()

        self._update_fit_display()

        self._update_state()

    def _mark_gsm_stale(
        self,
        *args,
    ) -> None:

        del args

        if (
            self._image is None
            or not self._st1_applied
        ):
            return

        self._processing_generation += 1

        self._result = None

        self.graph_widget.set_result(
            None
        )

        self.graph_widget.set_fit(
            False,
            "Exponential",
            None,
            None,
        )

        self.analysis_status_label.setText(
            "ST3 settings changed. Build GSM Graph again."
        )

        self.analysis_status_label.setText(
            "GSM result is stale because ST3 settings changed."
        )

        self.status_label.setText(
            "ST3 settings changed."
        )

        self.progress_label.clear()

        self._update_fit_display()

        self._update_state()

    # ------------------------------------------------------------------
    # Range filter
    # ------------------------------------------------------------------

    def _on_range_slider_changed(
        self,
        lower: int,
        upper: int,
    ) -> None:

        self.range_min_spin.blockSignals(
            True
        )

        self.range_max_spin.blockSignals(
            True
        )

        self.range_min_spin.setValue(
            lower
        )

        self.range_max_spin.setValue(
            upper
        )

        self.range_min_spin.blockSignals(
            False
        )

        self.range_max_spin.blockSignals(
            False
        )

        self._on_filter_changed()

    def _on_min_spin_changed(
        self,
        value: int,
    ) -> None:

        if value > (
            self.range_max_spin.value()
        ):

            self.range_max_spin.blockSignals(
                True
            )

            self.range_max_spin.setValue(
                value
            )

            self.range_max_spin.blockSignals(
                False
            )

        self.range_slider.set_range(
            value,
            self.range_max_spin.value(),
            emit_signal=False,
        )

        self._on_filter_changed()

    def _on_max_spin_changed(
        self,
        value: int,
    ) -> None:

        if value < (
            self.range_min_spin.value()
        ):

            self.range_min_spin.blockSignals(
                True
            )

            self.range_min_spin.setValue(
                value
            )

            self.range_min_spin.blockSignals(
                False
            )

        self.range_slider.set_range(
            self.range_min_spin.value(),
            value,
            emit_signal=False,
        )

        self._on_filter_changed()

    def _on_filter_changed(
        self,
        *args,
    ) -> None:

        del args

        self._update_range_labels()

        self._refresh_filtered_image()

        self._update_explorer_analysis()

    def _update_range_labels(
        self,
    ) -> None:

        lower = (
            self.range_min_spin.value()
        )

        upper = (
            self.range_max_spin.value()
        )

        reverse = (
            self.reverse_check.isChecked()
        )

        if reverse:

            self.range_value_label.setText(
                f"Reverse · G < {lower} or G > {upper}"
            )

        else:

            self.range_value_label.setText(
                f"{lower} ≤ G ≤ {upper}"
            )

    # ------------------------------------------------------------------
    # Filtered image
    # ------------------------------------------------------------------

    def _get_display_mask(
        self,
    ) -> Optional[np.ndarray]:

        if (
            self._image is None
            or self._st1_mask is None
        ):

            return None

        green = (
            self._image[:, :, 1]
        )

        lower = (
            self.range_min_spin.value()
        )

        upper = (
            self.range_max_spin.value()
        )

        inside = (
            (green >= lower)
            & (green <= upper)
        )

        reverse = (
            self.reverse_check.isChecked()
        )

        if reverse:

            selected = (
                self._st1_mask
                & ~inside
            )

        else:

            selected = (
                self._st1_mask
                & inside
            )

        return selected

    def _refresh_filtered_image(
        self,
    ) -> None:

        if (
            self._image is None
            or self._st1_mask is None
        ):
            return

        mask = self._get_display_mask()

        if mask is None:
            return

        filtered = make_processed_image(
            self._image,
            mask,
            background_rgb=self._background_rgb,
        )

        self.image_preview.set_image(
            filtered,
            reset_view=False,
        )

        lower = (
            self.range_min_spin.value()
        )

        upper = (
            self.range_max_spin.value()
        )

        reverse = (
            self.reverse_check.isChecked()
        )

        selected_pixels = int(
            np.count_nonzero(
                mask
            )
        )

        total_foreground = int(
            np.count_nonzero(
                self._st1_mask
            )
        )

        self.selected_pixels_label.setText(
            "Selected canopy pixels: "
            f"{selected_pixels:,} / "
            f"{total_foreground:,}"
        )

        if reverse:

            selection_text = (
                f"Reverse selection · "
                f"G < {lower} or G > {upper}"
            )

        else:

            selection_text = (
                f"G = {lower}–{upper}"
            )

        self.image_selection_label.setText(
            "ST1 = "
            f"{self.st1_method.currentText()}   ·   "
            f"{selection_text}   ·   "
            f"Selected: {selected_pixels:,}"
        )

        self.graph_widget.set_selection(
            lower,
            upper,
            reverse,
        )

    # ------------------------------------------------------------------
    # Explorer fitting
    # ------------------------------------------------------------------

    def _on_show_gsm_changed(
        self,
        checked: bool,
    ) -> None:
        self.graph_widget.set_data_visibility(
            checked
        )
        self._update_state()

    def _on_cursor_visibility_changed(
        self,
        checked: bool,
    ) -> None:
        self.graph_widget.set_cursor_visibility(checked)

    def _on_show_st3_changed(
        self,
        checked: bool,
    ) -> None:
        self.graph_widget.set_st3_visibility(checked)
        self.show_st3_labels_check.setEnabled(self._result is not None and checked)
        if not checked and self.show_st3_labels_check.isChecked():
            self.show_st3_labels_check.blockSignals(True)
            self.show_st3_labels_check.setChecked(False)
            self.show_st3_labels_check.blockSignals(False)
            self.graph_widget.set_st3_labels_visibility(False)

    def _on_show_st3_labels_changed(
        self,
        checked: bool,
    ) -> None:
        self.graph_widget.set_st3_labels_visibility(checked and self.show_st3_check.isChecked())

    def _on_fit_changed(
            self,
            *args,
    ) -> None:

        del args

        self._update_explorer_analysis()
        self._update_state()

    def _selected_levels(
        self,
    ) -> Optional[np.ndarray]:

        if self._result is None:
            return None

        levels = np.asarray(
            self._result.levels,
            dtype=np.int16,
        )

        lower = (
            self.range_min_spin.value()
        )

        upper = (
            self.range_max_spin.value()
        )

        inside = (
            (levels >= lower)
            & (levels <= upper)
        )

        if self.reverse_check.isChecked():

            selected = ~inside

        else:

            selected = inside

        return levels[
            selected
        ].astype(
            np.float64
        )

    def _fit_channel(
        self,
        x: np.ndarray,
        y: np.ndarray,
        channel: str,
    ) -> ExplorerFitResult:

        model_text = (
            self.fit_model_combo
            .currentText()
        )

        if model_text.startswith(
            "Exponential"
        ):

            return fit_exponential_selected(
                x,
                y,
                channel,
            )

        return fit_polynomial_selected(
            x,
            y,
            channel,
        )

    def _update_explorer_analysis(
        self,
    ) -> None:

        if self._result is None:

            self.graph_widget.set_fit(
                False,
                "Exponential",
                None,
                None,
            )

            self._update_fit_display()

            return

        x = self._selected_levels()

        if x is None or x.size == 0:

            self.graph_widget.set_fit(
                False,
                "Exponential",
                None,
                None,
            )

            self._update_fit_display()

            return

        levels = np.asarray(
            self._result.levels,
            dtype=np.float64,
        )

        lower = (
            self.range_min_spin.value()
        )

        upper = (
            self.range_max_spin.value()
        )

        inside = (
            (levels >= lower)
            & (levels <= upper)
        )

        if self.reverse_check.isChecked():

            selection = ~inside

        else:

            selection = inside

        x = levels[
            selection
        ]

        red_y = self._result.mean_red[
            selection
        ]

        blue_y = self._result.mean_blue[
            selection
        ]

        red_fit = None
        blue_fit = None

        show_fit = (
            self.fit_check.isChecked()
        )

        model = (
            self.fit_model_combo
            .currentText()
        )

        if show_fit:

            red_fit = self._fit_channel(
                x,
                red_y,
                "Red",
            )

            blue_fit = self._fit_channel(
                x,
                blue_y,
                "Blue",
            )

        self.graph_widget.set_fit(
            show_fit,
            (
                "Exponential"
                if model.startswith(
                    "Exponential"
                )
                else
                "Polynomial degree 2"
            ),
            red_fit,
            blue_fit,
        )

        self._update_fit_display(
            red_fit,
            blue_fit,
        )

        if (
            show_fit
            and model.startswith(
                "Exponential"
            )
        ):

            self.analysis_status_label.setText(
                "Interactive exponential fitting uses the selected Green-level subset. "
                "The standard Batch GSM fit remains unchanged."
            )

        elif (
            show_fit
            and
            model.startswith(
                "Polynomial"
            )
        ):

            self.analysis_status_label.setText(
                "Polynomial degree-2 fitting is an Explorer analytical extension "
                "and is not part of the MATLAB v2.1 GSM reference workflow."
            )

        else:

            self.analysis_status_label.setText(
                "GSM scientific result is available for interactive inspection."
            )

    def _update_fit_display(
        self,
        red_fit: Optional[ExplorerFitResult] = None,
        blue_fit: Optional[ExplorerFitResult] = None,
    ) -> None:

        if not self.fit_check.isChecked():

            self.fit_equation_label.setText(
                "Fit: —"
            )

            self.fit_stats_label.setText(
                "Red: —     Blue: —"
            )

            return

        equations = []

        if (
            red_fit is not None
            and red_fit.valid
        ):

            equations.append(
                f"Red: {red_fit.equation}"
            )

        if (
            blue_fit is not None
            and blue_fit.valid
        ):

            equations.append(
                f"Blue: {blue_fit.equation}"
            )

        if equations:

            self.fit_equation_label.setText(
                "   |   ".join(
                    equations
                )
            )

        else:

            self.fit_equation_label.setText(
                "Fit: unavailable for current selection"
            )

        red_text = "Red: —"

        blue_text = "Blue: —"

        if (
            red_fit is not None
            and red_fit.valid
        ):

            red_text = (
                "Red: "
                f"R²={red_fit.rsquare:.5f}  "
                f"RMSE={red_fit.rmse:.5f}"
            )

        if (
            blue_fit is not None
            and blue_fit.valid
        ):

            blue_text = (
                "Blue: "
                f"R²={blue_fit.rsquare:.5f}  "
                f"RMSE={blue_fit.rmse:.5f}"
            )

        self.fit_stats_label.setText(
            f"{red_text}     {blue_text}"
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset_explorer(
        self,
    ) -> None:

        if self._image is None:
            return

        self.range_slider.set_range(
            1,
            255,
            emit_signal=False,
        )

        self.range_min_spin.blockSignals(
            True
        )

        self.range_max_spin.blockSignals(
            True
        )

        self.range_min_spin.setValue(
            1
        )

        self.range_max_spin.setValue(
            255
        )

        self.range_min_spin.blockSignals(
            False
        )

        self.range_max_spin.blockSignals(
            False
        )

        self.reverse_check.setChecked(
            False
        )

        self.show_gsm_check.setChecked(
            True
        )

        self.fit_check.setChecked(
            False
        )

        self.show_st3_check.setChecked(
            False
        )

        self.show_st3_labels_check.setChecked(
            False
        )

        self.image_preview.reset_zoom()
        self.graph_widget.reset_zoom()

        self.fit_model_combo.setCurrentIndex(
            0
        )

        self._update_range_labels()

        self._refresh_filtered_image()

        self._update_explorer_analysis()

        self.status_label.setText(
            "Explorer selection reset."
        )

    # ------------------------------------------------------------------
    # Export all Explorer outputs
    # ------------------------------------------------------------------

    def _current_fit_results(
        self,
    ) -> tuple[
        Optional[ExplorerFitResult],
        Optional[ExplorerFitResult],
    ]:
        """
        Return fit results for the current interactive selection.
        """
        if (
            self._result is None
            or not self.fit_check.isChecked()
        ):
            return None, None

        levels = np.asarray(
            self._result.levels,
            dtype=np.float64,
        )

        lower = self.range_min_spin.value()
        upper = self.range_max_spin.value()

        inside = (
            (levels >= lower)
            & (levels <= upper)
        )

        selected = (
            ~inside
            if self.reverse_check.isChecked()
            else inside
        )

        x = levels[selected]

        if x.size == 0:
            return None, None

        return (
            self._fit_channel(
                x,
                self._result.mean_red[selected],
                "Red",
            ),
            self._fit_channel(
                x,
                self._result.mean_blue[selected],
                "Blue",
            ),
        )

    def _write_analysis_summary(
        self,
        output: Path,
    ) -> None:
        """
        Write a human-readable record of the exported Explorer state.
        """
        if self._image_path is None:
            return

        lower = self.range_min_spin.value()
        upper = self.range_max_spin.value()
        reverse = self.reverse_check.isChecked()

        total_foreground = (
            int(
                np.count_nonzero(
                    self._st1_mask
                )
            )
            if self._st1_mask is not None
            else 0
        )

        current_mask = (
            self._get_display_mask()
        )

        selected_pixels = (
            int(
                np.count_nonzero(
                    current_mask
                )
            )
            if current_mask is not None
            else 0
        )

        applied_config = self._applied_st1_config
        st1_method = (
            applied_config.method
            if applied_config is not None
            else self.st1_method.currentText().strip().upper()
        )

        lines = [
            "Canopy GSM Explorer",
            f"Software version: {VERSION}",
            "",
            f"Image: {self._image_path.name}",
            f"Image path: {self._image_path}",
            "",
            f"ST1 method: {st1_method}",
        ]

        # Record only ST1 parameters that were actually used for this
        # segmentation. Inactive HSV controls are deliberately omitted.
        if applied_config is not None and st1_method.upper() == "HSV":
            lines.extend(
                [
                    (
                        "HSV H range: "
                        f"{applied_config.hsv_h_min}–{applied_config.hsv_h_max}"
                    ),
                    (
                        "HSV S range: "
                        f"{applied_config.hsv_s_min}–{applied_config.hsv_s_max}"
                    ),
                    (
                        "HSV V range: "
                        f"{applied_config.hsv_v_min}–{applied_config.hsv_v_max}"
                    ),
                ]
            )
        elif (
            applied_config is not None
            and st1_method.upper() == "CUSTOM"
            and applied_config.custom_path is not None
        ):
            lines.append(
                f"Custom ST1 script: {applied_config.custom_path}"
            )

        lines.extend(
            [
                f"ST3 P: {self.st3_p.value()}",
                f"ST3 m: {self.st3_m.value()}",
                (
                    "Background RGB: "
                    f"{self._background_rgb}"
                ),
                "",
                f"Green minimum: {lower}",
                f"Green maximum: {upper}",
                f"Reverse selection: {reverse}",
                f"ST1 vegetation pixels: {total_foreground:,}",
                f"Selected canopy pixels: {selected_pixels:,}",
                (
                    "GSM data visible: "
                    f"{self.show_gsm_check.isChecked()}"
                ),
                (
                    "ST3 markers visible: "
                    f"{self.show_st3_check.isChecked()}"
                ),
                (
                    "ST3 labels visible: "
                    f"{self.show_st3_labels_check.isChecked()}"
                ),
                (
                    "Cursor details visible: "
                    f"{self.show_cursor_check.isChecked()}"
                ),
                "",
                (
                    "Fit enabled: "
                    f"{self.fit_check.isChecked()}"
                ),
                (
                    "Fit model: "
                    f"{self.fit_model_combo.currentText()}"
                ),
            ]
        )

        red_fit, blue_fit = (
            self._current_fit_results()
        )

        if red_fit is not None:
            lines.extend(
                [
                    "",
                    "Red fit:",
                    (
                        "Equation: "
                        f"{red_fit.equation if red_fit.valid else 'unavailable'}"
                    ),
                    (
                        "R²: "
                        f"{self._format_number(red_fit.rsquare)}"
                    ),
                    (
                        "RMSE: "
                        f"{self._format_number(red_fit.rmse)}"
                    ),
                ]
            )

        if blue_fit is not None:
            lines.extend(
                [
                    "",
                    "Blue fit:",
                    (
                        "Equation: "
                        f"{blue_fit.equation if blue_fit.valid else 'unavailable'}"
                    ),
                    (
                        "R²: "
                        f"{self._format_number(blue_fit.rsquare)}"
                    ),
                    (
                        "RMSE: "
                        f"{self._format_number(blue_fit.rmse)}"
                    ),
                ]
            )

        output.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    def _export_all(
        self,
    ) -> None:

        if (
            self._image is None
            or self._st1_mask is None
        ):
            show_warning(
                self,
                "Nothing to Export",
                "Apply ST1 before exporting Explorer results.",
            )
            return

        if self._result is None:
            show_warning(
                self,
                "GSM Graph Required",
                "Build the GSM graph before exporting the complete Explorer result.",
            )
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose Explorer export folder",
            str(
                self._image_path.parent
            ),
        )

        if not directory:
            return

        output_dir = Path(
            directory
        )

        stem = self._image_path.stem

        lower = self.range_min_spin.value()
        upper = self.range_max_spin.value()
        reverse_suffix = (
            "_Reverse"
            if self.reverse_check.isChecked()
            else ""
        )

        processed_path = (
            output_dir
            / (
                f"Explorer_{stem}_Segmented_"
                f"G{lower}-{upper}{reverse_suffix}.png"
            )
        )

        graph_path = (
            output_dir
            / f"Explorer_{stem}_GSM_Graph.pdf"
        )

        csv_path = (
            output_dir
            / f"Explorer_{stem}_GSM_Results.csv"
        )

        summary_path = (
            output_dir
            / f"Explorer_{stem}_Analysis.txt"
        )

        try:

            # ----------------------------------------------------------
            # 1. Current filtered image
            # ----------------------------------------------------------

            current_mask = (
                self._get_display_mask()
            )

            if current_mask is None:
                raise RuntimeError(
                    "The current Explorer selection is unavailable."
                )

            output_image = make_processed_image(
                self._image,
                current_mask,
                background_rgb=self._background_rgb,
            )

            # Full-resolution, lossless RGB export. The image is the original
            # uploaded pixel array with only the display mask applied; it is
            # never resized or captured from the GUI.
            output_image = np.ascontiguousarray(
                output_image,
                dtype=np.uint8,
            )

            save_rgb_uint8(
                output_image,
                processed_path,
            )

            # ----------------------------------------------------------
            # 2. Vector graph PDF
            # ----------------------------------------------------------

            if not self.graph_widget.export_pdf(
                graph_path
            ):
                raise RuntimeError(
                    "The GSM graph PDF could not be created."
                )

            # ----------------------------------------------------------
            # 3. Full GSM data + current Green selection
            # ----------------------------------------------------------

            levels = np.asarray(
                self._result.levels,
                dtype=np.int16,
            )

            inside = (
                (levels >= lower)
                & (levels <= upper)
            )

            selected = (
                ~inside
                if self.reverse_check.isChecked()
                else inside
            )

            records = (
                self._result.as_records()
            )

            fieldnames = (
                self._result.columns
                + ["Selected"]
            )

            with csv_path.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as handle:

                writer = csv.DictWriter(
                    handle,
                    fieldnames=fieldnames,
                )

                writer.writeheader()

                red_fit, blue_fit = (
                    self._current_fit_results()
                )

                interactive_exponential = (
                    self.fit_check.isChecked()
                    and self.fit_model_combo.currentText().startswith(
                        "Exponential"
                    )
                )

                for index, record in enumerate(
                    records
                ):

                    row = dict(
                        record
                    )

                    if index == 0:
                        if interactive_exponential:
                            if red_fit is not None and red_fit.valid:
                                row["R2_exp_Red"] = red_fit.rsquare
                                row["RMSE_exp_Red"] = red_fit.rmse
                                row["exp_a_Red"] = red_fit.coefficients[0]
                                row["exp_b_Red"] = red_fit.coefficients[1]
                            if blue_fit is not None and blue_fit.valid:
                                row["R2_exp_Blue"] = blue_fit.rsquare
                                row["RMSE_exp_Blue"] = blue_fit.rmse
                                row["exp_a_Blue"] = blue_fit.coefficients[0]
                                row["exp_b_Blue"] = blue_fit.coefficients[1]
                        else:
                            row["R2_exp_Red"] = self._result.exp_red.rsquare
                            row["RMSE_exp_Red"] = self._result.exp_red.rmse
                            row["exp_a_Red"] = self._result.exp_red.a
                            row["exp_b_Red"] = self._result.exp_red.b
                            row["R2_exp_Blue"] = self._result.exp_blue.rsquare
                            row["RMSE_exp_Blue"] = self._result.exp_blue.rmse
                            row["exp_a_Blue"] = self._result.exp_blue.a
                            row["exp_b_Blue"] = self._result.exp_blue.b

                    row["Selected"] = (
                        "Yes"
                        if selected[index]
                        else "No"
                    )

                    for key in list(
                        row.keys()
                    ):

                        value = row[key]

                        if value is None:
                            row[key] = ""
                            continue

                        try:

                            numeric = float(
                                value
                            )

                            if np.isnan(
                                numeric
                            ):
                                row[key] = ""

                        except (
                            TypeError,
                            ValueError,
                        ):
                            pass

                    writer.writerow(
                        row
                    )

            # ----------------------------------------------------------
            # 4. Human-readable numeric analysis record
            # ----------------------------------------------------------

            self._write_analysis_summary(
                summary_path
            )

        except Exception as exc:

            show_error(
                self,
                "Export Error",
                (
                    "The Explorer outputs could not be exported.\n\n"
                    f"{type(exc).__name__}: {exc}"
                ),
            )

            return

        show_information(
            self,
            "Export Complete",
            (
                "The complete Explorer result was saved.\n\n"
                f"Processed image:\n{processed_path}\n\n"
                f"Vector graph:\n{graph_path}\n\n"
                f"CSV results:\n{csv_path}\n\n"
                f"Analysis record:\n{summary_path}"
            ),
        )

    # ------------------------------------------------------------------
    # Responsive visual area
    # ------------------------------------------------------------------

    def resizeEvent(
        self,
        event,
    ):
        super().resizeEvent(
            event
        )

        if self.width() < 1040:

            self.visual_splitter.setOrientation(
                Qt.Orientation.Vertical
            )

        else:

            self.visual_splitter.setOrientation(
                Qt.Orientation.Horizontal
            )

        self._sync_range_slider_with_graph()

    # ------------------------------------------------------------------
    # UI state
    # ------------------------------------------------------------------

    def _update_state(self) -> None:
        has_image = self._image is not None
        has_st1 = self._st1_applied and self._st1_mask is not None
        has_result = self._result is not None
        processing = self._thread is not None and self._thread.isRunning()

        self.open_button.setEnabled(not processing)
        self.apply_st1_button.setEnabled(has_image and not processing)
        self.build_graph_button.setEnabled(
            has_image and has_st1 and not has_result and not processing
        )

        self.settings_button.setEnabled(not processing)
        self.export_button.setEnabled(has_result and not processing)

        self.range_slider.setEnabled(has_result)
        self.range_min_spin.setEnabled(has_result)
        self.range_max_spin.setEnabled(has_result)
        self.reverse_check.setEnabled(has_result)
        self.show_gsm_check.setEnabled(has_result)
        self.show_st3_check.setEnabled(has_result)
        self.show_st3_labels_check.setEnabled(has_result and self.show_st3_check.isChecked())
        self.fit_check.setEnabled(has_result)
        self.fit_model_combo.setEnabled(has_result and self.fit_check.isChecked())
        self.show_cursor_check.setEnabled(has_result)

        self.range_slider_host.setVisible(has_result)
        self.range_controls_frame.setVisible(has_result)

    # ------------------------------------------------------------------
    # Number formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_number(
        value,
    ) -> str:
        """Format a finite numeric value for Explorer text output."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "—"

        if not np.isfinite(number):
            return "—"

        absolute = abs(number)

        if (
            absolute != 0
            and (
                absolute < 0.001
                or absolute >= 100000
            )
        ):
            return f"{number:.5e}"

        return f"{number:.5f}"

    # ------------------------------------------------------------------
    # Additional behavior to update state when fit checkbox changes
    # ------------------------------------------------------------------

    def showEvent(
        self,
        event,
    ):
        super().showEvent(
            event
        )

        self._update_state()

    def event(
        self,
        event,
    ):

        result = super().event(
            event
        )

        return result

