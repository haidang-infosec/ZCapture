# ZCapture Enterprise Screen Capture System

ZCapture is an enterprise-grade screen capture, floating pin window, vector annotation, and OCR text extraction system designed for Microsoft Windows environments.

---

## 1. Executive Summary

ZCapture is engineered to meet rigorous standards of visual fidelity and execution performance. Combining a modern Windows 11 Fluent Ribbon interface with physical 1:1 pixel rendering, the system ensures seamless capture and annotation workflows.

---

## 2. System Features and Technical Specifications

### 2.1. Physical 1:1 HiDPI Screen Capture & Floating Pin Windows
- **1:1 Pixel-Perfect Rendering**: Direct extraction of raw GPU physical pixel buffers ensuring razor-sharp fidelity on 2K, 4K, and multi-monitor setups.
- **Fluent Ribbon UI**: Minimalist header and mini toolbar interface incorporating clean vector icons and transparent window borders.
- **Unrestricted Window Manipulation**: Header titlebar dragging and real-time resizing operational across all active tool modes.

### 2.2. Vector Graphics Annotation & Sweeping Eraser Engine
- **Continuous Sweeping Eraser**: Drag-to-erase stroke interaction, supported by object deletion shortcuts (`Delete` / `Backspace`) and linear undo/redo stacks (`Ctrl+Z` / `Ctrl+Y`).
- **Dynamic Text Annotation Engine**:
  - Transparent background by default with crisp vector typography.
  - Switchable background modes: Transparent, Dark Badge, and Solid Color Card.
  - Live auto-resizing input box (`QLineEdit`) adjusting dynamically to text input.
  - Double-click interaction to re-edit existing text annotations.
- **Pixel Magnifier & Color Reader**: Real-time pixel magnification loupe with instant RGB and HEX color code extraction.

### 2.3. Asynchronous Windows Native OCR Engine
- Integrated native Windows OCR engine executing on a dedicated background thread (`_OCRWorker`), eliminating interface freezing during text extraction.

### 2.4. Standardized Automated File Naming
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
│   ├── ocr.cs                  # C# source code for native OCR binary
│   └── zcapture_ocr.exe        # Compiled native Windows OCR executable
├── models/                     # Data models and graphic objects
│   ├── annotations.py          # Vector annotation items (TextItem, PathItem, etc.)
│   └── watermark.py            # Watermarking and timestamp overlays
├── ui/                         # User interface components (PyQt6)
│   ├── about_dialog.py         # Application metadata and credits dialog
│   ├── ocr_dialog.py           # OCR text preview and export dialog
│   ├── pin_manager.py          # Floating window lifecycle manager
│   ├── pin_window.py           # Floating pin window component
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
pip install -r requirements.txt
```

---

## 5. Operational Controls and Keyboard Shortcuts

| Shortcut | Execution Command |
| :--- | :--- |
| **`F4`** | Trigger screen capture mode |
| **`Esc`** | Cancel active selection or exit screen overlay |
| **`Enter / Ctrl + C`** | Copy cropped selection to Clipboard and close overlay |
| **`Ctrl + S`** | Save image using standard auto-generated filename |
| **`Ctrl + Z`** | Undo previous drawing action |
| **`Ctrl + Y`** | Redo previously undone drawing action |
| **`Delete / Backspace`** | Delete currently selected annotation object |
| **`Double Click`** | Edit existing text annotation / Close pinned window |

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

## 7. Security, Compliance, and Data Privacy

All temporary evidence logs and temporary image buffers are encapsulated with SHA-256 cryptographic hashes. Ephemeral logs are stored in system temporary space and automatically purged upon process termination to adhere to enterprise security and privacy mandates.
