"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Main graphical user interface.

The scientific GSM engine is implemented separately in gsm_engine.py.
This module contains application-level GUI structure and workflow
navigation.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from batch_gui import BatchPage
from explorer_gui import ExplorerPage
from gsm_engine import VERSION


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

LOGO_PNG = PROJECT_ROOT / "CanopyGSM.png"
LOGO_ICO = PROJECT_ROOT / "CanopyGSM.ico"


# ---------------------------------------------------------------------------
# Application visual identity
# ---------------------------------------------------------------------------

EPL_GREEN = "#57863c"

WINDOW_BACKGROUND = "#f5f6f4"
CARD_BACKGROUND = "#ffffff"
TEXT_PRIMARY = "#202520"
TEXT_SECONDARY = "#5f665f"
BORDER = "#d9ded6"


# ---------------------------------------------------------------------------
# Branding helpers
# ---------------------------------------------------------------------------

def application_icon() -> QIcon:
    """
    Return the application icon.

    Preference:
        1. CanopyGSM.ico
        2. CanopyGSM.png
    """
    if LOGO_ICO.is_file():
        icon = QIcon(str(LOGO_ICO))

        if not icon.isNull():
            return icon

    if LOGO_PNG.is_file():
        icon = QIcon(str(LOGO_PNG))

        if not icon.isNull():
            return icon

    return QIcon()


