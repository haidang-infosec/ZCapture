import sys
import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QRect, QPoint

DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_CLOAKED = 14


class WindowDetector:
    """
    Win32 Window Detection Engine.
    Tự động phát hiện vị trí và kích thước (bounding box) của các cửa sổ và control
    đang hiển thị trên màn hình để phục vụ tính năng Smart Window Snapping.
    """

    def __init__(self, exclude_hwnds=None):
        self.exclude_hwnds = set(exclude_hwnds or [])
        self.user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self.dwmapi = ctypes.windll.dwmapi if sys.platform == "win32" else None

    def get_visible_windows(self, virtual_offset: QPoint = QPoint(0, 0)) -> list[dict]:
        """
        Quét và trả về danh sách các cửa sổ đang hiển thị theo thứ tự Z-Order (từ trên xuống dưới).
        Mỗi phần tử gồm: {'hwnd': hwnd, 'rect': QRect, 'title': str}
        Tọa độ 'rect' được điều chỉnh theo virtual_offset (cho môi trường đa màn hình).
        """
        if not self.user32 or not self.dwmapi:
            return []

        windows = []

        def enum_callback(hwnd, lparam):
            if hwnd in self.exclude_hwnds:
                return True
            if not self.user32.IsWindowVisible(hwnd):
                return True
            if self.user32.IsIconic(hwnd):
                return True

            # Bỏ qua cửa sổ bị Cloaked (Windows Virtual Desktops hoặc UWP app đang ẩn)
            cloaked = wintypes.DWORD()
            self.dwmapi.DwmGetWindowAttribute(
                hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
            )
            if cloaked.value != 0:
                return True

            rect = wintypes.RECT()
            hr = self.dwmapi.DwmGetWindowAttribute(
                hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(rect), ctypes.sizeof(rect)
            )
            if hr != 0:
                self.user32.GetWindowRect(hwnd, ctypes.byref(rect))

            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w < 40 or h < 40:
                return True

            # Chuyển đổi sang hệ tọa độ của Overlay Canvas (trừ virtual desktop offset)
            qrect = QRect(
                rect.left - virtual_offset.x(),
                rect.top - virtual_offset.y(),
                w,
                h
            )

            length = self.user32.GetWindowTextLengthW(hwnd)
            title = ""
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value

            windows.append({
                "hwnd": hwnd,
                "rect": qrect,
                "title": title
            })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb = WNDENUMPROC(enum_callback)

        # Thử lấy desktop handle từ OpenInputDesktop
        hdesk = self.user32.OpenInputDesktop(0, False, 0x0100)
        if not hdesk:
            hdesk = self.user32.OpenDesktopW("Default", 0, False, 0x0100)

        if hdesk:
            self.user32.EnumDesktopWindows(hdesk, cb, 0)
        else:
            self.user32.EnumWindows(cb, 0)

        return windows

    def find_window_at(self, pos: QPoint, windows: list[dict]) -> dict | None:
        """
        Tìm cửa sổ nằm dưới con trỏ chuột `pos`.
        Ưu tiên cửa sổ có diện tích nhỏ nhất (cửa sổ con / dialog nằm trên) trước,
        sau đó mới đến cửa sổ lớn phía sau.
        """
        candidates = [w for w in windows if w["rect"].contains(pos)]
        if not candidates:
            return None

        # Sắp xếp theo diện tích nhỏ dần (nested window / popup / dialog được ưu tiên)
        candidates.sort(key=lambda w: w["rect"].width() * w["rect"].height())
        return candidates[0]
