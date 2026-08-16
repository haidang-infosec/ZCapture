import sys
import ctypes

def enable_hidpi_awareness():
    """
    Kích hoạt Per-Monitor V2 DPI Awareness tối đa trên Windows.
    Đảm bảo DWM (Desktop Window Manager) cung cấp khung hình 1:1 physical pixel grid.
    """
    if sys.platform == "win32":
        try:
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (-4)
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            ctypes.windll.user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
