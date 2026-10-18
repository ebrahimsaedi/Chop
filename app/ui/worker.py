"""Background worker — keeps the UI responsive during splitting."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.splitter import split_file


class SplitWorker(QThread):
    """Runs `split_file` on a list of files in a background thread."""

    progress = Signal(int)        # 0..100
    log = Signal(str)
    finished_ok = Signal(dict)    # {"ok": int, "failed": [(name, err)], "total": int}

    def __init__(self, files: list[Path], num_parts: int, parent=None):
        super().__init__(parent)
        self._files = list(files)
        self._num_parts = num_parts
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        total = len(self._files)
        if total == 0:
            self.finished_ok.emit({"ok": 0, "failed": [], "total": 0})
            return

        ok = 0
        failed: list[tuple[str, str]] = []

        for i, f in enumerate(self._files, 1):
            if self._cancel:
                self.log.emit("Cancelled.")
                break
            try:
                result = split_file(f, self._num_parts)
                self.log.emit(f"✓ {f.name}  →  {len(result.parts)} parts")
                ok += 1
            except Exception as e:
                self.log.emit(f"✗ {f.name}  →  {e}")
                failed.append((f.name, str(e)))
            self.progress.emit(int(i * 100 / total))

        self.finished_ok.emit({"ok": ok, "failed": failed, "total": total})
