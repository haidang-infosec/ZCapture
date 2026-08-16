"""
Port Cổng Re-export Tương Thích 100% (Backwards Compatibility Module).
Re-export ScreenOverlayCanvas và _OCRWorker từ package ui.overlay.
"""
from ui.overlay.canvas_widget import ScreenOverlayCanvas
from ui.overlay.ocr_worker import _OCRWorker

__all__ = ["ScreenOverlayCanvas", "_OCRWorker"]
