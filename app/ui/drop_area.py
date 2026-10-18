"""Drag & drop zone for .txt files."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout


class DropArea(QFrame):
    """
    A dashed drop zone. Emits `filesDropped(list[Path])` when the user
    drops .txt files onto it, or clicks to browse.

    Non-.txt files are silently ignored (with a small visual shake-free
    signal via `rejected`).
    """

    filesDropped = Signal(list)   # list[Path]
    rejected = Signal(str)        # reason

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setProperty("dragging", "false")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._hint = QLabel("Drop .txt files here\nor click to browse")
        self._hint.setObjectName("dropHint")
        self._hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._hint)

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(u.toLocalFile().lower().endswith(".txt") for u in urls):
            event.acceptProposedAction()
            self._set_dragging(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_dragging(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_dragging(False)
        paths: list[Path] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if not local:
                continue
            p = Path(local)
            if p.is_file() and p.suffix.lower() == ".txt":
                paths.append(p)

        if paths:
            event.acceptProposedAction()
            self.filesDropped.emit(paths)
        else:
            event.ignore()
            self.rejected.emit("Only .txt files are supported.")

    # ------------------------------------------------------------------
    # Click to browse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Choose .txt files",
                "",
                "Text files (*.txt);;All files (*)",
            )
            if files:
                self.filesDropped.emit([Path(f) for f in files])
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # Visual feedback
    # ------------------------------------------------------------------

    def _set_dragging(self, active: bool):
        self.setProperty("dragging", "true" if active else "false")
        # Force QSS re-evaluation for the property selector
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
