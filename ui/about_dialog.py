import os
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame
)

from ui.settings_window import MacTitleBar

_APP_ICON_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.ico"))

FEATURES = [
    "High-Definition 1:1 HiDPI Per-Monitor V2 capture",
    "Multi-Monitor virtual desktop support",
    "Full annotation tools: Rectangles, Ellipses, Arrows, Pen, Highlighters, "
    "Mosaic Blur, Step Markers, Text and Word Typography",
    "Always-on-top floating Pin Window",
    "Custom Text and Logo Watermark overlay",
]


def _make_check_icon(size=16) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("#DBEAFE")))
    p.drawEllipse(0, 0, size, size)
    p.setPen(QPen(QColor("#2563EB"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    path = QPainterPath()
    path.moveTo(size * 0.28, size * 0.52)
    path.lineTo(size * 0.44, size * 0.68)
    path.lineTo(size * 0.74, size * 0.32)
    p.drawPath(path)
    p.end()
    return pm


def _make_mail_icon(size=14, color="#2563EB") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    rect_h = size * 0.68
    top = (size - rect_h) / 2
    p.drawRoundedRect(QRectF(1, top, size - 2, rect_h), 2, 2)
    path = QPainterPath()
    path.moveTo(1, top + 1)
    path.lineTo(size / 2, top + rect_h * 0.62)
    path.lineTo(size - 1, top + 1)
    p.drawPath(path)
    p.end()
    return pm


def _make_keyboard_icon(size=14, color="#71717A") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(0.5, size * 0.16, size - 1, size * 0.68), 2, 2)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(color)))
    key_w, key_h = size * 0.12, size * 0.12
    key_y = size * 0.16 + (size * 0.68 - key_h) / 2
    for i, x in enumerate([size * 0.18, size * 0.34, size * 0.5, size * 0.66, size * 0.82]):
        w = key_w * (2.2 if i == 2 else 1)
        p.drawRoundedRect(QRectF(x - w / 2, key_y, w, key_h), 1, 1)
    p.end()
    return pm


