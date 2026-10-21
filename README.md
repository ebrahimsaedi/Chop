# Chop

Chop is an offline desktop utility that partitions large plain text files into smaller, equal-sized segments while preserving semantic boundaries.

Built with Python and PySide6, it uses a deterministic fallback hierarchy to split documents at natural break points without truncating paragraphs, sentences, or words, while normalizing legacy character encodings into standard UTF-8.

![Platform](https://img.shields.io/badge/Platform-Linux%20(x86__64)-grey?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-grey?style=flat-square)
![GUI](https://img.shields.io/badge/GUI-Qt6%20%2F%20PySide6-grey?style=flat-square)
![License](https://img.shields.io/badge/License-GPL--3.0-grey?style=flat-square)

---

## Technical Specifications

| Subsystem | Implementation Details | Behavior & Output |
| :--- | :--- | :--- |
| **Boundary Resolution** | Hierarchical Delimiter Scanner | Scans backward from target byte/char offset: `\n\n` (Paragraph) $\rightarrow$ `\n` (Line) $\rightarrow$ `\s` (Whitespace) |
| **Encoding Normalization** | Heuristic Charset Detector | Reads arbitrary input encodings (`UTF-8`, `Windows-1256`, `ISO-8859-1`, `UTF-16`) and transcodes to clean `UTF-8` |
| **Execution Model** | Asynchronous `QThread` Worker | Non-blocking file I/O and buffer slicing; keeps Qt event loop responsive on multi-megabyte inputs |
| **Ingestion** | Native Qt Drag-and-Drop / File Dialog | Direct path resolution for `.txt` streams |
| **Theming** | System Palette Integration | Follows desktop environment light/dark color schemes |

---

## Partitioning Pipeline

The splitting algorithm avoids mid-word or mid-paragraph truncation by resolving the nearest structural delimiter prior to the target chunk boundary:

~~~text
[Input Text Stream (Arbitrary Encoding)]
       │
       ▼
 [Charset Detection & Transcoding] ──> Decodes to In-Memory UTF-8 Buffer
       │
       ▼
 [Target Offset Calculation]       ──> Total Size / N Parts
       │
       ▼
 [Boundary Resolution Fallback]
       ├── 1. Paragraph Break (\n\n)
       ├── 2. Line Break (\n)
       └── 3. Word Boundary (Whitespace)
       │
       ▼
 [Sequential File Writer]          ──> [part_01.txt, part_02.txt, ... part_N.txt]
~~~

---

## Pre-built Binaries

Standalone x86_64 AppImages are available on the [Releases](../../releases) page. No local Python environment is required.

~~~bash
chmod +x Chop-x86_64.AppImage
./Chop-x86_64.AppImage
~~~

### Systems with FUSE 3 Defaults (Fedora, Arch, Ubuntu 22.04+)
If the AppImage fails to mount or throws an `execv error` due to FUSE 2 dependencies:

~~~bash
./Chop-x86_64.AppImage --appimage-extract-and-run
~~~

Alternatively, install user-space FUSE 2 compatibility:
* Fedora: `sudo dnf install fuse-libs`
* Debian/Ubuntu: `sudo apt install libfuse2`

---

## Building from Source

### Prerequisites
* Python 3.10+

### Environment Setup

~~~bash
git clone https://github.com/your-username/chop.git
cd chop

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
~~~

### Running Locally
~~~bash
python main.py
~~~

### Packaging
Building the standalone executable requires `pyinstaller` and `appimagetool`:

~~~bash
pyinstaller chop.spec
~~~

---

## License

This software is released under the [GNU General Public License v3.0](LICENSE).
