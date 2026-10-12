# ZCapture Enterprise Screen Capture System

ZCapture is an enterprise-grade screen capture, floating pin window, vector annotation, and OCR text extraction system designed for Microsoft Windows environments.

---

## 1. Executive Summary

ZCapture is engineered to meet rigorous standards of visual fidelity and execution performance. Combining a modern Windows 11 Fluent Ribbon interface with physical 1:1 pixel rendering, the system ensures seamless capture and annotation workflows.

---

## 2. System Features and Technical Specifications

### 2.1. Physical 1:1 HiDPI Screen Capture & Smart Window Snapping
- **Smart Window Snapping & Auto-Detection**: Real-time Win32 DWM detection of active top-level windows and controls. Hovering highlights the window boundary with a clean cutout, and a single click automatically snaps and selects the exact window region.
- **1:1 Pixel-Perfect Rendering**: Direct extraction of raw GPU physical pixel buffers ensuring razor-sharp fidelity on 2K, 4K, and multi-monitor setups.
- **Fluent Ribbon UI**: Minimalist header and mini toolbar interface incorporating clean vector icons and transparent window borders.
- **Smart Right-Click Flow**: Right-click to cancel/commit inline text, deselect objects, reset regions, or exit capture without needing to reach for Esc.

### 2.2. Vector Graphics Annotation & Privacy Obfuscation
- **Live Pixel Magnifier & Instant Color Picker**: Real-time pixel magnification loupe with RGB and HEX color inspector. Press **`C`** to copy the pixel HEX color code directly to the clipboard, and **`Shift`** to toggle HEX / RGB formatting.
- **Continuous Sweeping Eraser**: Drag-to-erase stroke interaction, supported by object deletion shortcuts (`Delete` / `Backspace`) and linear undo/redo stacks (`Ctrl+Z` / `Ctrl+Y`).
- **Comprehensive Annotation Arsenal**:
  - **Shapes**: Rectangle ▢, Circle ○, Straight Line —, Arrow ↗.
  - **Freehand**: Pencil ✏, Dạ quang Highlighter 🖍.
  - **Step Counter**: Incremental numbered badges ① ② ③ for procedural documentation.
  - **Privacy Obfuscation**: Mosaic Pixelate ░░, Soft Gaussian-like Smooth Blur ◌, and Absolute Redact Blackout ██.
- **Dynamic Text Annotation Engine**:
  - Transparent background by default with crisp vector typography.
  - Switchable background modes: Transparent, Dark Badge, and Solid Color Card.
  - Live auto-resizing input box (`QLineEdit`) adjusting dynamically to text input.
  - Double-click interaction to re-edit existing text annotations.

### 2.3. Floating Pin Windows with In-Pin OCR & Image Transformation
- **In-Pin Native OCR**: Directly extract text from any pinned reference image at any time.
- **Geometry Transforms**: Rotate 90° clockwise/counter-clockwise, flip horizontally and vertically.
- **Smooth Opacity Control**: Use `Ctrl + Mouse Wheel` or `Alt + Mouse Wheel` to seamlessly adjust opacity from 15% to 100%.

### 2.4. Asynchronous Windows Native OCR Engine
- Integrated native Windows OCR engine executing on a dedicated background thread (`_OCRWorker`), eliminating interface freezing during text extraction.

### 2.5. Standardized Automated File Naming
- Image captures and pinned windows: `ZCapture_YYYYMMDD_HHMMSS.png` (e.g., `ZCapture_20260802_002245.png`).
- Extracted OCR text files: `ZCapture_OCR_YYYYMMDD_HHMMSS.txt`.

---

## 3. Repository Architecture and Directory Layout

