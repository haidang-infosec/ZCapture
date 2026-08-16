import subprocess
import os
import tempfile
import sys
from PyQt6.QtGui import QPixmap

def get_ocr_paths() -> tuple[str, str]:
    """Lấy đường dẫn chính xác cho zcapture_ocr.exe và ocr.cs (tương thích cả khi chạy từ nguồn và file .exe PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = getattr(sys, "_MEIPASS")
        exe_path = os.path.join(base_dir, "core", "zcapture_ocr.exe")
        if not os.path.exists(exe_path):
            exe_path = os.path.join(base_dir, "zcapture_ocr.exe")

        cs_path = os.path.join(base_dir, "core", "ocr.cs")
        if not os.path.exists(cs_path):
            cs_path = os.path.join(base_dir, "ocr.cs")
        return os.path.normpath(exe_path), os.path.normpath(cs_path)

    base_dir = os.path.dirname(__file__)
    return (
        os.path.normpath(os.path.join(base_dir, "zcapture_ocr.exe")),
        os.path.normpath(os.path.join(base_dir, "ocr.cs"))
    )

def ensure_ocr_executable() -> bool:
    """Ensure zcapture_ocr.exe is compiled and ready for instant hardware-accelerated OCR."""
    exe_path, cs_path = get_ocr_paths()
    if os.path.exists(exe_path):
        return True

    if not os.path.exists(cs_path):
        return False

    csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    winmd_path = r"C:\Program Files (x86)\Windows Kits\10\UnionMetadata\10.0.26100.0\Windows.winmd"
    if not os.path.exists(winmd_path):
        winmd_path = r"C:\Windows\System32\WinMetadata\Windows.winmd"

    sys_rt = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Runtime.WindowsRuntime.dll"
    sys_dll = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Runtime.dll"
    sys_tasks = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Threading.Tasks.dll"

    cmd = [
        csc_path, "/target:exe", f'/r:"{winmd_path}"', f'/r:"{sys_rt}"', f'/r:"{sys_dll}"', f'/r:"{sys_tasks}"',
        f'/out:"{exe_path}"', f'"{cs_path}"'
    ]
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.run(" ".join(cmd), shell=True, capture_output=True, check=True, creationflags=flags)
        return os.path.exists(exe_path)
    except Exception as e:
        print(f"[OCR Compiler Error]: {e}")
        return False

def extract_text_from_pixmap(pixmap: QPixmap) -> str:
    """
    Extract text from QPixmap using native zcapture_ocr.exe (Windows Media OCR Engine).
    Returns clean UTF-8 text recognized from the screen region.
    """
    if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
        return ""

    exe_path, _ = get_ocr_paths()
    if not ensure_ocr_executable():
        print("[OCR Error]: Failed to ensure OCR executable.")
        return ""

    # Tên file tạm duy nhất cho mỗi lần gọi, tránh đụng độ khi OCR chạy đồng thời
    fd, tmp_img_path = tempfile.mkstemp(suffix=".png", prefix="zcapture_ocr_")
    os.close(fd)

    try:
        pixmap.save(tmp_img_path, "PNG")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        res = subprocess.run(
            [exe_path, tmp_img_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            creationflags=flags
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"[OCR Exception]: {e}")
        return ""
    finally:
        try:
            if os.path.exists(tmp_img_path):
                os.remove(tmp_img_path)
        except Exception:
            pass
