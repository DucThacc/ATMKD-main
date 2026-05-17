from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.styles import get_stylesheet
from app.utils import DEFAULT_THEME


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("WiFi Security Monitor")
    app.setApplicationVersion("2.0")
    app.setStyleSheet(get_stylesheet(DEFAULT_THEME))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

