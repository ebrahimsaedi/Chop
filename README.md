# ✂️ Chop - Text File Splitter

Chop is a lightweight, fast, and beautiful desktop application built with Python and PySide6. It allows you to split large text files (like books, scripts, or datasets) into equal, smaller parts without breaking words or paragraphs.

## ✨ Features
- **Smart Splitting**: Automatically finds the best natural break point (paragraphs → lines → words) to keep the text intact.
- **Auto Encoding Detection**: Reads files in almost any encoding (UTF-8, Windows-1256, etc.) and always outputs clean UTF-8 files.
- **Drag & Drop**: Simply drop your `.txt` files into the app.
- **Modern UI**: Supports both Light and Dark themes based on your system settings.
- **Background Processing**: Keeps the UI responsive even with massive files.

## 📥 Download & Install
You don't need Python to run this app. Just go to the **Releases** page, download the `Chop-x86_64.AppImage` file, make it executable, and run it!

## 🛠️ Built With
- [Python 3](https://www.python.org/)
- [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt for Python)
- [PyInstaller](https://pyinstaller.org/) (For packaging)

### 🐧 Note for Fedora Users
If you get an `execv error` when running the AppImage, run it using this terminal command:
`./Chop-x86_64.AppImage --appimage-extract-and-run`

---
*Created with ❤️ for easier reading and translation.*
