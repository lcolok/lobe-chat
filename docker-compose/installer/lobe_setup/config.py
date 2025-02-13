import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "lobe-setup"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "language": "en",
            "language_selected": False,
            "last_install_dir": str(Path.home() / "lobe-chat-db"),
            "last_used_time": None
        }
        self._ensure_config_dir()
        self.config = self._load_config()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    return {**self.default_config, **loaded_config}
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
                return dict(self.default_config)
        return dict(self.default_config)

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default if default is not None else self.default_config.get(key))

    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save()