```text
capture-poc/
├── main.py                     # Primary entry point for the PyQt6 application
├── README.md                   # System documentation and technical reference
├── assets/                     # Application icons and legal metadata
│   ├── app_icon.ico
│   └── version_info.txt
├── core/                       # Core system infrastructure
│   ├── config_store.py         # User configuration persistence
│   ├── dpi_utils.py            # HiDPI and multi-monitor scaling utilities
│   ├── ocr_engine.py           # Native OCR interface wrapper
│   ├── screen_grabber.py       # Physical 1:1 screen buffer extractor
│   ├── window_detector.py      # Win32 DWM smart window snapping detector
│   ├── ocr.cs                  # C# source code for native OCR binary
│   └── zcapture_ocr.exe        # Compiled native Windows OCR executable
├── models/                     # Data models and graphic objects
│   ├── annotations.py          # Vector annotation items (LineItem, BlurItem, TextItem, etc.)
│   └── watermark.py            # Watermarking and timestamp overlays
├── ui/                         # User interface components (PyQt6)
│   ├── about_dialog.py         # Application metadata and credits dialog
│   ├── ocr_dialog.py           # OCR text preview and export dialog
│   ├── pin_manager.py          # Floating window lifecycle manager
│   ├── pin_window.py           # Floating pin window with transforms and in-pin OCR
│   ├── settings_window.py      # System configuration panel
│   ├── toolbars.py             # Vector icon generators and toolbar styles
│   ├── widgets.py              # Reusable custom UI components
│   ├── overlay_canvas.py       # Backward compatibility re-export gateway
│   └── overlay/                # Screen capture overlay package
│       ├── canvas_widget.py    # Main ScreenOverlayCanvas controller
│       ├── ocr_worker.py       # Background thread OCR worker
│       ├── rendering_helper.py # Loupe, size badge, and annotation renderers
│       └── sub_toolbars.py     # Property sub-toolbar helpers
└── scripts/                    # Build scripts and deployment tools
    ├── build.ps1               # Automated 1-Click PowerShell build script
    └── ZCapture.spec           # PyInstaller build specification
```

---

## 4. System Requirements and Installation

### 4.1. Runtime Environment
- **Operating System**: Microsoft Windows 10 / Windows 11 (64-bit).
- **Python Runtime**: Python 3.10 or higher.

### 4.2. Dependency Installation
```bash
pip install -r requirements.txt   # chạy; dùng requirements-dev.txt để build
```

---

## 5. Operational Controls and Keyboard Shortcuts

| Shortcut | Execution Command |
| :--- | :--- |
| **`F4` / `Ctrl+Shift+S`** | Trigger screen capture mode |
| **`Single Click`** | Snap and select detected window (Smart Window Snapping) |
| **`Right Click`** | Cancel inline text / Deselect object / Clear region / Exit overlay |
| **`C`** | Copy hovered pixel HEX color code to Clipboard (Live Loupe) |
| **`Shift`** | Toggle color format between HEX and RGB |
| **`Esc`** | Cancel active selection or exit screen overlay |
| **`Enter / Ctrl + C`** | Copy cropped selection to Clipboard and close overlay |
| **`Ctrl + S`** | Save image using standard auto-generated filename |
| **`Ctrl + Z` / `Ctrl + Y`** | Linear Undo / Redo annotation stack |
| **`Delete / Backspace`** | Delete currently selected annotation object |
| **`Double Click`** | Edit existing text annotation / Close pinned window |
| **`Ctrl + Scroll`** | Smoothly adjust pinned window opacity (15% - 100%) |
| **`Mouse Wheel`** | Zoom in / Zoom out pinned window |

---

## 6. Automated Enterprise Build Procedure

The repository provides a single-click PowerShell build script that cleans environment caches, performs syntax checks, and packages the application into a standalone portable executable (`dist/ZCapture.exe`) with zero external Python dependencies.

The build script executes the following stages:
1. Cleans existing `__pycache__` directories and build artifacts (`build/`, `dist/`).
2. Performs syntax compilation across all 22 Python modules.
3. Invokes PyInstaller utilizing `scripts/ZCapture.spec`.

To initiate the build process, execute the following command in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

**Output Artifact**:
`dist/ZCapture.exe` (Standalone Portable Executable, ~54 MB).

---

## 7. Security and Data Privacy

- Ảnh chụp chỉ được xử lý cục bộ; ZCapture không gửi dữ liệu ra mạng.
- OCR ghi ảnh vào một file PNG tạm duy nhất trong thư mục temp của hệ thống, truyền cho `zcapture_ocr.exe` và xóa ngay sau khi xong.
- Cấu hình lưu tại `%APPDATA%\ZCapture\config.json` (không mã hóa, không chứa dữ liệu nhạy cảm).
- Phím tắt toàn cục dùng `pynput.GlobalHotKeys`, chỉ phản hồi tổ hợp phím đã đăng ký.
- `zcapture_ocr.exe` được build từ `core/ocr.cs`; khi phát hành nên tự build lại và ký số cả hai file `.exe`.
