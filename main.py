import os
import sys
import threading
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox,
    QWidget, QHBoxLayout, QLabel, QWidgetAction
)

from core.dpi_utils import enable_hidpi_awareness
from core.screen_grabber import capture_full_desktop
from core.config_store import load_config, save_config
from models.watermark import WatermarkSettings
from ui.overlay_canvas import ScreenOverlayCanvas
from ui.settings_window import SettingsWindow
from ui.toolbars import create_camera_icon, create_settings_icon, create_info_icon, create_power_icon

class CaptureSignalTrigger(QObject):
    trigger_capture = pyqtSignal()


class _TrayMenuRow(QWidget):
    """1 dòng trong Tray Menu Light Theme: icon 16px + label + shortcut (nếu có), hover #F4F4F5."""
    def __init__(self, menu: QMenu, icon: QIcon, label: str, callback, shortcut_text: str = None, danger: bool = False):
        super().__init__()
        self._menu = menu
        self._callback = callback
        self._hover_bg = "#FEE2E2" if danger else "#F4F4F5"
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setPixmap(icon.pixmap(QSize(16, 16)))
        layout.addWidget(icon_lbl)

        text_color = "#DC2626" if danger else "#27272A"
        text_lbl = QLabel(label)
        text_lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent;")
        layout.addWidget(text_lbl)

        layout.addStretch()

        self.shortcut_lbl = None
        if shortcut_text:
            self.shortcut_lbl = QLabel(shortcut_text)
            self.shortcut_lbl.setStyleSheet(
                "color: #A1A1AA; font-size: 12px; font-family: Consolas, monospace; background: transparent;"
            )
            layout.addWidget(self.shortcut_lbl)

    def update_shortcut(self, text: str):
        if self.shortcut_lbl:
            self.shortcut_lbl.setText(text)

    def enterEvent(self, event):
        self.setStyleSheet(f"background-color: {self._hover_bg}; border-radius: 8px;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._menu.close()
            if self._callback:
                self._callback()
        super().mousePressEvent(event)

class ZCaptureApp:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.watermark_settings = WatermarkSettings()
        self.config_data = {
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

        # Nạp cấu hình đã lưu từ lần chạy trước (nếu có), ghi đè lên giá trị mặc định ở trên
        load_config(self.config_data, self.watermark_settings)

        self.overlay_window = None
        self.hotkey_listener = None

        # Signal bridge for global hotkey
        self.signal_bridge = CaptureSignalTrigger()
        self.signal_bridge.trigger_capture.connect(self.start_capture)

        self.init_tray()
        self.init_hotkey()

    def create_tray_icon_pixmap(self) -> QIcon:
        """Create high-definition ZCapture camera icon for System Tray."""
        pm = QPixmap(32, 32)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw camera body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 120, 215)) # Windows Accent Blue
        painter.drawRoundedRect(4, 8, 24, 18, 4, 4)

        # Lens
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(12, 13, 8, 8)
        painter.setBrush(QColor(0, 120, 215))
        painter.drawEllipse(14, 15, 4, 4)

        painter.end()
        return QIcon(pm)

    def _add_tray_row(self, icon, label, callback, shortcut_text=None, danger=False):
        row = _TrayMenuRow(self.tray_menu, icon, label, callback, shortcut_text, danger)
        action = QWidgetAction(self.tray_menu)
        action.setDefaultWidget(row)
        self.tray_menu.addAction(action)
        return row

    def init_tray(self):
        self.tray = QSystemTrayIcon(self.create_tray_icon_pixmap(), self.qapp)
        self.update_tray_tooltip()

        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 6px;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(0,0,0,0.06);
                margin: 4px 8px;
            }
        """)

        # Nhóm 1: Capture Screen — action chính, dùng nhiều nhất
        self.capture_row = self._add_tray_row(
            create_camera_icon(), "Capture Screen", self.start_capture,
            shortcut_text=self.config_data.get("hotkey", "Ctrl+Shift+S")
        )

        self.tray_menu.addSeparator()

        # Nhóm 2: Settings (Options & Settings gộp chung vì cùng 1 chức năng duy nhất)
        self._add_tray_row(create_settings_icon(), "Settings", self.open_settings)

        self.tray_menu.addSeparator()

        # Nhóm 3: About
        self._add_tray_row(create_info_icon(), "About ZCapture", self.show_about)

        self.tray_menu.addSeparator()

        # Nhóm 4: Exit — cảnh báo màu đỏ
        self._add_tray_row(create_power_icon(), "Exit ZCapture", self.qapp.quit, danger=True)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def update_tray_tooltip(self):
        hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        self.tray.setToolTip(f"ZCapture by ZCS-Labs ({hk})")

    def apply_windows_autostart(self):
        """Enable or disable Windows startup registry key based on config."""
        enable = self.config_data.get("start_with_windows", False)
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            app_name = "ZCapture"
            if enable:
                exe_path = f'"{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[Autostart Registry Note]: {e}")

    def on_tray_activated(self, reason):
        single_click = self.config_data.get("single_click_tray", True)
        if single_click and reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.start_capture()
        elif not single_click and reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.start_capture()

    def format_pynput_hotkey(self, hk_str: str) -> str:
        """Chuyển đổi tên phím tắt sang chuẩn format pynput (Hỗ trợ F1-F12, PrintScreen, Ctrl, Alt...)."""
        if not hk_str:
            return "<ctrl>+<shift>+s"
        parts = hk_str.replace("Meta", "Cmd").replace("Control", "Ctrl").lower().split("+")
        formatted = []
        for p in parts:
            p = p.strip()
            if p in ("ctrl", "control"):
                formatted.append("<ctrl>")
            elif p in ("shift",):
                formatted.append("<shift>")
            elif p in ("alt",):
                formatted.append("<alt>")
            elif p in ("cmd", "meta", "win"):
                formatted.append("<cmd>")
            elif p.startswith("f") and p[1:].isdigit():  # Function keys F1-F12
                formatted.append(f"<{p}>")
            elif p in ("printscreen", "prtsc", "prtscr"):
                formatted.append("<print_screen>")
            elif p in ("space", "enter", "tab", "esc", "backspace", "delete"):
                formatted.append(f"<{p}>")
            else:
                formatted.append(p)
        return "+".join(formatted)

    def init_hotkey(self):
        """Lắng nghe phím tắt toàn cục động (Dừng listener cũ trước khi bind listener mới)."""
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None

        raw_hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        print(f"[Hotkey] Re-binding hotkey to: {raw_hk}")

        def run_hotkey_listener():
            try:
                from pynput import keyboard
                hk_pattern = self.format_pynput_hotkey(raw_hk)
                
                def on_activate():
                    print(f"[Hotkey] Triggered: {raw_hk}")
                    self.signal_bridge.trigger_capture.emit()

                with keyboard.GlobalHotKeys({hk_pattern: on_activate}) as h:
                    self.hotkey_listener = h
                    h.join()
            except Exception as e:
                print(f"[Hotkey Note] {raw_hk}: {e}")

        hotkey_thread = threading.Thread(target=run_hotkey_listener, daemon=True)
        hotkey_thread.start()

    def start_capture(self):
        """Bắt đầu tiến trình chụp màn hình (Multi-Monitor Aware & Safe Lifetime)."""
        try:
            if self.overlay_window and self.overlay_window.isVisible():
                return
        except (RuntimeError, AttributeError):
            self.overlay_window = None

        # Chụp toàn màn hình (hỗ trợ đa màn hình hoàn hảo)
        include_cursor = self.config_data.get("include_cursor", False)
        full_screen_pm, virtual_rect = capture_full_desktop(include_cursor=include_cursor)
        if full_screen_pm.isNull():
            QMessageBox.critical(None, "Error", "Failed to capture screen snapshot!")
            return

        self.overlay_window = ScreenOverlayCanvas(
            full_screen_pm, virtual_rect, self.watermark_settings, self.config_data,
            on_settings_changed=self.on_settings_updated
        )
        self.overlay_window.show()
        self.overlay_window.activateWindow()

    def on_settings_updated(self):
        """Callback executed when settings are saved."""
        hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        self.capture_row.update_shortcut(hk)
        self.update_tray_tooltip()
        self.apply_windows_autostart()
        self.init_hotkey()
        save_config(self.config_data, self.watermark_settings)

    def open_settings(self):
        dialog = SettingsWindow(self.watermark_settings, self.config_data)
        if dialog.exec():
            self.on_settings_updated()

    def show_about(self):
        from ui.about_dialog import AboutDialog
        hk = self.config_data.get("hotkey", "Ctrl+Shift+S")
        dialog = AboutDialog(hotkey=hk)
        dialog.exec()


def main():
    enable_hidpi_awareness()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    zcapture = ZCaptureApp(app)

    print(f"ZCapture Screen Capture is running! Hotkey: {zcapture.config_data['hotkey']}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
