# config_manager.py
import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "region": [100, 200, 800, 600],
    "save_folder": os.path.join(os.getcwd(), "map_screenshots"),
    "dpi": 300,
    "png_compress_level": 1,
    "current_row": 1,
    "key_right_presses": 5,
    "key_down_presses": 5,
    "auto_cols": 10,
    "auto_rows": 10,
    "auto_delay": 1.5,
    "rows_per_block": 10
}

def load_config():
    """設定ファイルを読み込み、デフォルト値とマージして返す"""
    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)
        config.update(loaded_config)
    except FileNotFoundError:
        pass  # ファイルがない場合はデフォルト設定を使用
    return config

def save_config(config):
    """現在の設定をファイルに保存する"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)