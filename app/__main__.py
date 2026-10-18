"""Entry point — run with `python3 -m app` or as a packaged binary."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def _icon_path() -> Path | None:
    """Works both from source and from a PyInstaller bundle."""
    here = Path(__file__).resolve().parent
    for name in ("icon.svg", "icon.png"):
        p = here / "resources" / name
        if p.exists():
            return p
    return None


def main() -> int:
    app = QApplication(sys.argv)

    # --- این خط اضافه شد ---
    app.setStyle("Fusion")
    # -----------------------

    app.setApplicationName("Chop")
    app.setApplicationDisplayName("Chop")

    icon = _icon_path()
    if icon:
        app.setWindowIcon(QIcon(str(icon)))

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