def logo_pixmap(
    max_width: int = 180,
    max_height: int = 180,
) -> QPixmap:
    """
    Load the official PNG logo and scale it while preserving aspect ratio.
    """
    if not LOGO_PNG.is_file():
        return QPixmap()

    pixmap = QPixmap(str(LOGO_PNG))

    if pixmap.isNull():
        return QPixmap()

    return pixmap.scaled(
        max_width,
        max_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def set_window_branding(
    window: QWidget,
) -> None:
    """
    Apply the Canopy GSM application icon.
    """
    icon = application_icon()

    if not icon.isNull():
        window.setWindowIcon(icon)


def show_error(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """
    Display a branded application error dialog.
    """
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    icon = application_icon()
    if not icon.isNull():
        dialog.setWindowIcon(icon)

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
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    icon = application_icon()
    if not icon.isNull():
        dialog.setWindowIcon(icon)

    dialog.exec()


def show_information(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """
    Display a branded application information dialog.
    """
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Information)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    icon = application_icon()
    if not icon.isNull():
        dialog.setWindowIcon(icon)

    dialog.exec()


# ---------------------------------------------------------------------------
# Responsive logo
# ---------------------------------------------------------------------------

class ResponsiveLogoLabel(QLabel):
    """
    Display the official logo without vertical clipping.

    The original logo is retained and only the display copy is scaled.
    The widget has a bounded vertical area so the launcher remains compact,
    while the pixmap is always fitted inside the actual label geometry.
    """

    def __init__(
        self,
        source_pixmap: QPixmap,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._source_pixmap = source_pixmap

        self.setObjectName("logoLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(124)
        self.setMaximumHeight(158)

        self.setContentsMargins(4, 4, 4, 4)
        self._update_logo()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_logo()

    def _update_logo(self) -> None:
        if self._source_pixmap.isNull():
            self.clear()
            return

        available_width = max(
            1,
            self.width() - self.contentsMargins().left() - self.contentsMargins().right(),
        )
        available_height = max(
            1,
            self.height() - self.contentsMargins().top() - self.contentsMargins().bottom(),
        )

        scaled = self._source_pixmap.scaled(
            available_width,
            available_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(scaled)


# ---------------------------------------------------------------------------
# Workflow card
# ---------------------------------------------------------------------------

class WorkflowCard(QFrame):
    """
    Reusable workflow-selection card.
    """

    clicked = Signal()

    def __init__(
        self,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("workflowCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("workflowTitle")

        description_label = QLabel(description)
        description_label.setObjectName("workflowDescription")
        description_label.setWordWrap(True)

        open_button = QPushButton("Open")
        open_button.setObjectName("workflowButton")
        open_button.clicked.connect(self.clicked.emit)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
        layout.addWidget(
            open_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

class HomePage(QWidget):
    """
    Main workflow-selection page.
    """

    batch_requested = Signal()
    explorer_requested = Signal()
    about_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            50,
            26,
            50,
            22,
        )
        layout.setSpacing(13)

        # ---------------------------------------------------------------
        # Official logo
        # ---------------------------------------------------------------

        pixmap = logo_pixmap(
            max_width=440,
            max_height=320,
        )

        if not pixmap.isNull():
            logo = ResponsiveLogoLabel(pixmap)
            layout.addWidget(
                logo,
                alignment=Qt.AlignmentFlag.AlignHCenter,
            )

        # ---------------------------------------------------------------
        # Application title
        # ---------------------------------------------------------------

        title = QLabel("Canopy GSM")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Scientific image analysis for RGB canopy imagery"
        )
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel(
            f"Version {VERSION} · "
            "MATLAB v2.1 reference-compatible scientific core"
        )
        version.setObjectName("versionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(version)
        layout.addSpacing(5)

        # ---------------------------------------------------------------
        # Workflow selection
        # ---------------------------------------------------------------

        workflow_heading = QLabel("Choose a workflow")
        workflow_heading.setObjectName("sectionTitle")
        workflow_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(workflow_heading)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        batch_card = WorkflowCard(
            "Batch Processing",
            (
                "Process multiple supported RGB images using the same "
                "validated GSM scientific engine and selected analysis settings."
            ),
        )

        explorer_card = WorkflowCard(
            "Canopy GSM Explorer",
            (
                "Interactively inspect a single RGB image, GSM segmentation, "
                "scientific curves, and analysis results."
            ),
        )

        batch_card.clicked.connect(self.batch_requested.emit)
        explorer_card.clicked.connect(self.explorer_requested.emit)

        cards_layout.addWidget(batch_card)
        cards_layout.addWidget(explorer_card)

        layout.addLayout(cards_layout)
        layout.addSpacing(2)

        # ---------------------------------------------------------------
        # RGB input contract
        # ---------------------------------------------------------------

        contract_frame = QFrame()
        contract_frame.setObjectName("contractFrame")

        contract_layout = QVBoxLayout(contract_frame)
        contract_layout.setContentsMargins(24, 15, 24, 15)
        contract_layout.setSpacing(7)

        contract_title = QLabel("Input contract")
        contract_title.setObjectName("contractTitle")

        contract_text = QLabel(
            "Canopy GSM accepts genuine 8-bit, 3-channel RGB images only. "
            "Grayscale, RGBA/four-channel, and non-8-bit images are rejected; "
            "the application does not convert them to make them acceptable."
        )
        contract_text.setObjectName("contractText")
        contract_text.setWordWrap(True)

        contract_layout.addWidget(contract_title)
        contract_layout.addWidget(contract_text)

        layout.addWidget(contract_frame)
        layout.addStretch()

        # ---------------------------------------------------------------
        # Footer
        # ---------------------------------------------------------------

        # The footer is intentionally kept as a simple two-element
        # vertical composition: one centered attribution line followed by
        # the compact About action.  The EPL affiliation is folded into
        # the attribution text so the footer remains visually clean and
        # avoids crowding in the normal-sized launcher window.
        footer_column = QVBoxLayout()
        footer_column.setContentsMargins(0, 10, 0, 0)
        footer_column.setSpacing(9)

        footer_author = QLabel(
            "Scientific concept and methodological direction: "
            "Abbas Haghshenas (Easy-Phenotyping Lab, EPL)"
        )
        footer_author.setObjectName("footerAuthor")
        footer_author.setAlignment(Qt.AlignmentFlag.AlignCenter)

        about_button = QPushButton("About")
        about_button.setObjectName("aboutButton")
        about_button.setToolTip(
            "About Canopy GSM for Python"
        )
        about_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        about_button.clicked.connect(self.about_requested.emit)

        footer_column.addWidget(
            footer_author,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        footer_column.addWidget(
            about_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addLayout(footer_column)


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """
    Main Canopy GSM application window.
    """

    def __init__(self):
        super().__init__()

        set_window_branding(self)

        self.setWindowTitle("Canopy GSM")

        # The Launcher is a normal-sized window, but it should remain above
        # other applications so the user can always choose a workflow.
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            True,
        )

        self._workflow_mode = False

        self.resize(1180, 760)
        self.setMinimumSize(980, 650)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # ---------------------------------------------------------------
        # Pages
        # ---------------------------------------------------------------

        self.home_page = HomePage()
        self.batch_page = BatchPage()
        self.explorer_page = ExplorerPage()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.batch_page)
        self.stack.addWidget(self.explorer_page)

        # ---------------------------------------------------------------
        # Navigation
        # ---------------------------------------------------------------

        self.home_page.batch_requested.connect(
            self._open_batch_workflow
        )

        self.home_page.explorer_requested.connect(
            self._open_explorer_workflow
        )

        self.home_page.about_requested.connect(
            self._show_about
        )

        self.batch_page.back_button.clicked.connect(
            self._return_to_launcher
        )

        self.explorer_page.back_button.clicked.connect(
            self._return_to_launcher
        )

        # ---------------------------------------------------------------
        # Application-wide visual styling
        # ---------------------------------------------------------------

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {WINDOW_BACKGROUND};
            }}

            QWidget {{
                background: {WINDOW_BACKGROUND};
                color: {TEXT_PRIMARY};
                font-family: "Segoe UI";
            }}

            QLabel#logoLabel {{
                background: transparent;
                min-height: 124px;
                max-height: 158px;
            }}

            QLabel#appTitle {{
                font-size: 34px;
                font-weight: 700;
                color: {TEXT_PRIMARY};
            }}

            QLabel#appSubtitle {{
                font-size: 18px;
                color: {TEXT_SECONDARY};
            }}

            QLabel#versionLabel {{
                font-size: 12px;
                color: {TEXT_SECONDARY};
            }}

            QLabel#sectionTitle {{
                font-size: 20px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
            }}

            QFrame#workflowCard {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}

            QFrame#workflowCard:hover {{
                border: 2px solid {EPL_GREEN};
            }}

            QLabel#workflowTitle {{
                font-size: 22px;
                font-weight: 650;
                color: {TEXT_PRIMARY};
                background: transparent;
            }}

            QLabel#workflowDescription {{
                font-size: 14px;
                color: {TEXT_SECONDARY};
                background: transparent;
            }}

            QPushButton#workflowButton {{
                background: {EPL_GREEN};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-size: 14px;
                font-weight: 600;
            }}

            QPushButton#workflowButton:hover {{
                background: #496f32;
            }}

            QPushButton#workflowButton:pressed {{
                background: #3f602b;
            }}

            QFrame#contractFrame {{
                background: #eef3eb;
                border: 1px solid #cfdcc7;
                border-radius: 10px;
            }}

            QLabel#contractTitle {{
                font-size: 15px;
                font-weight: 700;
                color: {EPL_GREEN};
                background: transparent;
            }}

            QLabel#contractText {{
                font-size: 13px;
                color: {TEXT_PRIMARY};
                background: transparent;
            }}

            QLabel#footerAuthor {{
                font-size: 11px;
                color: {TEXT_SECONDARY};
                background: transparent;
            }}

            QPushButton#aboutButton {{
                background: white;
                color: {EPL_GREEN};
                border: 1px solid {EPL_GREEN};
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 600;
            }}

            QPushButton#aboutButton:hover {{
                background: #eef3eb;
            }}

            QPushButton#aboutButton:pressed {{
                background: #e2ecdf;
            }}

            QPushButton#backButton {{
                background: transparent;
                color: {EPL_GREEN};
                border: none;
                padding: 6px 2px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton#backButton:hover {{
                color: #3f602b;
            }}

            QLabel#pageTitle {{
                font-size: 30px;
                font-weight: 700;
                color: {TEXT_PRIMARY};
            }}

            QLabel#pageDescription {{
                font-size: 16px;
                color: {TEXT_SECONDARY};
            }}

            QFrame#explorerControlFrame {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 9px;
            }}

            QFrame#explorerVisualFrame {{
                background: transparent;
                border: none;
            }}

            QFrame#explorerPanel {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}

            QLabel#panelTitle {{
                font-size: 15px;
                font-weight: 700;
                color: {TEXT_PRIMARY};
                background: transparent;
            }}

            QLabel#selectedLevelLabel {{
                font-size: 11px;
                color: {TEXT_SECONDARY};
                background: transparent;
                padding: 4px 2px;
            }}

            QGroupBox {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 9px;
                margin-top: 12px;
                padding-top: 10px;
                font-size: 13px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                background: {CARD_BACKGROUND};
            }}

            QLineEdit,
            QComboBox,
            QSpinBox {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 28px;
                color: {TEXT_PRIMARY};
            }}

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus {{
                border: 2px solid {EPL_GREEN};
            }}

            QPushButton#secondaryButton {{
                background: white;
                color: {EPL_GREEN};
                border: 1px solid {EPL_GREEN};
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton#secondaryButton:hover {{
                background: #eef3eb;
            }}

            QPushButton#startButton {{
                background: {EPL_GREEN};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 700;
            }}

            QPushButton#startButton:hover {{
                background: #496f32;
            }}

            QPushButton#startButton:disabled {{
                background: #aeb8a8;
            }}

            QLabel#batchStatus {{
                font-size: 13px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
                background: transparent;
            }}

            QLabel#mutedLabel {{
                font-size: 11px;
                color: {TEXT_SECONDARY};
                background: transparent;
            }}

            QLabel#backgroundPreview {{
                background: white;
                border: 1px solid #909690;
                border-radius: 4px;
            }}

            QCheckBox {{
                color: {TEXT_PRIMARY};
                spacing: 6px;
            }}

            QScrollArea {{
                background: transparent;
            }}
            """
        )

        self.stack.setCurrentWidget(self.home_page)

    # ---------------------------------------------------------------
    # About dialog
    # ---------------------------------------------------------------

    def _show_about(self) -> None:
        """Show the Canopy GSM application information dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("About Canopy GSM")
        dialog.setModal(True)
        dialog.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            True,
        )
        dialog.setMinimumSize(650, 500)
        dialog.resize(680, 520)
        set_window_branding(dialog)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 22, 28, 20)
        layout.setSpacing(9)

        # -----------------------------------------------------------
        # Compact branded header
        # -----------------------------------------------------------

        header_logo_pixmap = logo_pixmap(
            max_width=120,
            max_height=76,
        )

        if not header_logo_pixmap.isNull():
            header_logo = QLabel()
            header_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_logo.setPixmap(header_logo_pixmap)
            layout.addWidget(header_logo)

        title = QLabel("Canopy GSM for Python")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"""
            QLabel {{
                color: {EPL_GREEN};
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }}
            """
        )

        version = QLabel(f"Version {VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 10pt;
                background: transparent;
            }}
            """
        )

        layout.addWidget(title)
        layout.addWidget(version)

        # -----------------------------------------------------------
        # Information body
        # -----------------------------------------------------------

        info = QTextBrowser()
        info.setOpenExternalLinks(True)
        info.setFrameShape(QFrame.Shape.NoFrame)
        info.setStyleSheet(
            f"""
            QTextBrowser {{
                background: transparent;
                color: {TEXT_PRIMARY};
                border: none;
                font-family: "Segoe UI";
                font-size: 9.5pt;
            }}
            QTextBrowser a {{
                color: {EPL_GREEN};
                text-decoration: none;
            }}
            QTextBrowser a:hover {{
                text-decoration: underline;
            }}
            """
        )

        info.setHtml(
            f"""
            <p>
              <b>Canopy GSM for Python</b> is a research-oriented image-analysis
              application built around the Green-gradient based canopy
              segmentation model (GSM) for quantitative analysis of RGB canopy imagery.
            </p>

            <p>
              <b>Scientific basis</b><br>
              Haghshenas, A. &amp; Emam, Y. (2020).<br>
              <i>Green-gradient based canopy segmentation: A multipurpose image
              mining model with potential use in crop phenotyping and canopy studies.</i><br>
              <a href="https://doi.org/10.1016/j.compag.2020.105740">
                DOI: 10.1016/j.compag.2020.105740
              </a>
            </p>

            <p>
              <b>Historical MATLAB implementation</b><br>
              Canopy GSM — MATLAB v2<br>
              <a href="https://codeocean.com/capsule/1652693/tree/v2">
                Code Ocean capsule
              </a>
            </p>

            <p>
              <b>Current Python implementation</b><br>
              This release is a new Python software line rather than a new MATLAB
              version number. The scientific GSM core is maintained independently
              and follows the established MATLAB reference workflow.
            </p>

            <p>
              <b>Developer</b><br>
              Abbas Haghshenas — Easy-Phenotyping Lab (EPL)<br>
              <a href="https://haqueshenas.github.io/EPL/">
                Easy-Phenotyping Lab (EPL)
              </a>
            </p>

            <p>
              <b>Development</b><br>
              The software concept, scientific design, methodological decisions,
              project direction, and overall development were led by Abbas Haghshenas;
              the Python code was developed with coding assistance from
              OpenAI's GPT-5.6 Luna.
            </p>

            <p>
              <b>License</b>: MIT License<br>
              Copyright (c) 2026 Abbas Haghshenas
            </p>
            """
        )

        layout.addWidget(info, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        # Center on the active Canopy GSM window.
        geometry = dialog.frameGeometry()
        geometry.moveCenter(self.frameGeometry().center())
        dialog.move(geometry.topLeft())

        dialog.exec()

    # ---------------------------------------------------------------
    # Window presentation and workflow navigation
    # ---------------------------------------------------------------

    def showEvent(self, event) -> None:
        """Keep the Launcher normal-sized, foregrounded, and always on top."""
        super().showEvent(event)

        if not self._workflow_mode:
            QTimer.singleShot(
                0,
                self._present_launcher,
            )

    def _present_launcher(self) -> None:
        """Present the Home/Launcher state without maximizing the window."""
        if self._workflow_mode:
            return

        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _present_workflow(self) -> None:
        """Present a workflow as a maximized, always-on-top application window."""
        self.showMaximized()
        self.raise_()
        self.activateWindow()

    def _open_batch_workflow(self) -> None:
        """Open Batch Processing in the maximized foreground application window."""
        self._workflow_mode = True
        self.stack.setCurrentWidget(self.batch_page)
        self._present_workflow()

    def _open_explorer_workflow(self) -> None:
        """Open Explorer in the maximized foreground application window."""
        self._workflow_mode = True
        self.stack.setCurrentWidget(self.explorer_page)
        self._present_workflow()

    def _return_to_launcher(self) -> None:
        """Return from a workflow to the normal-sized Launcher state."""
        self._workflow_mode = False
        self.stack.setCurrentWidget(self.home_page)
        self.showNormal()
        self.resize(1180, 760)
        self.raise_()
        self.activateWindow()


# ---------------------------------------------------------------------------
# Qt application creation
# ---------------------------------------------------------------------------

def create_application() -> QApplication:
    """
    Create and configure the Qt application instance.
    """
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    app.setApplicationName("Canopy GSM")
    app.setApplicationDisplayName("Canopy GSM")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("Abbas Haghshenas")

    icon = application_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)

    return app