class AboutDialog(QDialog):
    """Hộp thoại About ZCapture — macOS Light Style đồng bộ SettingsWindow / OCR Dialog."""
    def __init__(self, hotkey: str = "Ctrl+Shift+S", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(440)

        self.container = QWidget(self)
        self.container.setObjectName("aboutContainer")
        self.container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.container.setStyleSheet("""
            #aboutContainer {
                background-color: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
            }
            QLabel { background-color: transparent; }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(64)
        shadow.setOffset(0, 24)
        shadow.setColor(QColor(0, 0, 0, 61))
        self.container.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.addWidget(self.container)

        box_layout = QVBoxLayout(self.container)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)

        title_bar = MacTitleBar("About ZCapture", self)
        title_bar.title_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #3F3F46;")
        box_layout.addWidget(title_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(0)
        box_layout.addWidget(content)

        # --- Header: Logo + Tên app + Badge version + Subtitle ---
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(56, 56)
        logo_lbl.setPixmap(self._make_logo_pixmap(56))
        header_row.addWidget(logo_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_lbl = QLabel("ZCapture")
        name_lbl.setStyleSheet("font-size: 20px; font-weight: 500; color: #18181B;")
        text_col.addWidget(name_lbl)

        version_lbl = QLabel("v1.0")
        version_lbl.setStyleSheet("""
            background-color: #F4F4F5;
            color: #71717A;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 6px;
        """)
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_col.addWidget(version_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

        subtitle_lbl = QLabel("Screen Capture Tool by ZCS-Labs")
        subtitle_lbl.setStyleSheet("color: #71717A; font-size: 13px; margin-top: 4px;")
        text_col.addWidget(subtitle_lbl)

        header_row.addLayout(text_col)
        header_row.addStretch()
        content_layout.addLayout(header_row)

        content_layout.addSpacing(20)
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.HLine)
        divider1.setFixedHeight(1)
        divider1.setStyleSheet("background-color: rgba(0,0,0,0.06); border: none;")
        content_layout.addWidget(divider1)
        content_layout.addSpacing(18)

        # --- Feature list ---
        for i, feat in enumerate(FEATURES):
            row = QHBoxLayout()
            row.setSpacing(10)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(16, 16)
            icon_lbl.setPixmap(_make_check_icon(16))
            row.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)

            text_lbl = QLabel(feat)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet("color: #3F3F46; font-size: 13px;")
            row.addWidget(text_lbl, 1)

            content_layout.addLayout(row)
            if i < len(FEATURES) - 1:
                content_layout.addSpacing(8)

        content_layout.addSpacing(20)

        # --- Contact & Copyright box ---
        contact_box = QWidget()
        contact_box.setObjectName("contactBox")
        contact_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        contact_box.setStyleSheet("#contactBox { background-color: #FAFAFA; border-radius: 10px; }")

        contact_layout = QVBoxLayout(contact_box)
        contact_layout.setContentsMargins(16, 12, 16, 12)
        contact_layout.setSpacing(6)

        author_lbl = QLabel("AUTHOR AND SUPPORT")
        author_lbl.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 600;")
        contact_layout.addWidget(author_lbl)

        email_row = QHBoxLayout()
        email_row.setSpacing(6)
        mail_icon_lbl = QLabel()
        mail_icon_lbl.setFixedSize(14, 14)
        mail_icon_lbl.setPixmap(_make_mail_icon(14))
        email_row.addWidget(mail_icon_lbl)

        email_lbl = QLabel(
            '<a href="mailto:haidang.infosec@gmail.com" style="color:#2563EB; text-decoration:none;">'
            'haidang.infosec@gmail.com</a>'
        )
        email_lbl.setOpenExternalLinks(True)
        email_lbl.setStyleSheet("font-size: 13px;")
        email_row.addWidget(email_lbl)
        email_row.addStretch()
        contact_layout.addLayout(email_row)

        copyright_lbl = QLabel("Copyright © 2026 ZCS-Labs")
        copyright_lbl.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        contact_layout.addWidget(copyright_lbl)

        content_layout.addWidget(contact_box)
        content_layout.addSpacing(14)

        # --- Active shortcut row ---
        shortcut_row = QHBoxLayout()
        shortcut_row.setSpacing(8)

        kb_icon_lbl = QLabel()
        kb_icon_lbl.setFixedSize(14, 14)
        kb_icon_lbl.setPixmap(_make_keyboard_icon(14))
        shortcut_row.addWidget(kb_icon_lbl)

        shortcut_lbl = QLabel("Active shortcut")
        shortcut_lbl.setStyleSheet("color: #71717A; font-size: 11px;")
        shortcut_row.addWidget(shortcut_lbl)

        shortcut_row.addStretch()

        kbd_tag = QLabel(hotkey)
        kbd_tag.setStyleSheet("""
            background-color: #F4F4F5;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 6px;
            padding: 3px 8px;
            font-family: Consolas, monospace;
            font-size: 12px;
            color: #3F3F46;
        """)
        shortcut_row.addWidget(kbd_tag)
        content_layout.addLayout(shortcut_row)

        # --- OK button ---
        content_layout.addSpacing(24)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        content_layout.addLayout(btn_row)

    @staticmethod
    def _make_logo_pixmap(size: int) -> QPixmap:
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#2563EB")))
        p.drawRoundedRect(0, 0, size, size, 14, 14)

        icon_pm = QIcon(_APP_ICON_PATH).pixmap(QSize(size, size)) if os.path.exists(_APP_ICON_PATH) else QPixmap()
        if not icon_pm.isNull():
            inner = int(size * 0.66)
            scaled = icon_pm.scaled(inner, inner, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            ox = (size - scaled.width()) // 2
            oy = (size - scaled.height()) // 2
            p.drawPixmap(ox, oy, scaled)
        else:
            p.setPen(QPen(QColor("#FFFFFF")))
            font = QFont("Segoe UI", int(size * 0.42), QFont.Weight.Bold)
            p.setFont(font)
            p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "Z")
        p.end()
        return pm
