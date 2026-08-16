from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap


class _OCRWorker(QObject):
    """Chạy OCR trên thread nền để không đơ giao diện overlay khi chờ zcapture_ocr.exe."""
    finished = pyqtSignal(str)

    def __init__(self, pixmap: QPixmap):
        super().__init__()
        self.pixmap = pixmap

    def run(self):
        from core.ocr_engine import extract_text_from_pixmap
        text = extract_text_from_pixmap(self.pixmap)
        self.finished.emit(text or "")
