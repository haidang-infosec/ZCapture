import time
import json
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QColorDialog,
    QFileDialog, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QFrame, QMessageBox, QSlider, QScrollArea, QGraphicsDropShadowEffect
)
from models.watermark import WatermarkSettings
from ui.widgets import StyledCheckBox, ColorPickerRow, RecordingKeySequenceEdit, make_card, make_icon, make_icon_pixmap


def _sidebar_icon(kind: str) -> QIcon:
    """Icon sidebar 18px với 2 trạng thái màu: xám (#71717A) bình thường, xanh (#2563EB) khi được chọn."""
    icon = QIcon()
    icon.addPixmap(make_icon_pixmap(kind, 18, "#71717A"), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(make_icon_pixmap(kind, 18, "#2563EB"), QIcon.Mode.Selected, QIcon.State.Off)
    return icon


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

        # 2. Absolute Centered Title
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


class SettingsWindow(QDialog):
    """
    CleanShot X / Notion Light Mode Settings Dialog for ZCapture.
    Frameless Window with Custom macOS Traffic Light TitleBar & Drop Shadow.
    """
    settings_changed = pyqtSignal()

    def __init__(self, watermark_settings: WatermarkSettings, config_data: dict, parent=None):
        super().__init__(parent)
        self.wm_settings = watermark_settings
        self.config_data = config_data

        # Color state variables with defaults
        self.text_color = QColor(self.config_data.get("default_text_color", "#FFFFFF"))
        self.bg_color = QColor(self.config_data.get("default_bg_color", "#161624"))
        self.stroke_color = QColor(self.config_data.get("default_stroke_color", "#EB3232"))
        # Staged locally (like text/bg/stroke colors above) so Cancel can discard the change
        self.wm_color = QColor(watermark_settings.color)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(860, 660)

        # Outer Container Widget for Drop Shadow & Rounded Corners
        self.container = QWidget(self)
        self.container.setObjectName("settingsContainer")
        self.container.setGeometry(10, 10, 840, 640)

        # Apply CleanShot X Light Mode styling (Notion / Linear Aesthetics)
        self.container.setStyleSheet("""
            #settingsContainer {
                background-color: #FAFAFA;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 14px;
            }
            #titleLabel {
                font-size: 19px;
                font-weight: 700;
                color: #18181B;
                padding-bottom: 2px;
            }
            #subTitleLabel {
                font-size: 13px;
                color: #71717A;
            }
            #sidebarList {
                background-color: #FAFAFA;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                outline: none;
                padding: 6px;
            }
            #sidebarList::item {
                color: #3F3F46;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 3px;
                border-left: 3px solid transparent;
            }
            #sidebarList::item:hover {
                background-color: #F4F4F5;
            }
            #sidebarList::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                font-weight: 500;
                border-left: 3px solid #2563EB;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            #contentCard {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
            }
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background-color: #FFFFFF;
                border: none;
            }
            QLabel {
                color: #3F3F46;
                background-color: transparent;
                font-weight: 500;
                font-size: 13px;
            }
            QLabel#descLabel {
                color: #71717A;
                background-color: transparent;
                font-size: 12px;
                font-weight: normal;
            }
            QLineEdit, QSpinBox, QKeySequenceEdit {
                background-color: #FFFFFF;
                color: #18181B;
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 8px;
                padding: 4px 10px;
                min-height: 32px;
                font-size: 13px;
                font-weight: 500;
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QSpinBox:focus, QKeySequenceEdit:focus {
                border: 1.5px solid #2563EB;
                background-color: #FFFFFF;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #18181B;
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 8px;
                padding: 4px 30px 4px 12px;
                min-height: 32px;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }
            QComboBox:focus {
                border: 1.5px solid #2563EB;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4.5px solid transparent;
                border-right: 4.5px solid transparent;
                border-top: 5.5px solid #64748B;
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #2563EB;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #18181B;
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
                font-weight: 500;
                outline: none;
                selection-background-color: #EFF6FF;
                selection-color: #1D4ED8;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                font-weight: 600;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #E4E4E7;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #3B82F6;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 1.5px solid #3B82F6;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #F4F4F5;
                color: #3F3F46;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                padding: 5px 16px;
                min-height: 32px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E4E4E7;
                border-color: rgba(0, 0, 0, 0.12);
                color: #18181B;
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
            QPushButton#dangerBtn {
                background-color: #FEE2E2;
                border: 1px solid #FCA5A5;
                color: #DC2626;
            }
            QPushButton#dangerBtn:hover {
                background-color: #FCA5A5;
                color: #991B1B;
            }
        """)

        # Drop Shadow Effect (Soft macOS Window Drop Shadow)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        outer_layout = QVBoxLayout(self.container)
        outer_layout.setContentsMargins(0, 0, 0, 16)
        outer_layout.setSpacing(0)

        # 1. Custom macOS Title Bar
        self.title_bar = MacTitleBar("ZCapture Settings", self)
        outer_layout.addWidget(self.title_bar)

        content_wrapper = QWidget()
        main_layout = QVBoxLayout(content_wrapper)
        main_layout.setContentsMargins(18, 14, 18, 0)
        main_layout.setSpacing(12)

        # Header Title
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel("ZCapture Options")
        title_lbl.setObjectName("titleLabel")
        header_box.addWidget(title_lbl)

        sub_title_lbl = QLabel("Customize system shortcuts, capture tools, text & background colors, watermarks, and UI preferences.")
        sub_title_lbl.setObjectName("subTitleLabel")
        header_box.addWidget(sub_title_lbl)

        main_layout.addLayout(header_box)

        # Body Layout: Left Navigation Sidebar + Right Stacked Pages
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # Left Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebarList")
        self.sidebar.setFixedWidth(200)
        self.sidebar.setIconSize(QSize(18, 18))

        nav_items = [
            ("General", "home"),
            ("Capture & Hotkeys", "keyboard"),
            ("Formatting & Tools", "brush"),
            ("Watermark & Branding", "droplet"),
            ("Storage & Output", "folder"),
            ("Appearance & Display", "monitor"),
            ("Advanced", "settings2"),
        ]

        for item_name, icon_kind in nav_items:
            self.sidebar.addItem(QListWidgetItem(_sidebar_icon(icon_kind), item_name))

        self.sidebar.setCurrentRow(0)
        body_layout.addWidget(self.sidebar)

        # Right Stacked Pages Container
        self.pages = QStackedWidget()
        self.pages.setObjectName("contentCard")

        self.pages.addWidget(self.wrap_in_scroll(self.create_general_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_capture_hotkeys_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_formatting_tools_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_watermark_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_storage_output_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_appearance_page()))
        self.pages.addWidget(self.wrap_in_scroll(self.create_advanced_page()))

        body_layout.addWidget(self.pages)
        main_layout.addLayout(body_layout)

        # Connect Sidebar selection to Stacked Pages
        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)
        outer_layout.addWidget(content_wrapper)

    def wrap_in_scroll(self, widget: QWidget) -> QScrollArea:
        """Wrap a page widget in a QScrollArea with CleanShot X Light Mode background (#FFFFFF)."""
        widget.setStyleSheet("background-color: #FFFFFF;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Dialog có bề rộng cố định — không bao giờ cần cuộn ngang, chỉ vài px lệch do
        # margin/border bo tròn có thể kích hoạt thanh cuộn ngang không mong muốn.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if scroll.viewport():
            scroll.viewport().setStyleSheet("background-color: #FFFFFF;")
        scroll.setStyleSheet("""
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background-color: #FFFFFF;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 2px 2px 2px 0px;
            }
            QScrollBar::handle:vertical {
                background: #D4D4D8;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A1A1AA;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 10px;
                margin: 0px 2px 2px 2px;
            }
            QScrollBar::handle:horizontal {
                background: #D4D4D8;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #A1A1AA;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)
        scroll.setWidget(widget)
        return scroll

    # -------------------------------------------------------------------------
    # PAGE 1: General Settings
    # -------------------------------------------------------------------------
    def create_general_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Startup & System Tray
        card1, l1 = make_card("Startup & System Tray Options", "power")

        self.start_with_windows_cb = StyledCheckBox("Start ZCapture automatically when Windows boots")
        self.start_with_windows_cb.setChecked(self.config_data.get("start_with_windows", False))
        l1.addWidget(self.start_with_windows_cb)

        self.minimize_to_tray_cb = StyledCheckBox("Minimize application to System Tray on window close")
        self.minimize_to_tray_cb.setChecked(self.config_data.get("minimize_to_tray", True))
        l1.addWidget(self.minimize_to_tray_cb)

        self.single_click_tray_cb = StyledCheckBox("Single-click tray icon to launch instant screen capture")
        self.single_click_tray_cb.setChecked(self.config_data.get("single_click_tray", True))
        l1.addWidget(self.single_click_tray_cb)

        layout.addWidget(card1)

        # Notifications & Feedback
        card2, l2 = make_card("Notifications & Feedback", "bell")

        self.play_sound_cb = StyledCheckBox("Play sound notification when screenshot is taken")
        self.play_sound_cb.setChecked(self.config_data.get("play_sound", True))
        l2.addWidget(self.play_sound_cb)

        self.show_notifications_cb = StyledCheckBox("Show desktop popup notification after copying or saving")
        self.show_notifications_cb.setChecked(self.config_data.get("show_notifications", True))
        l2.addWidget(self.show_notifications_cb)

        layout.addWidget(card2)

        # About ZCapture — rút gọn, chi tiết đầy đủ đã có ở dialog About riêng
        card3, l3 = make_card("About ZCapture", "info")

        about_row = QHBoxLayout()
        version_lbl = QLabel("ZCapture v1.0 — by ZCS-Labs")
        version_lbl.setObjectName("descLabel")
        about_row.addWidget(version_lbl)
        about_row.addStretch()

        view_info_btn = QPushButton("View full info →")
        view_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_info_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2563EB;
                font-weight: 600;
                font-size: 12px;
                padding: 2px 0px;
                min-height: 0px;
            }
            QPushButton:hover {
                color: #1D4ED8;
            }
        """)
        view_info_btn.clicked.connect(self._open_about_dialog)
        about_row.addWidget(view_info_btn)

        l3.addLayout(about_row)
        layout.addWidget(card3)

        layout.addStretch()
        return widget

    def _open_about_dialog(self):
        from ui.about_dialog import AboutDialog
        hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        dialog = AboutDialog(hotkey=hk, parent=self)
        dialog.exec()

    # -------------------------------------------------------------------------
    # PAGE 2: Capture & Hotkeys
    # -------------------------------------------------------------------------
    def create_capture_hotkeys_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Global Hotkey Recording
        card1, l1 = make_card("Global Screen Capture Shortcut", "keyboard")

        self.hotkey_desc_lbl = QLabel("Click the input field below and press your desired key sequence to record a custom shortcut:")
        self.hotkey_desc_lbl.setObjectName("descLabel")
        self.hotkey_desc_lbl.setWordWrap(True)
        l1.addWidget(self.hotkey_desc_lbl)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Recorded Shortcut:"))

        current_hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        self.hotkey_edit = RecordingKeySequenceEdit(QKeySequence(current_hk))
        self.hotkey_edit.setToolTip("Click here and press key combination (e.g. Ctrl+Shift+S, Alt+A, F4...)")
        self.hotkey_edit.recordingChanged.connect(self._on_hotkey_recording_changed)
        h1.addWidget(self.hotkey_edit)

        # Chấm đỏ nhấp nháy báo hiệu đang ghi phím
        self.record_dot_lbl = QLabel()
        self.record_dot_lbl.setFixedSize(8, 8)
        self.record_dot_lbl.setStyleSheet("background-color: #EF4444; border-radius: 4px;")
        self.record_dot_lbl.hide()
        h1.addWidget(self.record_dot_lbl)
        h1.addStretch()
        l1.addLayout(h1)

        self._record_blink_timer = QTimer(self)
        self._record_blink_timer.setInterval(500)
        self._record_blink_timer.timeout.connect(self._toggle_record_dot)

        # Preset selection combo
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Or Select Preset Shortcut:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Ctrl+Shift+S",
            "Ctrl+Alt+A",
            "Alt+Shift+S",
            "F4",
            "F9",
            "PrintScreen",
            "Ctrl+Alt+S"
        ])
        self.preset_combo.setCurrentText(current_hk)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        h2.addWidget(self.preset_combo)
        l1.addLayout(h2)

        layout.addWidget(card1)

        # Capture Interaction & Magnifier
        card2, l2 = make_card("Capture Preferences & Tools", "sliders")

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Default Selection Mode:"))
        self.capture_mode_combo = QComboBox()
        self.capture_mode_combo.addItems(["Region Selection", "Full Desktop", "Active Window"])
        self.capture_mode_combo.setCurrentText(self.config_data.get("default_capture_mode", "Region Selection"))
        h3.addWidget(self.capture_mode_combo)
        l2.addLayout(h3)

        self.auto_copy_cb = StyledCheckBox("Automatically copy screenshot to Clipboard after selection")
        self.auto_copy_cb.setChecked(self.config_data.get("auto_copy", True))
        l2.addWidget(self.auto_copy_cb)

        self.magnifier_cb = StyledCheckBox("Display pixel magnifier loupe and RGB color code inspector")
        self.magnifier_cb.setChecked(self.config_data.get("show_magnifier", True))
        l2.addWidget(self.magnifier_cb)

        self.freeze_animation_cb = StyledCheckBox("Enable screen dimming and transition effect on capture start")
        self.freeze_animation_cb.setChecked(self.config_data.get("freeze_animation", True))
        l2.addWidget(self.freeze_animation_cb)

        layout.addWidget(card2)
        layout.addStretch()
        return widget

    def on_preset_changed(self, preset_txt):
        self.hotkey_edit.setKeySequence(QKeySequence(preset_txt))

    def _on_hotkey_recording_changed(self, recording: bool):
        """Phản hồi trực quan khi bắt đầu / kết thúc ghi phím tắt."""
        if recording:
            self.hotkey_desc_lbl.setText("Press keys now...")
            self.record_dot_lbl.show()
            self._record_blink_timer.start()
        else:
            self.hotkey_desc_lbl.setText(
                "Click the input field below and press your desired key sequence to record a custom shortcut:"
            )
            self.record_dot_lbl.hide()
            self._record_blink_timer.stop()

    def _toggle_record_dot(self):
        self.record_dot_lbl.setVisible(not self.record_dot_lbl.isVisible())

    # -------------------------------------------------------------------------
    # PAGE 3: Formatting & Tools
    # -------------------------------------------------------------------------
    def create_formatting_tools_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Color Defaults Selection Box
        card0, l0 = make_card("Default Color Palette (Text, Background & Stroke)", "palette")

        self.text_color_picker = ColorPickerRow("Text / Foreground Color", self.text_color)
        self.text_color_picker.colorChanged.connect(lambda c: setattr(self, "text_color", c))
        l0.addWidget(self.text_color_picker)

        self.bg_color_picker = ColorPickerRow("Background / Fill Color", self.bg_color)
        self.bg_color_picker.colorChanged.connect(lambda c: setattr(self, "bg_color", c))
        l0.addWidget(self.bg_color_picker)

        self.stroke_color_picker = ColorPickerRow("Drawing / Line Stroke Color", self.stroke_color)
        self.stroke_color_picker.colorChanged.connect(lambda c: setattr(self, "stroke_color", c))
        l0.addWidget(self.stroke_color_picker)

        layout.addWidget(card0)

        # Default Annotation Defaults
        card1, l1 = make_card("Default Drawing & Annotation Styles", "brush")

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Default Drawing Tool:"))
        self.default_tool_combo = QComboBox()
        self.default_tool_combo.addItems(["Select / Move", "Rectangle", "Circle", "Arrow", "Pencil", "Highlighter", "Text", "Step Counter", "Mosaic", "Blackout"])
        self.default_tool_combo.setCurrentText(self.config_data.get("default_tool", "Select / Move"))
        h1.addWidget(self.default_tool_combo)
        l1.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Stroke Width (Pixels):"))
        self.stroke_spin = QSpinBox()
        self.stroke_spin.setRange(1, 48)
        self.stroke_spin.setValue(self.config_data.get("stroke_width", 3))
        h2.addWidget(self.stroke_spin)
        l1.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Default Typography Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Segoe UI", "Arial", "Calibri", "Times New Roman",
            "Consolas", "JetBrains Mono", "Tahoma", "Verdana", "Inter"
        ])
        self.font_combo.setCurrentText(self.config_data.get("default_font", "Segoe UI"))
        h3.addWidget(self.font_combo)
        l1.addLayout(h3)

        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Default Font Size (pt):"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.config_data.get("default_font_size", 14))
        h4.addWidget(self.font_size_spin)
        l1.addLayout(h4)

        h5 = QHBoxLayout()
        h5.addWidget(QLabel("Text Background Style:"))
        self.text_bg_combo = QComboBox()
        self.text_bg_combo.addItems(["Dark Badge", "Transparent (No Background)", "Solid Color Fill"])
        bg_mode_map = {"badge": 0, "none": 1, "color": 2}
        self.text_bg_combo.setCurrentIndex(bg_mode_map.get(self.config_data.get("default_text_bg", "badge"), 0))
        h5.addWidget(self.text_bg_combo)
        l1.addLayout(h5)

        layout.addWidget(card1)

        # Step Marker Options
        card2, l2 = make_card("Step Marker Configuration", "badge-number")

        h6 = QHBoxLayout()
        h6.addWidget(QLabel("Starting Number:"))
        self.step_start_spin = QSpinBox()
        self.step_start_spin.setRange(1, 99)
        self.step_start_spin.setValue(self.config_data.get("step_start_num", 1))
        h6.addWidget(self.step_start_spin)

        h6.addWidget(QLabel("Prefix String:"))
        self.step_prefix_input = QLineEdit(self.config_data.get("step_prefix", ""))
        self.step_prefix_input.setPlaceholderText("Optional e.g. Step- or #")
        h6.addWidget(self.step_prefix_input)
        l2.addLayout(h6)

        layout.addWidget(card2)
        layout.addStretch()
        return widget

    # -------------------------------------------------------------------------
    # PAGE 4: Watermark & Branding
    # -------------------------------------------------------------------------
    def create_watermark_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.wm_enable_cb = StyledCheckBox("Enable Watermark Overlay on Captured Screenshots")
        self.wm_enable_cb.setChecked(self.wm_settings.enabled)
        layout.addWidget(self.wm_enable_cb)

        # Text Watermark Box
        card1, l1 = make_card("Text Watermark Settings", "droplet")

        l1.addWidget(QLabel("Watermark Text Content:"))
        self.wm_text_input = QLineEdit(self.wm_settings.text)
        l1.addWidget(self.wm_text_input)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Font Family:"))
        self.wm_font_combo = QComboBox()
        self.wm_font_combo.addItems(["Segoe UI", "Arial", "Calibri", "Times New Roman", "Consolas", "JetBrains Mono", "Inter"])
        self.wm_font_combo.setCurrentText(self.wm_settings.font_family)
        h1.addWidget(self.wm_font_combo)

        h1.addWidget(QLabel("Font Size:"))
        self.wm_size_spin = QSpinBox()
        self.wm_size_spin.setRange(10, 72)
        self.wm_size_spin.setValue(self.wm_settings.font_size)
        h1.addWidget(self.wm_size_spin)
        l1.addLayout(h1)

        self.wm_color_picker = ColorPickerRow("Watermark color", self.wm_color)
        self.wm_color_picker.colorChanged.connect(lambda c: setattr(self, "wm_color", c))
        l1.addWidget(self.wm_color_picker)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Placement Position:"))
        self.wm_pos_combo = QComboBox()
        self.wm_pos_combo.addItems(["Bottom-Right", "Bottom-Left", "Top-Right", "Top-Left", "Center"])
        self.wm_pos_combo.setCurrentText(self.wm_settings.position)
        h2.addWidget(self.wm_pos_combo)
        l1.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Opacity Level:"))
        self.wm_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.wm_opacity_slider.setRange(10, 100)
        self.wm_opacity_slider.setValue(int(round(self.wm_settings.opacity * 100)))
        h3.addWidget(self.wm_opacity_slider)

        self.wm_opacity_value_lbl = QLabel(f"{self.wm_opacity_slider.value()}%")
        self.wm_opacity_value_lbl.setStyleSheet("color: #71717A; font-size: 12px; min-width: 34px;")
        self.wm_opacity_slider.valueChanged.connect(lambda v: self.wm_opacity_value_lbl.setText(f"{v}%"))
        h3.addWidget(self.wm_opacity_value_lbl)
        l1.addLayout(h3)

        layout.addWidget(card1)

        # Logo Watermark Box
        card2, l2 = make_card("Logo Image Watermark", "image")
        h_logo = QHBoxLayout()
        self.wm_logo_input = QLineEdit(self.wm_settings.logo_path)
        self.wm_logo_input.setPlaceholderText("Path to image file (.png, .jpg, .svg)")
        h_logo.addWidget(self.wm_logo_input)
        logo_btn = QPushButton("Browse Image...")
        logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_btn.clicked.connect(self.browse_wm_logo)
        h_logo.addWidget(logo_btn)
        l2.addLayout(h_logo)
        layout.addWidget(card2)

        # Timestamp Badge Box
        card3, l3 = make_card("Timestamp Overlay", "clock")
        self.auto_ts_cb = StyledCheckBox("Automatically insert date & time stamp badge (YYYY-MM-DD HH:MM:SS)")
        self.auto_ts_cb.setChecked(self.config_data.get("auto_timestamp", False))
        l3.addWidget(self.auto_ts_cb)
        layout.addWidget(card3)

        layout.addStretch()
        return widget

    # -------------------------------------------------------------------------
    # PAGE 5: Storage & Output
    # -------------------------------------------------------------------------
    def create_storage_output_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Default Directory
        card1, l1 = make_card("Default Save Directory", "folder")

        l1.addWidget(QLabel("Target Output Directory Path:"))
        h1 = QHBoxLayout()
        self.save_dir_input = QLineEdit(self.config_data.get("save_dir", ""))
        self.save_dir_input.setPlaceholderText("Default: Windows Pictures Folder")
        h1.addWidget(self.save_dir_input)

        browse_btn = QPushButton("Browse Folder...")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_save_dir)
        h1.addWidget(browse_btn)
        l1.addLayout(h1)

        self.auto_save_copy_cb = StyledCheckBox("Automatically save a copy to file when copying to Clipboard")
        self.auto_save_copy_cb.setChecked(self.config_data.get("auto_save_on_copy", False))
        l1.addWidget(self.auto_save_copy_cb)

        layout.addWidget(card1)

        # File Naming (tách riêng card + có live preview)
        card2, l2 = make_card("Filename Template", "tag")

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Filename Template:"))
        self.filename_pattern_combo = QComboBox()
        self.filename_pattern_combo.addItems([
            "ZCapture_{date}_{time}",
            "Screenshot_{timestamp}",
            "Capture_{date}",
            "Image_{index}"
        ])
        self.filename_pattern_combo.setCurrentText(self.config_data.get("filename_pattern", "ZCapture_{date}_{time}"))
        h2.addWidget(self.filename_pattern_combo)
        l2.addLayout(h2)

        self.filename_preview_lbl = QLabel()
        self.filename_preview_lbl.setStyleSheet("color: #71717A; font-size: 12px; font-family: Consolas, monospace;")
        l2.addWidget(self.filename_preview_lbl)

        layout.addWidget(card2)

        # Image Format & Quality (card riêng)
        card3, l3 = make_card("Image Format & Quality", "image")

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Default Image Format:"))
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG (*.png)", "JPEG (*.jpg)", "BMP (*.bmp)", "WEBP (*.webp)"])
        self.image_format_combo.setCurrentText(self.config_data.get("image_format", "PNG (*.png)"))
        h3.addWidget(self.image_format_combo)

        h3.addWidget(QLabel("JPEG Quality (%):"))
        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setRange(50, 100)
        self.image_quality_spin.setValue(self.config_data.get("image_quality", 95))
        h3.addWidget(self.image_quality_spin)
        l3.addLayout(h3)

        layout.addWidget(card3)

        self.filename_pattern_combo.currentTextChanged.connect(self._update_filename_preview)
        self.image_format_combo.currentTextChanged.connect(lambda _: self._update_filename_preview())
        self._update_filename_preview()

        layout.addStretch()
        return widget

    def _update_filename_preview(self, _pattern_text=None):
        pattern_text = self.filename_pattern_combo.currentText()
        now = time.localtime()
        preview = (
            pattern_text
            .replace("{date}", time.strftime("%Y-%m-%d", now))
            .replace("{time}", time.strftime("%H%M%S", now))
            .replace("{timestamp}", time.strftime("%Y%m%d_%H%M%S", now))
            .replace("{index}", "001")
        )
        ext = ".png"
        cur_format = self.image_format_combo.currentText().lower()
        if "jpg" in cur_format or "jpeg" in cur_format:
            ext = ".jpg"
        elif "bmp" in cur_format:
            ext = ".bmp"
        elif "webp" in cur_format:
            ext = ".webp"
        self.filename_preview_lbl.setText(f"Xem trước: {preview}{ext}")

    # -------------------------------------------------------------------------
    # PAGE 6: Appearance & Display
    # -------------------------------------------------------------------------
    def create_appearance_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Theme Options
        card1, l1 = make_card("Visual Theme & Style", "palette")

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Application Interface Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light (Default)", "Dark", "System (Theo hệ điều hành)"])
        self.theme_combo.setCurrentText(self.config_data.get("ui_theme", "Light (Default)"))
        h1.addWidget(self.theme_combo)
        l1.addLayout(h1)

        layout.addWidget(card1)

        # Canvas Overlay & Mouse Cursor
        card2, l2 = make_card("Canvas Overlay & Mouse Cursor", "cursor")

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Screen Overlay Darkness Level:"))
        self.dim_slider = QSlider(Qt.Orientation.Horizontal)
        self.dim_slider.setRange(20, 80)
        self.dim_slider.setValue(self.config_data.get("dim_opacity", 50))
        h2.addWidget(self.dim_slider)
        l2.addLayout(h2)

        self.include_cursor_cb = StyledCheckBox("Include mouse cursor pointer in captured screenshots")
        self.include_cursor_cb.setChecked(self.config_data.get("include_cursor", False))
        l2.addWidget(self.include_cursor_cb)

        layout.addWidget(card2)

        # DPI Awareness
        card3, l3 = make_card("High-DPI Scaling Awareness", "monitor")

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Display DPI Mode:"))
        self.dpi_mode_combo = QComboBox()
        self.dpi_mode_combo.addItems([
            "Per-Monitor DPI V2 (Recommended)",
            "System DPI Aware",
            "Unscaled Native Pixel Mode"
        ])
        self.dpi_mode_combo.setCurrentText(self.config_data.get("dpi_mode", "Per-Monitor DPI V2 (Recommended)"))
        h3.addWidget(self.dpi_mode_combo)
        l3.addLayout(h3)

        layout.addWidget(card3)
        layout.addStretch()
        return widget

    # -------------------------------------------------------------------------
    # PAGE 7: Advanced & Backup
    # -------------------------------------------------------------------------
    def create_advanced_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Backup & Portability
        card1, l1 = make_card("Configuration Backup & Portability", "settings2")

        lbl_desc = QLabel("Export or import your ZCapture system configuration and watermark profiles as a JSON file.")
        lbl_desc.setObjectName("descLabel")
        lbl_desc.setWordWrap(True)
        l1.addWidget(lbl_desc)

        h1 = QHBoxLayout()
        export_btn = QPushButton("Export Configuration to JSON...")
        export_btn.setIcon(make_icon("upload", 16, "#3F3F46"))
        export_btn.setIconSize(QSize(16, 16))
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_config)
        h1.addWidget(export_btn)

        import_btn = QPushButton("Import Configuration from JSON...")
        import_btn.setIcon(make_icon("download", 16, "#3F3F46"))
        import_btn.setIconSize(QSize(16, 16))
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_config)
        h1.addWidget(import_btn)
        l1.addLayout(h1)

        layout.addWidget(card1)

        # Reset Defaults
        card2, l2 = make_card("Reset Application State", "refresh")

        lbl_reset = QLabel("Restore all shortcuts, watermark configurations, and tool preferences to factory default settings.")
        lbl_reset.setObjectName("descLabel")
        lbl_reset.setWordWrap(True)
        l2.addWidget(lbl_reset)

        reset_btn = QPushButton("Reset All Settings to Defaults")
        reset_btn.setObjectName("dangerBtn")
        reset_btn.setIcon(make_icon("refresh", 16, "#DC2626"))
        reset_btn.setIconSize(QSize(16, 16))
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_to_defaults)
        l2.addWidget(reset_btn)

        layout.addWidget(card2)

        layout.addStretch()
        return widget

    # -------------------------------------------------------------------------
    # Dialog Helper Methods & Handlers
    # -------------------------------------------------------------------------
    def browse_save_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Default Output Directory")
        if directory:
            self.save_dir_input.setText(directory)

    def browse_wm_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image File", "", "Images (*.png *.jpg *.jpeg *.svg)"
        )
        if file_path:
            self.wm_logo_input.setText(file_path)

    def export_config(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "ZCapture_Config.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        export_payload = {
            "config": self.config_data,
            "watermark": {
                "enabled": self.wm_settings.enabled,
                "text": self.wm_settings.text,
                "font_family": self.wm_settings.font_family,
                "font_size": self.wm_settings.font_size,
                "color_rgba": [self.wm_settings.color.red(), self.wm_settings.color.green(), self.wm_settings.color.blue(), self.wm_settings.color.alpha()],
                "position": self.wm_settings.position,
                "opacity": self.wm_settings.opacity,
                "logo_path": self.wm_logo_input.text()
            }
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Export Successful", f"Configuration exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export configuration:\n{str(e)}")

    def _refresh_ui_from_config(self):
        """Đồng bộ hóa toàn bộ controls trên cả 7 tab từ config_data và wm_settings hiện tại."""
        # Page 1: General
        self.start_with_windows_cb.setChecked(self.config_data.get("start_with_windows", False))
        self.minimize_to_tray_cb.setChecked(self.config_data.get("minimize_to_tray", True))
        self.single_click_tray_cb.setChecked(self.config_data.get("single_click_tray", True))
        self.play_sound_cb.setChecked(self.config_data.get("play_sound", True))
        self.show_notifications_cb.setChecked(self.config_data.get("show_notifications", True))

        # Page 2: Capture & Hotkeys
        current_hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        self.hotkey_edit.setKeySequence(QKeySequence(current_hk))
        self.preset_combo.setCurrentText(current_hk)
        self.capture_mode_combo.setCurrentText(self.config_data.get("default_capture_mode", "Region Selection"))
        self.auto_copy_cb.setChecked(self.config_data.get("auto_copy", True))
        self.magnifier_cb.setChecked(self.config_data.get("show_magnifier", True))
        self.freeze_animation_cb.setChecked(self.config_data.get("freeze_animation", True))

        # Page 3: Formatting & Tools
        self.text_color = QColor(self.config_data.get("default_text_color", "#FFFFFF"))
        self.bg_color = QColor(self.config_data.get("default_bg_color", "#161624"))
        self.stroke_color = QColor(self.config_data.get("default_stroke_color", "#EB3232"))
        self.text_color_picker.set_color(self.text_color)
        self.bg_color_picker.set_color(self.bg_color)
        self.stroke_color_picker.set_color(self.stroke_color)

        self.default_tool_combo.setCurrentText(self.config_data.get("default_tool", "Select / Move"))
        self.stroke_spin.setValue(self.config_data.get("stroke_width", 3))
        self.font_combo.setCurrentText(self.config_data.get("default_font", "Segoe UI"))
        self.font_size_spin.setValue(self.config_data.get("default_font_size", 14))

        bg_mode_map = {"badge": 0, "none": 1, "color": 2}
        self.text_bg_combo.setCurrentIndex(bg_mode_map.get(self.config_data.get("default_text_bg", "badge"), 0))
        self.step_start_spin.setValue(self.config_data.get("step_start_num", 1))
        self.step_prefix_input.setText(self.config_data.get("step_prefix", ""))

        # Page 4: Watermark & Branding
        self.wm_enable_cb.setChecked(self.wm_settings.enabled)
        self.wm_text_input.setText(self.wm_settings.text)
        self.wm_font_combo.setCurrentText(self.wm_settings.font_family)
        self.wm_size_spin.setValue(self.wm_settings.font_size)
        self.wm_color = QColor(self.wm_settings.color)
        self.wm_color_picker.set_color(self.wm_color)
        self.wm_pos_combo.setCurrentText(self.wm_settings.position)
        self.wm_opacity_slider.setValue(int(round(self.wm_settings.opacity * 100)))
        self.wm_logo_input.setText(self.wm_settings.logo_path)
        self.auto_ts_cb.setChecked(self.config_data.get("auto_timestamp", False))

        # Page 5: Storage & Output
        self.save_dir_input.setText(self.config_data.get("save_dir", ""))
        self.auto_save_copy_cb.setChecked(self.config_data.get("auto_save_on_copy", False))
        self.filename_pattern_combo.setCurrentText(self.config_data.get("filename_pattern", "ZCapture_{date}_{time}"))
        self.image_format_combo.setCurrentText(self.config_data.get("image_format", "PNG (*.png)"))
        self.image_quality_spin.setValue(self.config_data.get("image_quality", 95))
        self._update_filename_preview()

        # Page 6: Appearance & Display
        self.theme_combo.setCurrentText(self.config_data.get("ui_theme", "Light (Default)"))
        self.dim_slider.setValue(self.config_data.get("dim_opacity", 50))
        self.include_cursor_cb.setChecked(self.config_data.get("include_cursor", False))
        self.dpi_mode_combo.setCurrentText(self.config_data.get("dpi_mode", "Per-Monitor DPI V2 (Recommended)"))

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "config" in data and isinstance(data["config"], dict):
                self.config_data.update(data["config"])

            if "watermark" in data and isinstance(data["watermark"], dict):
                wm = data["watermark"]
                self.wm_settings.enabled = wm.get("enabled", self.wm_settings.enabled)
                self.wm_settings.text = wm.get("text", self.wm_settings.text)
                self.wm_settings.font_family = wm.get("font_family", self.wm_settings.font_family)
                self.wm_settings.font_size = wm.get("font_size", self.wm_settings.font_size)
                if "color_rgba" in wm:
                    r, g, b, a = wm["color_rgba"]
                    self.wm_settings.color = QColor(r, g, b, a)
                self.wm_settings.position = wm.get("position", self.wm_settings.position)
                self.wm_settings.opacity = wm.get("opacity", self.wm_settings.opacity)
                self.wm_settings.logo_path = wm.get("logo_path", self.wm_settings.logo_path)

            self._refresh_ui_from_config()
            QMessageBox.information(self, "Import Successful", "Configuration loaded successfully! Click Save Changes to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to load configuration file:\n{str(e)}")

    def reset_to_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Confirmation",
            "Are you sure you want to reset all options and shortcuts to factory defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            defaults = {
                "hotkey": "Ctrl+Shift+S",
                "auto_copy": True,
                "show_magnifier": True,
                "save_dir": "",
                "stroke_width": 3,
                "default_font": "Segoe UI",
                "start_with_windows": False,
                "minimize_to_tray": True,
                "single_click_tray": True,
                "play_sound": True,
                "show_notifications": True,
                "default_capture_mode": "Region Selection",
                "freeze_animation": True,
                "default_tool": "Select / Move",
                "default_font_size": 14,
                "default_text_bg": "badge",
                "step_start_num": 1,
                "step_prefix": "",
                "auto_timestamp": False,
                "auto_save_on_copy": False,
                "filename_pattern": "ZCapture_{date}_{time}",
                "image_format": "PNG (*.png)",
                "image_quality": 95,
                "ui_theme": "Light (Default)",
                "dim_opacity": 50,
                "include_cursor": False,
                "dpi_mode": "Per-Monitor DPI V2 (Recommended)",
                "default_text_color": "#FFFFFF",
                "default_bg_color": "#161624",
                "default_stroke_color": "#EB3232"
            }
            self.config_data.update(defaults)

            self.wm_settings.enabled = False
            self.wm_settings.text = "ZCS-Labs"
            self.wm_settings.font_family = "Segoe UI"
            self.wm_settings.font_size = 18
            self.wm_settings.color = QColor(255, 255, 255, 180)
            self.wm_settings.position = "Bottom-Right"
            self.wm_settings.opacity = 0.7
            self.wm_settings.logo_path = ""

            self._refresh_ui_from_config()
            QMessageBox.information(self, "Reset Complete", "All options have been restored to default values.")

    def save_settings(self):
        """Save all page settings back to config_data and watermark_settings."""
        # Page 1: General
        self.config_data["start_with_windows"] = self.start_with_windows_cb.isChecked()
        self.config_data["minimize_to_tray"] = self.minimize_to_tray_cb.isChecked()
        self.config_data["single_click_tray"] = self.single_click_tray_cb.isChecked()
        self.config_data["play_sound"] = self.play_sound_cb.isChecked()
        self.config_data["show_notifications"] = self.show_notifications_cb.isChecked()

        # Page 2: Capture & Hotkeys
        recorded_hk = self.hotkey_edit.keySequence().toString()
        if recorded_hk:
            self.config_data["hotkey"] = recorded_hk
        else:
            self.config_data["hotkey"] = self.preset_combo.currentText()

        self.config_data["default_capture_mode"] = self.capture_mode_combo.currentText()
        self.config_data["auto_copy"] = self.auto_copy_cb.isChecked()
        self.config_data["show_magnifier"] = self.magnifier_cb.isChecked()
        self.config_data["freeze_animation"] = self.freeze_animation_cb.isChecked()

        # Page 3: Formatting & Tools (With Colors!)
        self.config_data["default_text_color"] = self.text_color.name()
        self.config_data["default_bg_color"] = self.bg_color.name()
        self.config_data["default_stroke_color"] = self.stroke_color.name()

        self.config_data["default_tool"] = self.default_tool_combo.currentText()
        self.config_data["stroke_width"] = self.stroke_spin.value()
        self.config_data["default_font"] = self.font_combo.currentText()
        self.config_data["default_font_size"] = self.font_size_spin.value()

        text_bg_modes = ["badge", "none", "color"]
        self.config_data["default_text_bg"] = text_bg_modes[self.text_bg_combo.currentIndex()]
        self.config_data["step_start_num"] = self.step_start_spin.value()
        self.config_data["step_prefix"] = self.step_prefix_input.text().strip()

        # Page 4: Watermark & Branding
        self.wm_settings.enabled = self.wm_enable_cb.isChecked()
        self.wm_settings.text = self.wm_text_input.text().strip()
        self.wm_settings.font_family = self.wm_font_combo.currentText()
        self.wm_settings.font_size = self.wm_size_spin.value()
        self.wm_settings.color = self.wm_color
        self.wm_settings.position = self.wm_pos_combo.currentText()
        self.wm_settings.opacity = self.wm_opacity_slider.value() / 100.0
        self.wm_settings.logo_path = self.wm_logo_input.text().strip()
        self.config_data["auto_timestamp"] = self.auto_ts_cb.isChecked()

        # Page 5: Storage & Output
        self.config_data["save_dir"] = self.save_dir_input.text().strip()
        self.config_data["auto_save_on_copy"] = self.auto_save_copy_cb.isChecked()
        self.config_data["filename_pattern"] = self.filename_pattern_combo.currentText()
        self.config_data["image_format"] = self.image_format_combo.currentText()
        self.config_data["image_quality"] = self.image_quality_spin.value()

        # Page 6: Appearance & Display
        self.config_data["ui_theme"] = self.theme_combo.currentText()
        self.config_data["dim_opacity"] = self.dim_slider.value()
        self.config_data["include_cursor"] = self.include_cursor_cb.isChecked()
        self.config_data["dpi_mode"] = self.dpi_mode_combo.currentText()

        # Tự động ghi trực tiếp cấu hình xuống %APPDATA%/ZCapture/config.json
        from core.config_store import save_config
        save_config(self.config_data, self.wm_settings)

        self.settings_changed.emit()
        self.accept()
