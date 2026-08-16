import math, time, os
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF, QSize, QTimer, QThread
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage, QPolygonF,
    QKeySequence, QShortcut, QFontMetrics, QIcon, QGuiApplication, QCursor, QPainterPath, QAction
)
from PyQt6.QtWidgets import (
    QWidget, QMenu, QFileDialog, QHBoxLayout, QVBoxLayout,
    QPushButton, QComboBox, QSpinBox, QColorDialog, QToolButton, QLabel, QLineEdit, QTextEdit,
    QGraphicsDropShadowEffect, QToolTip, QMessageBox, QWidgetAction, QFrame
)

from models.watermark import apply_watermark, apply_timestamp, WatermarkSettings
from models.annotations import (
    calc_position_from_setting, AnnotationItem, ShapeItem, ArrowItem, HighlightItem, PathItem,
    StepItem, TextItem, TimestampItem, WatermarkItem, WatermarkLogoItem, MosaicItem, BlackoutItem
)
from ui.toolbars import (
    DraggableToolbarPanel, DragGripWidget, create_rect_icon, create_pencil_icon, create_pointer_icon,
    create_mosaic_icon, create_blackout_icon, create_watermark_icon, common_toolbar_style, word_toolbar_style
)
from ui.pin_window import PinnedWindow
from ui.overlay.ocr_worker import _OCRWorker
from ui.overlay.rendering_helper import (
    draw_dimension_badge, draw_magnifier_loupe, draw_annotation_item
)
from ui.overlay.sub_toolbars import (
    make_divider, make_checkerboard_icon, make_simple_icon, draw_sun, draw_card
)


class ScreenOverlayCanvas(QWidget):
    """
    Cửa sổ phủ toàn màn hình (Overlay Canvas) chụp & chỉnh sửa ảnh.
    Thanh Ribbon Định Dạng Font Chữ Màu Trắng Nền Đen Nổi Bật 100%.
    """
    def __init__(self, full_pixmap: QPixmap, virtual_rect: QRect, watermark_settings: WatermarkSettings = None, config_data: dict = None, on_settings_changed=None):
        super().__init__()
        self.full_pixmap = full_pixmap
        self.virtual_rect = virtual_rect
        self.watermark_settings = watermark_settings or WatermarkSettings()
        self.config_data = config_data or {}
        self.on_settings_changed = on_settings_changed

        self.cached_image = self.full_pixmap.toImage()

        self.selection_rect = QRect()
        self.is_selecting = False
        self.is_resizing_selection = False
        self.is_moving_selection = False
        self.active_selection_handle = None
        self.drag_start = QPoint()
        self.initial_move_rect = QRect()

        self.annotations = []
        self.redo_stack = []
        self.current_drawing_item = None
        self.selected_annotation = None
        self.is_dragging_annotation = False
        self.is_resizing_annotation = False
        self.active_handle = None

        self.initial_font_size = 18
        self.initial_annotation_rect = QRect()

        self.is_bold = True
        self.is_italic = False
        self.is_underline = False

        default_tool_map = {
            "Select / Move": "select",
            "Rectangle": "rect",
            "Circle": "circle",
            "Arrow": "arrow",
            "Pencil": "pencil",
            "Highlighter": "highlighter",
            "Step Counter": "step",
            "Text": "text",
            "Mosaic": "mosaic",
            "Blackout": "blackout"
        }
        init_tool_setting = self.config_data.get("default_tool", "Select / Move")
        self.current_tool = default_tool_map.get(init_tool_setting, "select")

        self.current_color = QColor(self.config_data.get("default_stroke_color", "#EB3232"))
        self.current_bg_color = QColor(self.config_data.get("default_bg_color", "#161624"))
        self.current_stroke_width = max(1, self.config_data.get("stroke_width", 3))
        self.current_font_family = self.config_data.get("default_font", "Segoe UI")
        self.current_font_size = self.config_data.get("default_font_size", 14)
        self.current_text_bg_mode = self.config_data.get("default_text_bg", "none")
        self.step_counter = max(1, self.config_data.get("step_start_num", 1))

        self.inline_text_edit = None

        self.v_toolbar = None
        self.h_toolbar = None
        self.sub_toolbar = None

        self.dash_offset = 0.0
        self.ants_timer = QTimer(self)
        self.ants_timer.setInterval(40)
        self.ants_timer.timeout.connect(self.update_marching_ants)
        self.ants_timer.start()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setGeometry(self.virtual_rect)

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.delete_selected_annotation)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self, self.delete_selected_annotation)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.redo)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_and_close)
        QShortcut(QKeySequence("Return"), self, self.copy_and_close)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_to_file)

        self.init_toolbars()

    def init_toolbars(self):
        self.v_toolbar = DraggableToolbarPanel(self)
        self.v_toolbar.setObjectName("toolbarPanel")
        self.v_toolbar.setStyleSheet(common_toolbar_style)

        v_layout = QVBoxLayout(self.v_toolbar)
        v_layout.setContentsMargins(6, 6, 6, 8)
        v_layout.setSpacing(6)

        # Drag grip handle at top of vertical toolbar
        self.v_grip = DragGripWidget(vertical=True, parent=self.v_toolbar)
        v_layout.addWidget(self.v_grip)

        self.select_btn = QToolButton()
        self.select_btn.setIcon(create_pointer_icon())
        self.select_btn.setIconSize(QSize(36, 36))
        self.select_btn.setToolTip("Select / Move selection & Resize annotations")
        self.select_btn.setCheckable(True)
        self.select_btn.setChecked(True)
        self.select_btn.setFixedSize(42, 42)
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.clicked.connect(lambda: self.select_tool("select"))
        v_layout.addWidget(self.select_btn)

        self.shapes_btn = QToolButton()
        self.shapes_btn.setIcon(create_rect_icon())
        self.shapes_btn.setIconSize(QSize(36, 36))
        self.shapes_btn.setToolTip("Shapes (Rectangle ▢, Circle ○, Arrow ➔)")
        self.shapes_btn.setCheckable(True)
        self.shapes_btn.setFixedSize(42, 42)
        self.shapes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.shapes_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        shapes_menu = QMenu(self.shapes_btn)
        act_rect = shapes_menu.addAction("▢   Rectangle")
        act_rect.triggered.connect(lambda: self.select_tool("rect"))
        act_circle = shapes_menu.addAction("○   Circle")
        act_circle.triggered.connect(lambda: self.select_tool("circle"))
        act_arrow = shapes_menu.addAction("↗   Arrow")
        act_arrow.triggered.connect(lambda: self.select_tool("arrow"))
        self.shapes_btn.setMenu(shapes_menu)
        v_layout.addWidget(self.shapes_btn)

        self.pencil_btn = QToolButton()
        self.pencil_btn.setIcon(create_pencil_icon())
        self.pencil_btn.setIconSize(QSize(36, 36))
        self.pencil_btn.setToolTip("Freehand Pencil & Highlighter")
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setFixedSize(42, 42)
        self.pencil_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pencil_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        pencil_menu = QMenu(self.pencil_btn)
        act_pencil = pencil_menu.addAction("✏   Pencil")
        act_pencil.triggered.connect(lambda: self.select_tool("pencil"))
        act_highlighter = pencil_menu.addAction("🖍   Highlighter")
        act_highlighter.triggered.connect(lambda: self.select_tool("highlighter"))
        self.pencil_btn.setMenu(pencil_menu)
        v_layout.addWidget(self.pencil_btn)

        self.step_btn = QToolButton()
        self.step_btn.setText("①")
        self.step_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.step_btn.setToolTip("Step Badge Number Counter ① ② ③")
        self.step_btn.setCheckable(True)
        self.step_btn.setFixedSize(42, 42)
        self.step_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.step_btn.clicked.connect(lambda: self.select_tool("step"))
        v_layout.addWidget(self.step_btn)

        self.mosaic_btn = QToolButton()
        self.mosaic_btn.setIcon(create_mosaic_icon())
        self.mosaic_btn.setIconSize(QSize(36, 36))
        self.mosaic_btn.setToolTip("Privacy Obfuscation (Mosaic Pixelate & Blackout)")
        self.mosaic_btn.setCheckable(True)
        self.mosaic_btn.setFixedSize(42, 42)
        self.mosaic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mosaic_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        mosaic_menu = QMenu(self.mosaic_btn)
        act_mosaic = mosaic_menu.addAction("░░  Mosaic Pixelate")
        act_mosaic.triggered.connect(lambda: self.select_tool("mosaic"))
        act_blackout = mosaic_menu.addAction("██  Blackout Redact")
        act_blackout.triggered.connect(lambda: self.select_tool("blackout"))
        self.mosaic_btn.setMenu(mosaic_menu)
        v_layout.addWidget(self.mosaic_btn)

        self.text_btn = QToolButton()
        self.text_btn.setText("T")
        self.text_btn.setFont(QFont("Times New Roman", 15, QFont.Weight.Bold))
        self.text_btn.setToolTip("Text Annotation (Rich Font Ribbon Toolbar)")
        self.text_btn.setCheckable(True)
        self.text_btn.setFixedSize(42, 42)
        self.text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_btn.clicked.connect(lambda: self.select_tool("text"))
        v_layout.addWidget(self.text_btn)

        # Nút Undo / Redo nằm trực tiếp trên thanh dọc
        self.undo_btn = QToolButton()
        self.undo_btn.setText("↶")
        self.undo_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.undo_btn.setToolTip("Undo last action (Ctrl+Z)")
        self.undo_btn.setFixedSize(42, 42)
        self.undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_btn.clicked.connect(self.undo)
        v_layout.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↷")
        self.redo_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.redo_btn.setToolTip("Redo action (Ctrl+Y)")
        self.redo_btn.setFixedSize(42, 42)
        self.redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.redo_btn.clicked.connect(self.redo)
        v_layout.addWidget(self.redo_btn)

        self.h_toolbar = DraggableToolbarPanel(self)
        self.h_toolbar.setObjectName("toolbarPanel")
        self.h_toolbar.setStyleSheet(common_toolbar_style)

        h_layout = QHBoxLayout(self.h_toolbar)
        h_layout.setContentsMargins(6, 6, 8, 6)
        h_layout.setSpacing(6)

        # Drag grip handle at left of horizontal toolbar
        self.h_grip = DragGripWidget(vertical=False, parent=self.h_toolbar)
        h_layout.addWidget(self.h_grip)

        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.setFont(QFont("Segoe UI Symbol", 14))
        self.settings_btn.setToolTip("Settings & Options")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings_window)
        h_layout.addWidget(self.settings_btn)

        self.watermark_btn = QToolButton()
        self.watermark_btn.setIcon(create_watermark_icon())
        self.watermark_btn.setIconSize(QSize(28, 28))
        self.watermark_btn.setToolTip("Watermark Stamp (Text Watermark & Image Logo)")
        self.watermark_btn.setFixedSize(36, 36)
        self.watermark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.watermark_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        wm_menu = QMenu(self.watermark_btn)
        act_timestamp = wm_menu.addAction("🕒  Insert Timestamp Stamp")
        act_timestamp.triggered.connect(self.add_timestamp_stamp)
        act_wm_text = wm_menu.addAction("🏷   Insert Text Watermark")
        act_wm_text.triggered.connect(self.add_text_watermark_stamp)
        act_wm_logo = wm_menu.addAction("🖼   Insert Image Logo Watermark")
        act_wm_logo.triggered.connect(self.add_logo_watermark_stamp)
        self.watermark_btn.setMenu(wm_menu)
        h_layout.addWidget(self.watermark_btn)

        self.pin_btn = QToolButton()
        self.pin_btn.setText("📌")
        self.pin_btn.setFont(QFont("Segoe UI Symbol", 14))
        self.pin_btn.setToolTip("Pin cropped image on top of screen")
        self.pin_btn.setFixedSize(36, 36)
        self.pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_btn.clicked.connect(self.pin_image)
        h_layout.addWidget(self.pin_btn)

        self.ocr_btn = QToolButton()
        self.ocr_btn.setText("OCR")
        self.ocr_btn.setToolTip("Extract text from selection via OCR")
        self.ocr_btn.setFixedSize(48, 36)
        self.ocr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ocr_btn.setStyleSheet("""
            QToolButton {
                background-color: #E0F2FE;
                color: #0284C7;
                border-radius: 18px;
                font-weight: 700;
                font-size: 12px;
            }
            QToolButton:hover {
                background-color: #BAE6FD;
                color: #0369A1;
            }
        """)
        self.ocr_btn.clicked.connect(self.perform_ocr_extraction)
        h_layout.addWidget(self.ocr_btn)

        self.save_btn = QToolButton()
        self.save_btn.setText("💾")
        self.save_btn.setFont(QFont("Segoe UI Symbol", 14))
        self.save_btn.setToolTip("Save image to file (Ctrl+S)")
        self.save_btn.setFixedSize(36, 36)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_to_file)
        h_layout.addWidget(self.save_btn)

        self.close_btn = QToolButton()
        self.close_btn.setText("✕")
        self.close_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.close_btn.setToolTip("Close / Cancel (Esc)")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        h_layout.addWidget(self.close_btn)

        self.copy_btn = QPushButton("✔")
        self.copy_btn.setObjectName("zaloCopyBtn")
        self.copy_btn.setToolTip("Copy image to Clipboard & Exit (Ctrl+C / Enter)")
        self.copy_btn.setFixedSize(36, 36)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_and_close)
        h_layout.addWidget(self.copy_btn)

        self.sub_toolbar = DraggableToolbarPanel(self)
        self.sub_toolbar.setObjectName("wordSubToolbar")
        self.sub_toolbar.setStyleSheet(word_toolbar_style)
        sub_layout = QHBoxLayout(self.sub_toolbar)
        sub_layout.setContentsMargins(6, 6, 6, 6)
        sub_layout.setSpacing(6)

        self.v_toolbar.hide()
        self.h_toolbar.hide()
        self.sub_toolbar.hide()

    def update_toolbar_positions(self):
        if self.selection_rect.isEmpty() or not self.selection_rect.isValid():
            self.v_toolbar.hide()
            self.h_toolbar.hide()
            self.sub_toolbar.hide()
            return

        r = self.selection_rect.normalized()
        v_size = self.v_toolbar.sizeHint()
        h_size = self.h_toolbar.sizeHint()

        # 1. Vertical Toolbar
        if not getattr(self.v_toolbar, "is_user_moved", False):
            vx = r.left() - v_size.width() - 10
            vy = r.top()
            if vx < 10:
                vx = r.left() + 10
                vy = r.top() + 10
            vy = max(10, min(self.height() - v_size.height() - 10, vy))
            self.v_toolbar.move(vx, vy)
        else:
            cx = max(0, min(self.width() - self.v_toolbar.width(), self.v_toolbar.x()))
            cy = max(0, min(self.height() - self.v_toolbar.height(), self.v_toolbar.y()))
            self.v_toolbar.move(cx, cy)

        self.v_toolbar.show()
        self.v_toolbar.raise_()

        # 2. Horizontal Toolbar
        if not getattr(self.h_toolbar, "is_user_moved", False):
            hx = r.right() - h_size.width()
            hy = r.bottom() + 10
            if hy + h_size.height() > self.height() - 10:
                hy = r.top() - h_size.height() - 10
                if hy < 10:
                    hy = r.bottom() - h_size.height() - 10
            hx = max(10, min(self.width() - h_size.width() - 10, hx))
            self.h_toolbar.move(hx, hy)
        else:
            cx = max(0, min(self.width() - self.h_toolbar.width(), self.h_toolbar.x()))
            cy = max(0, min(self.height() - self.h_toolbar.height(), self.h_toolbar.y()))
            self.h_toolbar.move(cx, cy)

        self.h_toolbar.show()
        self.h_toolbar.raise_()

        # 3. Sub Toolbar (Always check current active tool / selected item)
        should_show_sub = False
        if self.current_tool == "text" or (self.selected_annotation and isinstance(self.selected_annotation, TextItem)):
            if getattr(self, "_current_sub_toolbar_mode", None) != "text":
                self.setup_text_sub_toolbar()
            should_show_sub = True
        elif self.current_tool in ("rect", "circle", "arrow", "pencil", "highlighter", "blackout") or (self.selected_annotation and isinstance(self.selected_annotation, ShapeItem)):
            if getattr(self, "_current_sub_toolbar_mode", None) != "shape":
                self.setup_shape_sub_toolbar()
            should_show_sub = True

        if should_show_sub:
            self.sub_toolbar.show()
            self.sub_toolbar.adjustSize()
            sub_size = self.sub_toolbar.sizeHint()
            if not getattr(self.sub_toolbar, "is_user_moved", False):
                sx = self.h_toolbar.x()
                sy = self.h_toolbar.y() + self.h_toolbar.height() + 6
                if sy + sub_size.height() > self.height() - 10:
                    sy = self.h_toolbar.y() - sub_size.height() - 6
                sx = max(10, min(self.width() - sub_size.width() - 10, sx))
                self.sub_toolbar.move(sx, sy)
            else:
                cx = max(0, min(self.width() - self.sub_toolbar.width(), self.sub_toolbar.x()))
                cy = max(0, min(self.height() - self.sub_toolbar.height(), self.sub_toolbar.y()))
                self.sub_toolbar.move(cx, cy)
            self.sub_toolbar.raise_()
        else:
            self.sub_toolbar.hide()

    def select_tool(self, tool_id: str):
        self.commit_inline_text()
        self.current_tool = tool_id
        self.selected_annotation = None

        self.select_btn.setChecked(tool_id == "select")
        self.shapes_btn.setChecked(tool_id in ("rect", "circle", "arrow"))
        self.pencil_btn.setChecked(tool_id in ("pencil", "highlighter"))
        self.step_btn.setChecked(tool_id == "step")
        self.mosaic_btn.setChecked(tool_id in ("mosaic", "blackout"))
        self.text_btn.setChecked(tool_id == "text")

        if tool_id == "text":
            self.setup_text_sub_toolbar()
            self.sub_toolbar.show()
        elif tool_id in ("rect", "circle", "arrow", "pencil", "highlighter", "blackout"):
            self.setup_shape_sub_toolbar()
            self.sub_toolbar.show()
        else:
            self._current_sub_toolbar_mode = None
            self.sub_toolbar.hide()

        self.update_toolbar_positions()

    def setup_text_sub_toolbar(self):
        if not hasattr(self, "sub_toolbar") or not self.sub_toolbar:
            return

        self._current_sub_toolbar_mode = "text"

        sub_layout = self.sub_toolbar.layout()
        while sub_layout.count():
            item = sub_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        sub_layout.setContentsMargins(6, 6, 6, 6)
        sub_layout.setSpacing(6)

        # 1. Drag Grip Handle
        sub_grip = DragGripWidget(vertical=False, parent=self.sub_toolbar)
        sub_layout.addWidget(sub_grip)

        # 2. Text Color Button (Màu chữ)
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(24, 24)
        self.text_color_btn.setToolTip("Màu chữ (Font Color)")
        self.text_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_text_color_btn()

        def show_text_color_popover():
            popover = QMenu(self.text_color_btn)
            popover.setStyleSheet("""
                QMenu {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0,0,0,0.08);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
            sw_widget = QWidget()
            sw_lay = QHBoxLayout(sw_widget)
            sw_lay.setContentsMargins(4, 4, 4, 4)
            sw_lay.setSpacing(6)

            text_presets = [
                ("#FFFFFF", "Trắng"),
                ("#18181B", "Đen"),
                ("#EF4444", "Đỏ"),
                ("#3B82F6", "Xanh dương"),
                ("#10B981", "Xanh lá"),
                ("#F59E0B", "Cam"),
                ("#8B5CF6", "Tím"),
                ("#EC4899", "Hồng"),
            ]

            for hex_val, name in text_presets:
                btn = QPushButton()
                btn.setFixedSize(20, 20)
                btn.setToolTip(name)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                cur_hex = self.current_color.name().upper()
                is_cur = (hex_val.upper() == cur_hex)
                ring = "2px solid #2563EB" if is_cur else "1.5px solid rgba(0,0,0,0.12)"
                btn.setStyleSheet(f"background-color: {hex_val}; border-radius: 10px; border: {ring};")

                def apply_tc(h=hex_val):
                    self.current_color = QColor(h)
                    self._update_text_color_btn()
                    self._update_inline_text_edit_style()
                    if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
                        self.selected_annotation.color = self.current_color
                        self.update()
                    popover.close()

                btn.clicked.connect(apply_tc)
                sw_lay.addWidget(btn)

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(20, 20)
            plus_btn.setToolTip("Màu tùy chọn...")
            plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F4F4F5;
                    color: #52525B;
                    border: 1.5px solid rgba(0,0,0,0.12);
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #DBEAFE;
                    color: #2563EB;
                    border: 2px solid #2563EB;
                }
            """)

            def open_tc_picker():
                popover.close()
                col = QColorDialog.getColor(self.current_color, self, "Chọn màu chữ")
                if col.isValid():
                    self.current_color = col
                    self._update_text_color_btn()
                    self._update_inline_text_edit_style()
                    if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
                        self.selected_annotation.color = self.current_color
                        self.update()

            plus_btn.clicked.connect(open_tc_picker)
            sw_lay.addWidget(plus_btn)

            act = QWidgetAction(popover)
            act.setDefaultWidget(sw_widget)
            popover.addAction(act)
            popover.exec(self.text_color_btn.mapToGlobal(QPoint(0, -sw_widget.sizeHint().height() - 8)))

        self.text_color_btn.clicked.connect(show_text_color_popover)
        sub_layout.addWidget(self.text_color_btn)

        sub_layout.addWidget(make_divider())

        # 3. Font Family
        self.font_combo = QComboBox()
        self.font_combo.setObjectName("fontFamilyCombo")
        font_list = ["Segoe UI", "Arial", "Calibri", "Times New Roman", "Consolas", "JetBrains Mono", "Tahoma", "Verdana", "Inter"]
        self.font_combo.addItems(font_list)
        self.font_combo.setCurrentText(getattr(self, "current_font_family", "Segoe UI"))
        self.font_combo.setToolTip("Font chữ")
        self.font_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        sub_layout.addWidget(self.font_combo)

        # 4. Font Size
        self.size_spin = QSpinBox()
        self.size_spin.setObjectName("fontSizeSpin")
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(getattr(self, "current_font_size", 14))
        self.size_spin.setToolTip("Cỡ chữ (pt)")
        self.size_spin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.size_spin.valueChanged.connect(self.on_size_changed)
        sub_layout.addWidget(self.size_spin)

        sub_layout.addWidget(make_divider())

        # 5. Bold, Italic, Underline Segmented Buttons
        seg_container = QWidget()
        seg_container.setStyleSheet("background: transparent; border: none;")
        seg_layout = QHBoxLayout(seg_container)
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(0)

        self.bold_btn = QToolButton()
        self.bold_btn.setObjectName("segBtnLeft")
        self.bold_btn.setText("B")
        self.bold_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.bold_btn.setToolTip("In đậm (Bold)")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setChecked(getattr(self, "is_bold", True))
        self.bold_btn.setFixedSize(30, 30)
        self.bold_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bold_btn.clicked.connect(self.toggle_bold)
        seg_layout.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setObjectName("segBtnMid")
        self.italic_btn.setText("I")
        italic_font = QFont("Segoe UI", 12)
        italic_font.setItalic(True)
        self.italic_btn.setFont(italic_font)
        self.italic_btn.setToolTip("In nghiêng (Italic)")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setChecked(getattr(self, "is_italic", False))
        self.italic_btn.setFixedSize(30, 30)
        self.italic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.italic_btn.clicked.connect(self.toggle_italic)
        seg_layout.addWidget(self.italic_btn)

        self.underline_btn = QToolButton()
        self.underline_btn.setObjectName("segBtnRight")
        self.underline_btn.setText("U")
        u_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        u_font.setUnderline(True)
        self.underline_btn.setFont(u_font)
        self.underline_btn.setToolTip("Gạch chân (Underline)")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setChecked(getattr(self, "is_underline", False))
        self.underline_btn.setFixedSize(30, 30)
        self.underline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.underline_btn.clicked.connect(self.toggle_underline)
        seg_layout.addWidget(self.underline_btn)

        sub_layout.addWidget(seg_container)
        sub_layout.addWidget(make_divider())

        # 6. Text Background Mode Combo
        self.text_bg_combo = QComboBox()
        self.text_bg_combo.setObjectName("textBgCombo")
        self.text_bg_combo.addItem("Trong suốt")
        self.text_bg_combo.addItem("Nền thẻ tối")
        self.text_bg_combo.addItem("Nền màu tùy chọn")

        bg_mode_map = {"none": 0, "badge": 1, "color": 2}
        self.text_bg_combo.setCurrentIndex(bg_mode_map.get(getattr(self, "current_text_bg_mode", "badge"), 1))
        self.text_bg_combo.setToolTip("Kiểu nền chữ")
        self.text_bg_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_bg_combo.currentIndexChanged.connect(self.on_text_bg_changed)
        sub_layout.addWidget(self.text_bg_combo)

        # 7. Text Background Color Swatch
        self.text_bg_swatch = QPushButton()
        self.text_bg_swatch.setToolTip("Màu nền chữ")
        self.text_bg_swatch.setFixedSize(24, 24)
        self.text_bg_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_bg_swatch()

        def show_bg_color_popover():
            popover = QMenu(self.text_bg_swatch)
            popover.setStyleSheet("""
                QMenu {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0,0,0,0.08);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
            sw_widget = QWidget()
            sw_lay = QHBoxLayout(sw_widget)
            sw_lay.setContentsMargins(4, 4, 4, 4)
            sw_lay.setSpacing(6)

            preset_colors = [
                ("#161624", "Thẻ tối"),
                ("#000000", "Đen"),
                ("#FFFFFF", "Trắng"),
                ("#71717A", "Xám"),
                ("#DBEAFE", "Xanh nhạt"),
                ("#FEF3C7", "Vàng nhạt"),
                ("#FCE7F3", "Hồng nhạt"),
                ("transparent", "Trong suốt"),
            ]

            for hex_val, name in preset_colors:
                btn = QPushButton()
                btn.setFixedSize(20, 20)
                btn.setToolTip(name)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                if hex_val == "transparent":
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #D4D4D8, stop:0.49 #D4D4D8,
                                stop:0.5 #FFFFFF, stop:1 #FFFFFF);
                            border-radius: 10px;
                            border: 1.5px solid rgba(0,0,0,0.12);
                        }
                        QPushButton:hover { border: 2px solid #2563EB; }
                    """)
                else:
                    cur_hex = self.current_bg_color.name().upper()
                    is_cur = (hex_val.upper() == cur_hex)
                    ring = "2px solid #2563EB" if is_cur else "1.5px solid rgba(0,0,0,0.12)"
                    btn.setStyleSheet(f"background-color: {hex_val}; border-radius: 10px; border: {ring};")

                def apply_bg(h=hex_val):
                    if h == "transparent":
                        self.current_text_bg_mode = "none"
                        self.text_bg_combo.setCurrentIndex(0)
                    else:
                        self.current_bg_color = QColor(h)
                        self.current_text_bg_mode = "color"
                        self.text_bg_combo.setCurrentIndex(2)

                    self._update_bg_swatch()
                    self._update_inline_text_edit_style()

                    if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
                        self.selected_annotation.bg_color = self.current_bg_color
                        self.selected_annotation.bg_mode = self.current_text_bg_mode
                        self.update()

                    popover.close()

                btn.clicked.connect(apply_bg)
                sw_lay.addWidget(btn)

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(20, 20)
            plus_btn.setToolTip("Màu nền tùy chọn...")
            plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F4F4F5;
                    color: #52525B;
                    border: 1.5px solid rgba(0,0,0,0.12);
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #DBEAFE;
                    color: #2563EB;
                    border: 2px solid #2563EB;
                }
            """)

            def open_custom_bg_picker():
                popover.close()
                col = QColorDialog.getColor(self.current_bg_color, self, "Chọn màu nền chữ")
                if col.isValid():
                    self.current_bg_color = col
                    self.current_text_bg_mode = "color"
                    self.text_bg_combo.setCurrentIndex(2)
                    self._update_bg_swatch()
                    self._update_inline_text_edit_style()
                    if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
                        self.selected_annotation.bg_color = self.current_bg_color
                        self.selected_annotation.bg_mode = self.current_text_bg_mode
                        self.update()

            plus_btn.clicked.connect(open_custom_bg_picker)
            sw_lay.addWidget(plus_btn)

            swatch_action = QWidgetAction(popover)
            swatch_action.setDefaultWidget(sw_widget)
            popover.addAction(swatch_action)
            popover.exec(self.text_bg_swatch.mapToGlobal(QPoint(0, -sw_widget.sizeHint().height() - 8)))

        self.text_bg_swatch.clicked.connect(show_bg_color_popover)
        sub_layout.addWidget(self.text_bg_swatch)

        self.sub_toolbar.adjustSize()

    def _update_text_color_btn(self):
        if hasattr(self, "text_color_btn") and self.text_color_btn:
            col = getattr(self, "current_color", QColor("#FFFFFF"))
            self.text_color_btn.setStyleSheet(
                f"background-color: {col.name()}; border-radius: 12px; "
                f"border: 2px solid rgba(0,0,0,0.15);"
            )

    def _update_bg_swatch(self):
        if hasattr(self, 'text_bg_swatch') and self.text_bg_swatch:
            bg = getattr(self, 'current_bg_color', QColor("#161624"))
            if getattr(self, 'current_text_bg_mode', 'badge') == 'none':
                self.text_bg_swatch.setStyleSheet(
                    "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
                    "stop:0 #D4D4D8, stop:0.49 #D4D4D8,"
                    "stop:0.5 #FFFFFF, stop:1 #FFFFFF);"
                    "border-radius: 12px; border: 1.5px solid rgba(0,0,0,0.15);"
                )
            else:
                self.text_bg_swatch.setStyleSheet(
                    f"background-color: {bg.name()}; border-radius: 12px; "
                    f"border: 1.5px solid rgba(0,0,0,0.15);"
                )

    def _update_inline_text_edit_style(self):
        if not hasattr(self, 'inline_text_edit') or not self.inline_text_edit:
            return
        text_color = getattr(self, 'current_color', QColor("#FFFFFF"))
        bg_color = getattr(self, 'current_bg_color', QColor("#161624"))
        bg_mode = getattr(self, 'current_text_bg_mode', 'badge')
        color_hex = text_color.name()

        if bg_mode == "badge":
            bg_css = "rgba(16, 16, 24, 235)"
            border_css = "1.5px solid #2563EB"
        elif bg_mode == "none":
            bg_css = "transparent"
            border_css = "1.5px dashed #2563EB"
        else:
            bg_css = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 230)"
            border_css = "1.5px solid #2563EB"

        font_weight = "bold" if getattr(self, "is_bold", True) else "normal"
        self.inline_text_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_css};
                color: {color_hex};
                border: {border_css};
                border-radius: 6px;
                padding: 2px 8px;
                font-weight: {font_weight};
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
            }}
        """)

    def setup_shape_sub_toolbar(self):
        if not hasattr(self, "sub_toolbar") or not self.sub_toolbar:
            return

        self._current_sub_toolbar_mode = "shape"

        sub_layout = self.sub_toolbar.layout()
        while sub_layout.count():
            item = sub_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        sub_layout.setContentsMargins(8, 6, 8, 6)
        sub_layout.setSpacing(8)

        # 1. Drag Grip
        sub_grip = DragGripWidget(vertical=False, parent=self.sub_toolbar)
        sub_layout.addWidget(sub_grip)

        # 2. Color Label & Swatch
        color_lbl = QLabel("Màu nét:")
        color_lbl.setStyleSheet("color: #3F3F46; font-size: 12px; font-weight: 600;")
        sub_layout.addWidget(color_lbl)

        self.shape_color_btn = QPushButton()
        self.shape_color_btn.setFixedSize(24, 24)
        self.shape_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.shape_color_btn.setToolTip("Màu nét vẽ (Shape Color)")
        self.shape_color_btn.setStyleSheet(
            f"background-color: {self.current_color.name()}; border-radius: 12px; "
            f"border: 2px solid rgba(0,0,0,0.15);"
        )

        def show_shape_color_popover():
            popover = QMenu(self.shape_color_btn)
            popover.setStyleSheet("""
                QMenu {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0,0,0,0.08);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
            sw_widget = QWidget()
            sw_lay = QHBoxLayout(sw_widget)
            sw_lay.setContentsMargins(4, 4, 4, 4)
            sw_lay.setSpacing(6)

            shape_presets = [
                ("#EF4444", "Đỏ"),
                ("#F59E0B", "Cam"),
                ("#10B981", "Xanh lá"),
                ("#3B82F6", "Xanh dương"),
                ("#8B5CF6", "Tím"),
                ("#EC4899", "Hồng"),
                ("#FFFFFF", "Trắng"),
                ("#18181B", "Đen"),
            ]

            for hex_val, name in shape_presets:
                btn = QPushButton()
                btn.setFixedSize(20, 20)
                btn.setToolTip(name)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                cur_hex = self.current_color.name().upper()
                is_cur = (hex_val.upper() == cur_hex)
                ring = "2px solid #2563EB" if is_cur else "1.5px solid rgba(0,0,0,0.12)"
                btn.setStyleSheet(f"background-color: {hex_val}; border-radius: 10px; border: {ring};")

                def apply_sc(h=hex_val):
                    self.current_color = QColor(h)
                    self.shape_color_btn.setStyleSheet(
                        f"background-color: {self.current_color.name()}; border-radius: 12px; "
                        f"border: 2px solid rgba(0,0,0,0.15);"
                    )
                    if self.selected_annotation:
                        self.selected_annotation.color = self.current_color
                        self.update()
                    popover.close()

                btn.clicked.connect(apply_sc)
                sw_lay.addWidget(btn)

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(20, 20)
            plus_btn.setToolTip("Màu tùy chọn...")
            plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F4F4F5;
                    color: #52525B;
                    border: 1.5px solid rgba(0,0,0,0.12);
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #DBEAFE;
                    color: #2563EB;
                    border: 2px solid #2563EB;
                }
            """)

            def open_sc_picker():
                popover.close()
                col = QColorDialog.getColor(self.current_color, self, "Chọn màu nét vẽ")
                if col.isValid():
                    self.current_color = col
                    self.shape_color_btn.setStyleSheet(
                        f"background-color: {self.current_color.name()}; border-radius: 12px; "
                        f"border: 2px solid rgba(0,0,0,0.15);"
                    )
                    if self.selected_annotation:
                        self.selected_annotation.color = self.current_color
                        self.update()

            plus_btn.clicked.connect(open_sc_picker)
            sw_lay.addWidget(plus_btn)

            act = QWidgetAction(popover)
            act.setDefaultWidget(sw_widget)
            popover.addAction(act)
            popover.exec(self.shape_color_btn.mapToGlobal(QPoint(0, -sw_widget.sizeHint().height() - 8)))

        self.shape_color_btn.clicked.connect(show_shape_color_popover)
        sub_layout.addWidget(self.shape_color_btn)

        sub_layout.addWidget(make_divider())

        # 3. Stroke Width SpinBox
        width_lbl = QLabel("Độ dày:")
        width_lbl.setStyleSheet("color: #3F3F46; font-size: 12px; font-weight: 600;")
        sub_layout.addWidget(width_lbl)

        self.stroke_spin = QSpinBox()
        self.stroke_spin.setRange(1, 48)
        self.stroke_spin.setSuffix(" px")
        self.stroke_spin.setValue(self.current_stroke_width)
        self.stroke_spin.setFixedSize(76, 28)
        self.stroke_spin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stroke_spin.setStyleSheet("""
            QSpinBox {
                background: #FFFFFF;
                color: #18181B;
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 6px;
                padding: 2px 4px 2px 6px;
                font-weight: 600;
                font-size: 12px;
            }
            QSpinBox:focus {
                border: 1.5px solid #2563EB;
            }
        """)

        def on_stroke_changed(val):
            self.current_stroke_width = val
            if self.selected_annotation and hasattr(self.selected_annotation, "stroke_width"):
                self.selected_annotation.stroke_width = val
                self.update()

        self.stroke_spin.valueChanged.connect(on_stroke_changed)
        sub_layout.addWidget(self.stroke_spin)

        self.sub_toolbar.adjustSize()

    def on_font_changed(self, font_family: str):
        self.current_font_family = font_family
        if self.inline_text_edit:
            font = self.inline_text_edit.font()
            font.setFamily(font_family)
            self.inline_text_edit.setFont(font)
            m = QFontMetrics(font)
            txt = self.inline_text_edit.text()
            nw = max(140, m.horizontalAdvance(txt if txt else "Nhập văn bản...") + 28)
            nh = max(32, m.height() + 10)
            self.inline_text_edit.resize(nw, nh)
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.font.setFamily(font_family)
            self.selected_annotation.calc_rect()
            self.update()

    def on_size_changed(self, font_size: int):
        self.current_font_size = font_size
        if self.inline_text_edit:
            font = self.inline_text_edit.font()
            font.setPointSize(font_size)
            self.inline_text_edit.setFont(font)
            m = QFontMetrics(font)
            txt = self.inline_text_edit.text()
            nw = max(140, m.horizontalAdvance(txt if txt else "Nhập văn bản...") + 28)
            nh = max(32, m.height() + 10)
            self.inline_text_edit.resize(nw, nh)
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.font.setPointSize(font_size)
            self.selected_annotation.calc_rect()
            self.update()

    def toggle_bold(self):
        self.is_bold = self.bold_btn.isChecked()
        if self.inline_text_edit:
            font = self.inline_text_edit.font()
            font.setBold(self.is_bold)
            self.inline_text_edit.setFont(font)
            self._update_inline_text_edit_style()
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.font.setBold(self.is_bold)
            self.selected_annotation.calc_rect()
            self.update()

    def toggle_italic(self):
        self.is_italic = self.italic_btn.isChecked()
        if self.inline_text_edit:
            font = self.inline_text_edit.font()
            font.setItalic(self.is_italic)
            self.inline_text_edit.setFont(font)
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.font.setItalic(self.is_italic)
            self.selected_annotation.calc_rect()
            self.update()

    def toggle_underline(self):
        self.is_underline = self.underline_btn.isChecked()
        if self.inline_text_edit:
            font = self.inline_text_edit.font()
            font.setUnderline(self.is_underline)
            self.inline_text_edit.setFont(font)
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.font.setUnderline(self.is_underline)
            self.selected_annotation.calc_rect()
            self.update()

    def on_text_bg_changed(self, index: int):
        mode_map = {0: "none", 1: "badge", 2: "color"}
        self.current_text_bg_mode = mode_map.get(index, "badge")
        self._update_bg_swatch()
        self._update_inline_text_edit_style()
        if self.selected_annotation and isinstance(self.selected_annotation, TextItem):
            self.selected_annotation.bg_mode = self.current_text_bg_mode
            self.update()

    def open_inline_text_editor(self, pos: QPoint, target_item=None):
        self.commit_inline_text()
        self.editing_target_item = target_item
        initial_txt = target_item.text if target_item else ""

        if target_item and isinstance(target_item, TextItem):
            self.current_font_family = target_item.font.family()
            ps = target_item.font.pointSize()
            if ps <= 0:
                ps = target_item.font.pixelSize() if target_item.font.pixelSize() > 0 else 14
            self.current_font_size = max(8, ps)
            self.is_bold = target_item.font.bold()
            self.is_italic = target_item.font.italic()
            self.is_underline = target_item.font.underline()
            self.current_color = target_item.color
            if hasattr(target_item, "bg_color") and target_item.bg_color:
                self.current_bg_color = target_item.bg_color
            if hasattr(target_item, "bg_mode"):
                self.current_text_bg_mode = target_item.bg_mode

        self.setup_text_sub_toolbar()
        self.sub_toolbar.show()
        self.update_toolbar_positions()

        self.inline_text_edit = QLineEdit(self)
        font = QFont(self.current_font_family, max(8, self.current_font_size))
        font.setBold(self.is_bold)
        font.setItalic(self.is_italic)
        font.setUnderline(self.is_underline)
        self.inline_text_edit.setFont(font)

        self._update_inline_text_edit_style()

        metrics = QFontMetrics(font)
        w = max(140, metrics.horizontalAdvance(initial_txt if initial_txt else "Nhập văn bản...") + 28)
        h = max(32, metrics.height() + 10)

        # Giới hạn tọa độ nếu nằm trong selection_rect
        if not self.selection_rect.isEmpty():
            px = max(self.selection_rect.left() + 2, min(pos.x(), self.selection_rect.right() - w - 2))
            py = max(self.selection_rect.top() + 2, min(pos.y(), self.selection_rect.bottom() - h - 2))
            pos = QPoint(px, py)

        self.inline_text_edit.setGeometry(pos.x(), pos.y(), w, h)
        self.inline_text_edit.setText(initial_txt)
        self.inline_text_edit.setPlaceholderText("Nhập văn bản...")
        self.inline_text_edit.setFocus()
        if initial_txt:
            self.inline_text_edit.selectAll()

        def update_edit_size(txt):
            if self.inline_text_edit:
                m = QFontMetrics(self.inline_text_edit.font())
                nw = max(140, m.horizontalAdvance(txt if txt else "Nhập văn bản...") + 28)
                nh = max(32, m.height() + 10)
                self.inline_text_edit.resize(nw, nh)

        self.inline_text_edit.textChanged.connect(update_edit_size)
        self.inline_text_edit.show()
        self.inline_text_edit.raise_()

        self.inline_text_edit.returnPressed.connect(self.commit_inline_text)
        self.inline_text_edit.editingFinished.connect(self.commit_inline_text)
        self.update()

    def commit_inline_text(self):
        if self.inline_text_edit:
            txt = self.inline_text_edit.text().strip()
            pos = self.inline_text_edit.pos()
            font = QFont(self.inline_text_edit.font())

            target_item = getattr(self, "editing_target_item", None)
            self.inline_text_edit.deleteLater()
            self.inline_text_edit = None
            self.editing_target_item = None

            if target_item and isinstance(target_item, TextItem):
                if txt:
                    target_item.text = txt
                    target_item.font = font
                    target_item.color = self.current_color
                    target_item.bg_color = self.current_bg_color
                    target_item.bg_mode = self.current_text_bg_mode
                    target_item.calc_rect()
                    self.selected_annotation = target_item
                else:
                    if target_item in self.annotations:
                        self.annotations.remove(target_item)
                    if self.selected_annotation == target_item:
                        self.selected_annotation = None
                self.update()
            elif target_item and isinstance(target_item, WatermarkItem):
                if txt:
                    target_item.text = txt
                    target_item.calc_rect()
                    self.selected_annotation = target_item
                self.update()
            else:
                if txt:
                    item = TextItem(pos, txt, font, self.current_color, bg_color=self.current_bg_color, bg_mode=self.current_text_bg_mode)
                    self.annotations.append(item)
                    self.redo_stack.clear()
                    self.selected_annotation = item
                    self.update()

            if self.current_tool != "text" and not (self.selected_annotation and isinstance(self.selected_annotation, TextItem)):
                if hasattr(self, "sub_toolbar") and self.sub_toolbar:
                    self.sub_toolbar.hide()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            clicked_item = self.get_annotation_at(pos)
            if clicked_item and isinstance(clicked_item, (TextItem, WatermarkItem)):
                self.open_inline_text_editor(clicked_item.pos, target_item=clicked_item)
                event.accept()

    def mousePressEvent(self, event):
        pos = event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            if (self.v_toolbar and self.v_toolbar.geometry().contains(pos) and self.v_toolbar.isVisible()) or \
               (self.h_toolbar and self.h_toolbar.geometry().contains(pos) and self.h_toolbar.isVisible()) or \
               (self.sub_toolbar and self.sub_toolbar.geometry().contains(pos) and self.sub_toolbar.isVisible()):
                return
            if self.inline_text_edit and self.inline_text_edit.geometry().contains(pos):
                return

            self.commit_inline_text()

            if not self.selection_rect.isEmpty():
                self.active_selection_handle = self.get_selection_handle_at(pos)
                if self.active_selection_handle:
                    self.is_resizing_selection = True
                    self.drag_start = pos
                    self.initial_move_rect = QRect(self.selection_rect)
                    return

                if self.current_tool == "select":
                    clicked_item = self.get_annotation_at(pos)
                    if clicked_item:
                        self.selected_annotation = clicked_item
                        self.active_handle = self.get_handle_at(pos, clicked_item)

                        if self.active_handle:
                            self.is_resizing_annotation = True
                            self.initial_annotation_rect = QRect(clicked_item.rect) if hasattr(clicked_item, "rect") else QRect()
                            if isinstance(clicked_item, TextItem):
                                ps = clicked_item.font.pointSize()
                                if ps <= 0:
                                    ps = clicked_item.font.pixelSize() if clicked_item.font.pixelSize() > 0 else 14
                                self.initial_font_size = max(8, ps)
                        else:
                            self.is_dragging_annotation = True
                        self.drag_start = pos

                        if isinstance(clicked_item, TextItem):
                            self.current_font_family = clicked_item.font.family()
                            ps = clicked_item.font.pointSize()
                            if ps <= 0:
                                ps = clicked_item.font.pixelSize() if clicked_item.font.pixelSize() > 0 else 14
                            self.current_font_size = max(8, ps)
                            self.is_bold = clicked_item.font.bold()
                            self.is_italic = clicked_item.font.italic()
                            self.is_underline = clicked_item.font.underline()
                            self.current_color = clicked_item.color
                            self.current_bg_color = clicked_item.bg_color
                            self.current_text_bg_mode = clicked_item.bg_mode
                            self.setup_text_sub_toolbar()
                            self.sub_toolbar.show()
                            self.update_toolbar_positions()
                        elif isinstance(clicked_item, ShapeItem):
                            self.current_color = clicked_item.color
                            self.current_stroke_width = clicked_item.stroke_width
                            self.setup_shape_sub_toolbar()
                            self.sub_toolbar.show()
                            self.update_toolbar_positions()
                        else:
                            if hasattr(self, "sub_toolbar") and self.sub_toolbar:
                                self.sub_toolbar.hide()

                        self.update()
                        return
                    elif self.selection_rect.contains(pos):
                        self.selected_annotation = None
                        self.is_moving_selection = True
                        self.drag_start = pos
                        self.initial_move_rect = QRect(self.selection_rect)
                        self.update()
                        return
                    else:
                        # Click bên ngoài khung chọn cũ khi ở mode select -> tạo khung chọn mới
                        self.is_selecting = True
                        self.drag_start = pos
                        self.selection_rect = QRect(pos, pos)
                        self.selected_annotation = None
                        self.v_toolbar.hide()
                        self.h_toolbar.hide()
                        self.sub_toolbar.hide()
                        self.update()
                        return

            if self.current_tool == "text":
                self.open_inline_text_editor(pos)
                return
            elif self.current_tool == "step":
                item = StepItem(pos, self.step_counter, self.current_color)
                self.annotations.append(item)
                self.step_counter += 1
                self.redo_stack.clear()
                self.selected_annotation = item
                self.update()
                return

            if self.selection_rect.isEmpty():
                self.is_selecting = True
                self.drag_start = pos
                self.selection_rect = QRect(pos, pos)
                self.selected_annotation = None
                self.v_toolbar.hide()
                self.h_toolbar.hide()
                self.sub_toolbar.hide()
                self.current_drawing_item = None
            else:
                self.is_selecting = True
                self.drag_start = pos
                dummy_rect = QRect(pos, pos)
                if self.current_tool == "rect":
                    self.current_drawing_item = ShapeItem("rect", dummy_rect, self.current_color, self.current_stroke_width)
                elif self.current_tool == "circle":
                    self.current_drawing_item = ShapeItem("circle", dummy_rect, self.current_color, self.current_stroke_width)
                elif self.current_tool == "arrow":
                    self.current_drawing_item = ArrowItem(pos, pos, self.current_color, self.current_stroke_width)
                elif self.current_tool in ("pencil", "highlighter"):
                    self.current_drawing_item = PathItem([pos], self.current_color, self.current_stroke_width, tool_type=self.current_tool)
                elif self.current_tool == "mosaic":
                    self.current_drawing_item = MosaicItem(dummy_rect)
                elif self.current_tool == "blackout":
                    self.current_drawing_item = BlackoutItem(dummy_rect)

            self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.is_resizing_selection and self.active_selection_handle:
            r = QRect(self.initial_move_rect)
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()

            if self.active_selection_handle == "top_left":
                r.setTopLeft(r.topLeft() + QPoint(dx, dy))
            elif self.active_selection_handle == "top_right":
                r.setTopRight(r.topRight() + QPoint(dx, dy))
            elif self.active_selection_handle == "bottom_left":
                r.setBottomLeft(r.bottomLeft() + QPoint(dx, dy))
            elif self.active_selection_handle == "bottom_right":
                r.setBottomRight(r.bottomRight() + QPoint(dx, dy))
            elif self.active_selection_handle == "top":
                r.setTop(r.top() + dy)
            elif self.active_selection_handle == "bottom":
                r.setBottom(r.bottom() + dy)
            elif self.active_selection_handle == "left":
                r.setLeft(r.left() + dx)
            elif self.active_selection_handle == "right":
                r.setRight(r.right() + dx)

            self.selection_rect = r.normalized()
            self.update_toolbar_positions()
            self.update()
            return

        if self.is_moving_selection:
            delta = pos - self.drag_start
            new_r = self.initial_move_rect.translated(delta)
            if new_r.left() >= 0 and new_r.top() >= 0 and new_r.right() < self.width() and new_r.bottom() < self.height():
                self.selection_rect = new_r
                self.update_toolbar_positions()
                self.update()
            return

        if self.is_dragging_annotation and self.selected_annotation:
            delta = pos - self.drag_start
            self.drag_start = pos
            if isinstance(self.selected_annotation, TextItem):
                self.selected_annotation.pos += delta
                self.selected_annotation.calc_rect()
            elif isinstance(self.selected_annotation, StepItem):
                self.selected_annotation.pos += delta
            elif isinstance(self.selected_annotation, ArrowItem):
                self.selected_annotation.start_p += delta
                self.selected_annotation.end_p += delta
            elif isinstance(self.selected_annotation, PathItem):
                self.selected_annotation.points = [p + delta for p in self.selected_annotation.points]
            elif hasattr(self.selected_annotation, "rect"):
                self.selected_annotation.rect.translate(delta)
            self.update()
            return

        if self.is_resizing_annotation and self.selected_annotation and self.active_handle:
            delta = pos - self.drag_start
            if isinstance(self.selected_annotation, ArrowItem):
                if self.active_handle == "start":
                    self.selected_annotation.start_p = pos
                elif self.active_handle == "end":
                    self.selected_annotation.end_p = pos
            elif isinstance(self.selected_annotation, TextItem):
                new_w = max(40, self.initial_annotation_rect.width() + delta.x())
                scale_ratio = new_w / float(max(1, self.initial_annotation_rect.width()))
                new_font_sz = max(10, min(72, int(self.initial_font_size * scale_ratio)))
                self.selected_annotation.font.setPointSize(new_font_sz)
                self.selected_annotation.calc_rect()
            elif hasattr(self.selected_annotation, "rect"):
                r = QRect(self.selected_annotation.rect)
                if self.active_handle == "bottom_right":
                    r.setBottomRight(r.bottomRight() + delta)
                self.selected_annotation.rect = r.normalized()
            self.update()
            return

        if self.is_selecting:
            if self.current_drawing_item:
                draw_rect = QRect(self.drag_start, pos).normalized()
                if isinstance(self.current_drawing_item, ShapeItem):
                    self.current_drawing_item.rect = draw_rect
                elif isinstance(self.current_drawing_item, ArrowItem):
                    self.current_drawing_item.end_p = pos
                elif isinstance(self.current_drawing_item, PathItem):
                    self.current_drawing_item.points.append(pos)
                elif isinstance(self.current_drawing_item, (MosaicItem, BlackoutItem)):
                    self.current_drawing_item.rect = draw_rect
            else:
                self.selection_rect = QRect(self.drag_start, pos).normalized()
            self.update()
        else:
            if not self.selection_rect.isEmpty() and self.current_tool == "select":
                handle = self.get_selection_handle_at(pos)
                if handle in ("top_left", "bottom_right"):
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif handle in ("top_right", "bottom_left"):
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                elif handle in ("top", "bottom"):
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                elif handle in ("left", "right"):
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif self.selection_rect.contains(pos):
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                else:
                    self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = False
            self.is_resizing_selection = False
            self.is_moving_selection = False
            self.is_dragging_annotation = False
            self.is_resizing_annotation = False
            self.active_selection_handle = None
            self.active_handle = None

            if self.current_drawing_item:
                self.annotations.append(self.current_drawing_item)
                self.redo_stack.clear()
                self.selected_annotation = self.current_drawing_item
                self.current_drawing_item = None

            self.update_toolbar_positions()
            self.update()

    def update_marching_ants(self):
        if not self.selection_rect.isEmpty():
            self.dash_offset = (self.dash_offset + 1.0) % 12.0
            self.update()

    def get_selection_handle_at(self, pos: QPoint):
        if self.selection_rect.isEmpty():
            return None
        r = self.selection_rect
        h_size = 12
        handles = {
            "top_left": QRect(r.left() - h_size // 2, r.top() - h_size // 2, h_size, h_size),
            "top_right": QRect(r.right() - h_size // 2, r.top() - h_size // 2, h_size, h_size),
            "bottom_left": QRect(r.left() - h_size // 2, r.bottom() - h_size // 2, h_size, h_size),
            "bottom_right": QRect(r.right() - h_size // 2, r.bottom() - h_size // 2, h_size, h_size),
            "top": QRect(r.center().x() - h_size // 2, r.top() - h_size // 2, h_size, h_size),
            "bottom": QRect(r.center().x() - h_size // 2, r.bottom() - h_size // 2, h_size, h_size),
            "left": QRect(r.left() - h_size // 2, r.center().y() - h_size // 2, h_size, h_size),
            "right": QRect(r.right() - h_size // 2, r.center().y() - h_size // 2, h_size, h_size),
        }
        for handle_name, h_rect in handles.items():
            if h_rect.contains(pos):
                return handle_name
        return None

    def get_annotation_at(self, pos: QPoint):
        for item in reversed(self.annotations):
            if isinstance(item, TextItem):
                if item.get_bounding_rect().adjusted(-6, -6, 6, 6).contains(pos):
                    return item
            elif isinstance(item, StepItem):
                if QRect(item.pos.x() - 14, item.pos.y() - 14, 28, 28).contains(pos):
                    return item
            elif isinstance(item, ArrowItem):
                if QRect(QPoint(min(item.start_p.x(), item.end_p.x()), min(item.start_p.y(), item.end_p.y())),
                         QPoint(max(item.start_p.x(), item.end_p.x()), max(item.start_p.y(), item.end_p.y()))).adjusted(-8, -8, 8, 8).contains(pos):
                    return item
            elif hasattr(item, "rect") and item.rect.contains(pos):
                return item
        return None

    def get_handle_at(self, pos: QPoint, item: AnnotationItem):
        if isinstance(item, ArrowItem):
            if QRect(item.start_p.x() - 6, item.start_p.y() - 6, 12, 12).contains(pos):
                return "start"
            if QRect(item.end_p.x() - 6, item.end_p.y() - 6, 12, 12).contains(pos):
                return "end"
        elif isinstance(item, TextItem):
            r = item.get_bounding_rect()
            if QRect(r.right() - 8, r.bottom() - 8, 16, 16).contains(pos):
                return "bottom_right"
        elif hasattr(item, "rect"):
            r = item.rect
            if QRect(r.right() - 6, r.bottom() - 6, 12, 12).contains(pos):
                return "bottom_right"
        return None

    def undo(self):
        self.commit_inline_text()
        if self.annotations:
            self.redo_stack.append(self.annotations.pop())
            self.selected_annotation = None
            self.update()

    def redo(self):
        self.commit_inline_text()
        if self.redo_stack:
            self.annotations.append(self.redo_stack.pop())
            self.selected_annotation = None
            self.update()

    def delete_selected_annotation(self):
        self.commit_inline_text()
        if self.selected_annotation in self.annotations:
            self.annotations.remove(self.selected_annotation)
            self.redo_stack.append(self.selected_annotation)
            self.selected_annotation = None
            self.update()

    def add_timestamp_stamp(self):
        if self.selection_rect.isEmpty():
            QMessageBox.information(self, "Timestamp", "Please select a screen area first!")
            return
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        font = QFont(self.current_font_family, 11, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        br = fm.boundingRect(now_str)
        item_w = br.width() + 24
        item_h = max(br.height() + 16, 28)
        pos = calc_position_from_setting("Bottom-Left", item_w, item_h, self.selection_rect)
        stamp = TimestampItem(pos, now_str, font, QColor("#3B82F6"))
        self.annotations.append(stamp)
        self.selected_annotation = stamp
        self.update()

    def add_text_watermark_stamp(self):
        if self.selection_rect.isEmpty():
            QMessageBox.information(self, "Watermark", "Please select a screen area first!")
            return
        txt = self.watermark_settings.text if self.watermark_settings.text else "ZCAPTURE WATERMARK"
        font = QFont(self.watermark_settings.font_family or self.current_font_family, self.watermark_settings.font_size or 14, QFont.Weight.Bold)
        metrics = QFontMetrics(font)
        br = metrics.boundingRect(txt)
        pad = 12
        item_w = br.width() + pad * 2
        item_h = max(br.height() + pad * 2, 32)
        pos = calc_position_from_setting(self.watermark_settings.position, item_w, item_h, self.selection_rect)
        wm = WatermarkItem(pos, txt, font, QColor(self.watermark_settings.color), opacity=self.watermark_settings.opacity)
        self.annotations.append(wm)
        self.selected_annotation = wm
        self.update()

    def add_logo_watermark_stamp(self):
        if self.selection_rect.isEmpty():
            QMessageBox.information(self, "Watermark Logo", "Please select a screen area first!")
            return
        logo_path = self.watermark_settings.logo_path
        if not logo_path or not os.path.exists(logo_path):
            QMessageBox.warning(self, "Logo Missing", "Watermark logo image not configured or not found!")
            return
        pm = QPixmap(logo_path)
        if pm.isNull():
            return
        max_w = min(180, max(40, int(self.selection_rect.width() * 0.25)))
        max_h = min(120, max(30, int(self.selection_rect.height() * 0.25)))
        scaled_pm = pm.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pos = calc_position_from_setting(self.watermark_settings.position, scaled_pm.width(), scaled_pm.height(), self.selection_rect)
        logo_item = WatermarkLogoItem(pos, scaled_pm, opacity=self.watermark_settings.opacity)
        self.annotations.append(logo_item)
        self.selected_annotation = logo_item
        self.update()

    def apply_mosaic(self, painter: QPainter, r: QRect):
        if r.isEmpty() or r.width() < 4 or r.height() < 4:
            return
        block_size = 12
        scale_x = self.full_pixmap.width() / float(max(1, self.width()))
        scale_y = self.full_pixmap.height() / float(max(1, self.height()))

        phys_crop = QRect(int(r.x() * scale_x), int(r.y() * scale_y), int(r.width() * scale_x), int(r.height() * scale_y))
        cropped = self.full_pixmap.copy(phys_crop)
        small = cropped.scaled(max(1, phys_crop.width() // block_size), max(1, phys_crop.height() // block_size), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
        pixelated = small.scaled(phys_crop.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)

        painter.save()
        painter.setClipRect(r)
        painter.drawPixmap(r, pixelated)
        painter.restore()

    def apply_blackout(self, painter: QPainter, r: QRect):
        if r.isEmpty():
            return
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(16, 16, 22)))
        painter.drawRect(r)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRect(self.rect())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.drawPixmap(self.rect(), self.full_pixmap)

        w, h = self.width(), self.height()
        dim_pct = max(0, min(100, self.config_data.get("dim_opacity", 50)))
        dim_alpha = int(255 * (dim_pct / 100.0) * 0.7)
        dim_color = QColor(255, 255, 255, dim_alpha)

        if not self.selection_rect.isEmpty():
            r = self.selection_rect
            r_top = max(0, min(h, r.top()))
            r_bottom = max(0, min(h - 1, r.bottom()))
            r_left = max(0, min(w, r.left()))
            r_right = max(0, min(w - 1, r.right()))

            painter.fillRect(0, 0, w, r_top, dim_color)
            painter.fillRect(0, r_bottom + 1, w, h - (r_bottom + 1), dim_color)
            painter.fillRect(0, r_top, r_left, (r_bottom - r_top + 1), dim_color)
            painter.fillRect(r_right + 1, r_top, w - (r_right + 1), (r_bottom - r_top + 1), dim_color)

            dash_pen = QPen(QColor("#0068FF"), 1.5, Qt.PenStyle.DashLine)
            dash_pen.setDashOffset(self.dash_offset)
            painter.setPen(dash_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r)

            draw_dimension_badge(painter, r, w, h)
            self.draw_selection_handles(painter, r)
        else:
            painter.fillRect(0, 0, w, h, dim_color)

        for item in self.annotations:
            if isinstance(item, MosaicItem) and not item.rect.isEmpty():
                self.apply_mosaic(painter, item.rect)
            elif isinstance(item, BlackoutItem) and not item.rect.isEmpty():
                self.apply_blackout(painter, item.rect)

        for item in self.annotations:
            if getattr(self, "editing_target_item", None) == item:
                continue
            draw_annotation_item(painter, item, self.selected_annotation, self.current_drawing_item)

        if self.current_drawing_item:
            draw_annotation_item(painter, self.current_drawing_item, self.selected_annotation, self.current_drawing_item)

        if self.selected_annotation and hasattr(self.selected_annotation, "rect"):
            r = self.selected_annotation.rect
            painter.setPen(QPen(QColor(0, 104, 255), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r)
            cr = 4
            painter.setBrush(QBrush(QColor("#3B82F6")))
            painter.drawEllipse(QPoint(r.right(), r.bottom()), cr, cr)

        if self.config_data.get("show_magnifier", True):
            if self.is_selecting or self.is_resizing_selection or self.is_moving_selection:
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                draw_magnifier_loupe(painter, cursor_pos, self.full_pixmap, self.cached_image, w, h)

    def draw_selection_handles(self, painter: QPainter, r: QRect):
        cr = 4
        handle_centers = [
            r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight(),
            QPoint(r.center().x(), r.top()), QPoint(r.center().x(), r.bottom()),
            QPoint(r.left(), r.center().y()), QPoint(r.right(), r.center().y())
        ]
        for center in handle_centers:
            cx = max(cr + 2, min(self.width() - cr - 2, center.x()))
            cy = max(cr + 2, min(self.height() - cr - 2, center.y()))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 35)))
            painter.drawEllipse(QPoint(cx, cy + 1), cr + 1, cr + 1)
            painter.setPen(QPen(QColor("#3B82F6"), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QPoint(cx, cy), cr, cr)

    def get_processed_cropped_pixmap(self) -> QPixmap:
        self.commit_inline_text()
        if self.selection_rect.isEmpty():
            return QPixmap()

        scale_x = self.full_pixmap.width() / float(max(1, self.width()))
        scale_y = self.full_pixmap.height() / float(max(1, self.height()))

        r = self.selection_rect
        phys_crop = QRect(
            int(r.x() * scale_x),
            int(r.y() * scale_y),
            int(r.width() * scale_x),
            int(r.height() * scale_y)
        )

        cropped = self.full_pixmap.copy(phys_crop)
        cropped.setDevicePixelRatio(1.0)

        painter = QPainter(cropped)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.scale(scale_x, scale_y)
        painter.translate(-r.topLeft())

        for item in self.annotations:
            if isinstance(item, MosaicItem) and not item.rect.isEmpty():
                self.apply_mosaic(painter, item.rect)
            elif isinstance(item, BlackoutItem) and not item.rect.isEmpty():
                self.apply_blackout(painter, item.rect)

        for item in self.annotations:
            if isinstance(item, (MosaicItem, BlackoutItem)):
                continue
            draw_annotation_item(painter, item)

        painter.end()

        if self.config_data.get("auto_timestamp", False):
            cropped = apply_timestamp(cropped)

        if self.watermark_settings.enabled:
            cropped = apply_watermark(cropped, self.watermark_settings)

        return cropped

    def open_settings_window(self):
        from ui.settings_window import SettingsWindow
        dialog = SettingsWindow(self.watermark_settings, self.config_data, parent=self)
        if dialog.exec():
            self.current_color = QColor(self.config_data.get("default_stroke_color", "#EB3232"))
            self.current_bg_color = QColor(self.config_data.get("default_bg_color", "#161624"))
            self.current_stroke_width = max(1, self.config_data.get("stroke_width", 3))
            self.current_font_family = self.config_data.get("default_font", "Segoe UI")
            self.current_font_size = self.config_data.get("default_font_size", 14)
            self.current_text_bg_mode = self.config_data.get("default_text_bg", "none")
            self.step_counter = max(1, self.config_data.get("step_start_num", 1))

            if self.on_settings_changed:
                self.on_settings_changed()
            self.update()

    def copy_and_close(self):
        pm = self.get_processed_cropped_pixmap()
        if not pm.isNull():
            if self.config_data.get("auto_copy", True):
                cb = QGuiApplication.clipboard()
                cb.setPixmap(pm)

            if self.config_data.get("auto_save_on_copy", False):
                save_dir = self.config_data.get("save_dir", "")
                target_dir = save_dir if save_dir else os.path.expanduser("~/Pictures")
                os.makedirs(target_dir, exist_ok=True)
                pat = self.config_data.get("filename_pattern", "ZCapture_{date}_{time}")
                fn = pat.replace("{date}", time.strftime("%Y%m%d")).replace("{time}", time.strftime("%H%M%S"))
                if not fn.endswith(".png") and not fn.endswith(".jpg"):
                    fn += ".png"
                saved_path = os.path.join(target_dir, fn)
                pm.save(saved_path)

            if self.config_data.get("play_sound", True):
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    pass

        self.close()

    def save_to_file(self):
        pm = self.get_processed_cropped_pixmap()
        if pm.isNull():
            return
        pat = self.config_data.get("filename_pattern", "ZCapture_{date}_{time}")
        auto_name = pat.replace("{date}", time.strftime("%Y%m%d")).replace("{time}", time.strftime("%H%M%S"))
        if not auto_name.endswith(".png") and not auto_name.endswith(".jpg"):
            auto_name += ".png"
        default_dir = self.config_data.get("save_dir", "")
        default_path = os.path.join(default_dir, auto_name) if default_dir else auto_name
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file ảnh", default_path, "PNG Files (*.png);;JPEG Files (*.jpg)")
        if file_path:
            quality = self.config_data.get("image_quality", 95)
            if file_path.lower().endswith((".jpg", ".jpeg")):
                pm.save(file_path, "JPEG", quality)
            else:
                pm.save(file_path)

            if self.config_data.get("play_sound", True):
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    pass

            self.close()

    def pin_image(self):
        pm = self.get_processed_cropped_pixmap()
        if not pm.isNull():
            pin_win = PinnedWindow(
                pm,
                config_data=self.config_data,
            )
            pin_win.show()
        self.close()

    def perform_ocr_extraction(self):
        pm = self.get_processed_cropped_pixmap()
        if pm.isNull():
            QMessageBox.warning(self, "No Selection", "Please select a screen region first!")
            return

        self.ocr_btn.setEnabled(False)
        self.ocr_btn.setText("OCR")

        self._ocr_thread = QThread(self)
        self._ocr_worker = _OCRWorker(pm)
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_thread.started.connect(self._ocr_worker.run)
        self._ocr_worker.finished.connect(self.on_ocr_finished)
        self._ocr_worker.finished.connect(self._ocr_thread.quit)
        self._ocr_worker.finished.connect(self._ocr_worker.deleteLater)
        self._ocr_thread.finished.connect(self._ocr_thread.deleteLater)
        self._ocr_thread.start()

    def on_ocr_finished(self, text: str):
        try:
            self.ocr_btn.setEnabled(True)
            self.ocr_btn.setText("OCR")
        except RuntimeError:
            return

        if not text:
            QMessageBox.information(self, "OCR Result", "No text was detected in the selected region.")
            return

        QGuiApplication.clipboard().setText(text)
        from ui.ocr_dialog import OCRResultDialog
        dialog = OCRResultDialog(text, parent=self)
        dialog.exec()
