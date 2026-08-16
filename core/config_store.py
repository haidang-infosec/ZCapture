import json
import os

from PyQt6.QtGui import QColor

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ZCapture")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_config(config_data: dict, watermark_settings) -> None:
    """Nạp config đã lưu (nếu có) từ %APPDATA%/ZCapture/config.json, ghi đè trực tiếp lên
    config_data / watermark_settings hiện có. Nếu chưa từng lưu, giữ nguyên giá trị mặc định."""
    if not os.path.exists(CONFIG_PATH):
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Config Load Error]: {e}")
        return

    saved_config = data.get("config", {})
    if isinstance(saved_config, dict):
        for key, value in saved_config.items():
            if key in config_data:
                config_data[key] = value

    wm = data.get("watermark")
    if isinstance(wm, dict):
        watermark_settings.enabled = wm.get("enabled", watermark_settings.enabled)
        watermark_settings.text = wm.get("text", watermark_settings.text)
        watermark_settings.font_family = wm.get("font_family", watermark_settings.font_family)
        watermark_settings.font_size = wm.get("font_size", watermark_settings.font_size)
        if "color_rgba" in wm:
            try:
                r, g, b, a = wm["color_rgba"]
                watermark_settings.color = QColor(r, g, b, a)
            except (TypeError, ValueError):
                pass
        watermark_settings.position = wm.get("position", watermark_settings.position)
        watermark_settings.opacity = wm.get("opacity", watermark_settings.opacity)
        watermark_settings.logo_path = wm.get("logo_path", watermark_settings.logo_path)


def save_config(config_data: dict, watermark_settings) -> None:
    """Ghi config_data / watermark_settings hiện tại xuống %APPDATA%/ZCapture/config.json (Atomic write pattern)."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        payload = {
            "config": config_data,
            "watermark": {
                "enabled": watermark_settings.enabled,
                "text": watermark_settings.text,
                "font_family": watermark_settings.font_family,
                "font_size": watermark_settings.font_size,
                "color_rgba": [
                    watermark_settings.color.red(),
                    watermark_settings.color.green(),
                    watermark_settings.color.blue(),
                    watermark_settings.color.alpha(),
                ],
                "position": watermark_settings.position,
                "opacity": watermark_settings.opacity,
                "logo_path": watermark_settings.logo_path,
            },
        }
        tmp_path = CONFIG_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        print(f"[Config Save Error]: {e}")
