"""
Canopy GSM for Python
Version: 1.0.0

Application entry point for the Canopy GSM graphical
user interface.

Development note

The software concept, scientific design, methodological
decisions, project direction, and overall development
were led by Abbas Haghshenas; the Python code was
developed with coding assistance from OpenAI's GPT-5.6 Luna.

Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QSplashScreen,
)


# ============================================================================
# Resource paths
# ============================================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent
)

LOGO_PNG = (
    PROJECT_ROOT
    / "CanopyGSM.png"
)

LOGO_ICO = (
    PROJECT_ROOT
    / "CanopyGSM.ico"
)


def resource_path(
    filename: str,
) -> Path:
    """
    Return the path to a bundled application resource.

    Works both when running from source and when running
    from a PyInstaller onedir package.
    """

    return (
        Path(__file__).resolve().parent
        / filename
    )


# ============================================================================
# Application icon
# ============================================================================

def application_icon() -> QIcon:
    """
    Return the official Canopy GSM application icon.

    Preference:
        1. CanopyGSM.ico
        2. CanopyGSM.png
    """

    icon_path = resource_path(
        "CanopyGSM.ico"
    )

    if icon_path.exists():

        icon = QIcon(
            str(icon_path)
        )

        if not icon.isNull():
            return icon

    png_path = resource_path(
        "CanopyGSM.png"
    )

    if png_path.exists():

        icon = QIcon(
            str(png_path)
        )

        if not icon.isNull():
            return icon

    return QIcon()


# ============================================================================
# Top-level exception handling
# ============================================================================

def show_unhandled_exception(
    exc_type,
    exc_value,
    exc_traceback,
) -> None:
    """
    Display an unhandled application exception using
    the official Canopy GSM branding.

    The complete traceback is still printed to stderr
    for development and debugging.
    """

    if issubclass(
        exc_type,
        KeyboardInterrupt,
    ):

        sys.__excepthook__(
            exc_type,
            exc_value,
            exc_traceback,
        )

        return

    # Keep the complete traceback available in the
    # PyCharm terminal / console.
    sys.__excepthook__(
        exc_type,
        exc_value,
        exc_traceback,
    )

    try:

        dialog = QMessageBox()

        dialog.setIcon(
            QMessageBox.Icon.Critical
        )

        dialog.setWindowTitle(
            "Canopy GSM — Application Error"
        )

        dialog.setText(
            "An unexpected error occurred while running Canopy GSM."
        )

        dialog.setInformativeText(
            str(exc_value)
        )

        icon = application_icon()

        if not icon.isNull():

            dialog.setWindowIcon(
                icon
            )

        dialog.exec()

    except Exception:
        # Never allow a failure of the error dialog
        # to hide the original application exception.
        pass


# ============================================================================
# Main application
# ============================================================================

def main() -> int:
    """
    Launch the Canopy GSM desktop application.

    The startup Splash Screen is implemented entirely
    with Qt/PySide6. PyInstaller is only responsible
    for packaging the required resources.
    """

    sys.excepthook = (
        show_unhandled_exception
    )

    # --------------------------------------------------------
    # Create Qt application
    # --------------------------------------------------------

    app = QApplication(
        sys.argv
    )

    # --------------------------------------------------------
    # Application icon
    # --------------------------------------------------------

    icon_path = resource_path(
        "CanopyGSM.ico"
    )

    if icon_path.exists():

        app.setWindowIcon(
            QIcon(
                str(icon_path)
            )
        )

    # --------------------------------------------------------
    # Startup splash
    # --------------------------------------------------------

    splash = None

    splash_path = resource_path(
        "CanopyGSM.png"
    )

    if splash_path.exists():

        pixmap = QPixmap(
            str(splash_path)
        )

        # Keep the Splash reasonably sized on Windows
        # display resolutions while preserving the logo's
        # original aspect ratio.
        #
        # These dimensions intentionally follow the
        # successful Canopy CCGR implementation.

        screen = app.primaryScreen()

        if screen is not None:

            available = (
                screen.availableGeometry()
            )

            max_width = min(
                420,
                int(
                    available.width()
                    * 0.40
                ),
            )

            max_height = min(
                280,
                int(
                    available.height()
                    * 0.40
                ),
            )

            pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        splash = QSplashScreen(
            pixmap
        )

        splash.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            |
            Qt.WindowType.FramelessWindowHint
        )

        splash.show()

        app.processEvents()

    # --------------------------------------------------------
    # Import and create the actual GUI
    # --------------------------------------------------------
    #
    # Importing gui.py here, after the Splash is visible,
    # allows the Splash to appear before the application
    # GUI modules are fully imported.

    from gui import (
        MainWindow,
        create_application,
    )

    # Configure the existing QApplication through the
    # application's centralized Qt configuration.
    app = create_application()

    # --------------------------------------------------------
    # Create and show the main window
    # --------------------------------------------------------

    window = MainWindow()

    window.show()

    app.processEvents()

    # --------------------------------------------------------
    # Close splash after the GUI is visible
    # --------------------------------------------------------

    if splash is not None:

        splash.finish(
            window
        )

        app.processEvents()

    # --------------------------------------------------------
    # Start Qt event loop
    # --------------------------------------------------------

    return app.exec()


# ============================================================================
# Script entry
# ============================================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )