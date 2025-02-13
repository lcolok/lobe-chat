import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, install_dir: str):
        self.install_dir = install_dir
        self.project_config_dir = Path(install_dir) / ".lobe-setup"
        self.project_config_file = self.project_config_dir / "config.json"
        self._ensure_config_dir()
        self.config = self._load_config()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.project_config_dir, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.project_config_file.exists():
            try:
                with open(self.project_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load project config file: {e}")
                return {}
        return {}

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.project_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save project config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save()
