"""
Package ui.overlay chứa các sub-module chia nhỏ của màn hình chụp Screen Capture Overlay.
"""
from ui.overlay.ocr_worker import _OCRWorker
from ui.overlay.canvas_widget import ScreenOverlayCanvas

__all__ = ["_OCRWorker", "ScreenOverlayCanvas"]
