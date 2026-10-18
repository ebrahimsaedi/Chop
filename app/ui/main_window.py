"""Main window for Chop."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ui import theme
from app.ui.drop_area import DropArea
from app.ui.worker import SplitWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chop")
        self.resize(520, 720)

        self._files: list[Path] = []
        self._worker: SplitWorker | None = None

        self._build_ui()
        self._apply_theme()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("Chop")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("Split .txt files into equal parts")
        subtitle.setObjectName("dropHint")
        root.addWidget(subtitle)

        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self._add_files)
        self.drop_area.rejected.connect(self._on_rejected)
        root.addWidget(self.drop_area)

        root.addWidget(QLabel("Files"))
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setMaximumHeight(140)
        root.addWidget(self.file_list)

        row_btns = QHBoxLayout()
        add_btn = QPushButton("Add files…")
        add_btn.setObjectName("ghost")
        add_btn.clicked.connect(self._browse)
        remove_btn = QPushButton("Remove selected")
        remove_btn.setObjectName("ghost")
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ghost")
        clear_btn.clicked.connect(self._clear_files)
        row_btns.addWidget(add_btn)
        row_btns.addWidget(remove_btn)
        row_btns.addStretch()
        row_btns.addWidget(clear_btn)
        root.addLayout(row_btns)

        row_parts = QHBoxLayout()
        row_parts.addWidget(QLabel("Split each file into"))

        # --- دکمه‌های سفارشی - و + ---
        btn_minus = QPushButton("−")
        btn_minus.setObjectName("stepBtn")
        btn_minus.setFixedSize(32, 32)

        self.parts_spin = QSpinBox()
        self.parts_spin.setRange(1, 999)
        self.parts_spin.setValue(3)
        self.parts_spin.setAlignment(Qt.AlignCenter)
        self.parts_spin.setButtonSymbols(QSpinBox.NoButtons) # مخفی کردن فلش‌های پیش‌فرض
        self.parts_spin.setFixedWidth(64)

        btn_plus = QPushButton("+")
        btn_plus.setObjectName("stepBtn")
        btn_plus.setFixedSize(32, 32)

        btn_minus.clicked.connect(self.parts_spin.stepDown)
        btn_plus.clicked.connect(self.parts_spin.stepUp)

        row_parts.addWidget(btn_minus)
        row_parts.addWidget(self.parts_spin)
        row_parts.addWidget(btn_plus)
        # --------------------------------

        row_parts.addWidget(QLabel("parts"))
        row_parts.addStretch()
        root.addLayout(row_parts)

        self.split_btn = QPushButton("Split")
        self.split_btn.setMinimumHeight(44)
        self.split_btn.clicked.connect(self._start_split)
        root.addWidget(self.split_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        root.addWidget(QLabel("Log"))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(120)
        root.addWidget(self.log)

    def _apply_theme(self) -> None:
        self.setStyleSheet(theme.stylesheet())

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def _add_files(self, paths: list[Path]) -> None:
        existing = {str(p) for p in self._files}
        added = 0
        for p in paths:
            if str(p) in existing:
                continue
            self._files.append(p)
            item = QListWidgetItem(p.name)
            item.setToolTip(str(p))
            item.setData(Qt.UserRole, str(p))
            self.file_list.addItem(item)
            added += 1
        if added:
            self._log(f"Added {added} file(s). Total: {len(self._files)}.")

    def _on_rejected(self, reason: str) -> None:
        QMessageBox.warning(self, "Chop", reason)

    def _browse(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose .txt files", "", "Text files (*.txt);;All files (*)"
        )
        if files:
            self._add_files([Path(f) for f in files])

    def _remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            path = Path(item.data(Qt.UserRole))
            self._files = [p for p in self._files if p != path]
            self.file_list.takeItem(self.file_list.row(item))

    def _clear_files(self) -> None:
        self._files.clear()
        self.file_list.clear()

    # ------------------------------------------------------------------
    # Splitting
    # ------------------------------------------------------------------

    def _start_split(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not self._files:
            QMessageBox.information(self, "Chop", "Add at least one .txt file first.")
            return

        n = self.parts_spin.value()
        self.log.clear()
        self.progress.setValue(0)
        self._set_busy(True)
        self._log(f"Splitting {len(self._files)} file(s) into {n} parts each…")

        self._worker = SplitWorker(self._files, n, self)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.log.connect(self._log)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _on_finished(self, summary: dict) -> None:
        ok = summary["ok"]
        failed = summary["failed"]
        total = summary["total"]
        self._log(f"Done. {ok}/{total} succeeded.")
        if failed:
            self._log(f"{len(failed)} file(s) failed.")
        else:
            QMessageBox.information(self, "Chop", f"All done! {ok} file(s) split.")

    def _set_busy(self, busy: bool) -> None:
        self.split_btn.setEnabled(not busy)
        self.split_btn.setText("Splitting…" if busy else "Split")
        self.drop_area.setEnabled(not busy)

    def _log(self, msg: str) -> None:
        self.log.appendPlainText(msg)
