import re, time
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QGuiApplication, QFont, QColor
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox, QGraphicsDropShadowEffect
)

def clean_ocr_text(text: str) -> str:
    """Hậu xử lý làm sạch văn bản OCR (Sửa các lỗi phổ biến như Circ1e -> Circle)."""
    if not text:
        return ""
    # Fix '1' inside words like Circ1e -> Circle
    cleaned = re.sub(r'([a-zA-Z])1([a-zA-Z])', r'\1l\2', text)
    # Fix '0' inside words like R0bot -> Robot
    cleaned = re.sub(r'([a-zA-Z])0([a-zA-Z])', r'\1o\2', cleaned)
    return cleaned


class MacTitleBar(QWidget):
    """Thanh tiêu đề tùy chỉnh chuẩn macOS (Custom Title Bar với 3 nút Traffic Light Red/Yellow/Green)."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(44)
        self.drag_position = None

        self.setStyleSheet("""
            MacTitleBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid rgba(0, 0, 0, 0.06);
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        # 1. Traffic Light Buttons Layout (3 nút tròn Red/Yellow/Green góc trái)
        traffic_box = QHBoxLayout()
        traffic_box.setSpacing(8)

        # Red Close Button (#FF5F57)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(12, 12)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5F57;
                border: none;
                border-radius: 6px;
                color: transparent;
                font-size: 8px;
                font-weight: bold;
                padding: 0px;
                min-height: 12px;
            }
            QPushButton:hover {
                color: #800000;
                background-color: #FF5F57;
            }
        """)
        if parent:
            self.close_btn.clicked.connect(parent.close)
        traffic_box.addWidget(self.close_btn)

        # Yellow Minimize Button (#FEBC2E)
        self.min_btn = QPushButton("−")
        self.min_btn.setFixedSize(12, 12)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEBC2E;
                border: none;
                border-radius: 6px;
                color: transparent;
                font-size: 9px;
                font-weight: bold;
                padding: 0px;
                min-height: 12px;
            }
            QPushButton:hover {
                color: #995c00;
                background-color: #FEBC2E;
            }
        """)
        if parent:
            self.min_btn.clicked.connect(parent.showMinimized)
        traffic_box.addWidget(self.min_btn)

        # Green Maximize Button (#28C840)
        self.max_btn = QPushButton("")
        self.max_btn.setFixedSize(12, 12)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background-color: #28C840;
                border: none;
                border-radius: 6px;
                padding: 0px;
                min-height: 12px;
            }
        """)
        traffic_box.addWidget(self.max_btn)

        layout.addLayout(traffic_box)

        layout.addStretch()

        # 2. Absolute Centered Title (Không icon window, font-weight: 600, color: #3F3F46)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #3F3F46;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Spacer matching traffic_box width to keep title perfectly centered
        spacer = QWidget()
        spacer.setFixedWidth(52)
        layout.addWidget(spacer)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_window:
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position and self.parent_window:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class OCRResultDialog(QDialog):
    """
    Sleek Enterprise macOS Light Mode OCR Result Window for ZCapture.
    Frameless Window with Custom Traffic Light TitleBar & Drop Shadow.
    """
    def __init__(self, extracted_text: str, parent=None):
        super().__init__(parent)
        self.extracted_text = clean_ocr_text(extracted_text)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(520, 440)

        # Main Outer Container Widget for Drop Shadow & Rounded Corners
        self.container = QWidget(self)
        self.container.setObjectName("dialogContainer")
        self.container.setGeometry(10, 10, 500, 420)
        self.container.setStyleSheet("""
            #dialogContainer {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 14px;
            }
            QLabel#titleHeaderLabel {
                font-size: 16px;
                font-weight: 700;
                color: #2563EB;
            }
            QLabel#countLabel {
                font-size: 12px;
                font-weight: 600;
                color: #71717A;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #18181B;
                border: 1px solid rgba(0, 0, 0, 0.10);
                border-radius: 12px;
                padding: 14px;
                font-family: -apple-system, BlinkMacSystemFont, "SF Mono", "Consolas", monospace;
                font-size: 13px;
                line-height: 1.6;
                selection-background-color: #DBEAFE;
                selection-color: #1D4ED8;
            }
            QTextEdit:focus {
                border: 1px solid #2563EB;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #3F3F46;
                border: 1px solid rgba(0, 0, 0, 0.10);
                border-radius: 10px;
                padding: 6px 16px;
                min-height: 32px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F4F4F5;
                color: #18181B;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QPushButton#primaryBtn {
                background-color: #2563EB;
                border: 1px solid #1D4ED8;
                color: #FFFFFF;
                border-radius: 10px;
                font-weight: 700;
            }
            QPushButton#primaryBtn:hover {
                background-color: #1D4ED8;
            }
        """)

        # Drop Shadow Effect (Soft macOS Window Drop Shadow)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 16)
        main_layout.setSpacing(0)

        # 1. Custom macOS Title Bar
        self.title_bar = MacTitleBar("OCR Text Extraction", self)
        main_layout.addWidget(self.title_bar)

        # Content Layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 16, 24, 0)
        content_layout.setSpacing(14)

        # Header Title & Word Count
        h_box = QHBoxLayout()
        title_lbl = QLabel("Extracted Text (OCR)")
        title_lbl.setObjectName("titleHeaderLabel")
        h_box.addWidget(title_lbl)

        h_box.addStretch()

        words = len(self.extracted_text.split())
        chars = len(self.extracted_text)
        self.count_lbl = QLabel(f"{words} words | {chars} characters")
        self.count_lbl.setObjectName("countLabel")
        h_box.addWidget(self.count_lbl)
        content_layout.addLayout(h_box)

        # Text Edit Container
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.extracted_text)
        self.text_edit.textChanged.connect(self.update_count)
        content_layout.addWidget(self.text_edit)

        # Action Buttons Layout (Space-Between Layout)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # Left Buttons: Copy + Save as File...
        copy_btn = QPushButton(" Copy to Clipboard")
        copy_btn.setObjectName("primaryBtn")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save as File...")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_to_file)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()

        # Right Button: Close
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        content_layout.addLayout(btn_layout)
        main_layout.addLayout(content_layout)

    def update_count(self):
        txt = self.text_edit.toPlainText()
        words = len(txt.split())
        chars = len(txt)
        self.count_lbl.setText(f"{words} words | {chars} characters")

    def copy_to_clipboard(self):
        txt = self.text_edit.toPlainText()
        QGuiApplication.clipboard().setText(txt)
        QMessageBox.information(self, "Copied", "Extracted text copied to Clipboard!")

    def save_to_file(self):
        default_name = f"ZCapture_OCR_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save OCR Text", default_name, "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "Saved", f"Text saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save text file:\n{str(e)}")
