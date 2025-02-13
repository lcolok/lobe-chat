import json
import os
import secrets
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
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving project config file: {e}")

    def save_preset_credentials(self, credentials: Dict[str, str]):
        """保存预设的凭据信息
        
        Args:
            credentials: 包含用户名和密码的字典
        """
        self.config['preset_credentials'] = credentials
        self.save()

    def get_preset_credentials(self) -> Dict[str, str]:
        """获取预设的凭据信息
        
        Returns:
            Dict[str, str]: 预设的凭据信息
        """
        return self.config.get('preset_credentials', {})

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save()

    def _generate_secret(self, length: int = 32) -> str:
        """生成指定长度的随机密钥
        
        Args:
            length: 密钥长度，默认为 32 个字符
            
        Returns:
            str: 生成的密钥
        """
        return secrets.token_hex(length // 2)

    def get_generated_value(self, key: str) -> str:
        """获取或生成配置值。如果值不存在，则生成新的值并保存。
        
        Args:
            key: 配置键名
            
        Returns:
            str: 配置值
        """
        # 如果值已存在，直接返回
        value = self.get(key)
        if value:
            return value
            
        # 根据不同的键生成不同的值
        if key == 'auth_casdoor_secret':
            # Casdoor secret 需要 32 个字符
            value = self._generate_secret(32)
        elif key == 'minio_root_password':
            # MinIO 密码使用 8 个字符
            value = self._generate_secret(8)
        else:
            # 默认生成 16 个字符的密钥
            value = self._generate_secret(16)
            
        # 保存生成的值
        self.set(key, value)
        return value

    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """递归合并两个字典
        
        Args:
            dict1: 基础字典
            dict2: 要合并的字典（优先级更高）
            
        Returns:
            Dict: 合并后的字典
        """
        merged = dict1.copy()
        
        for key, value in dict2.items():
            if (
                key in merged and 
                isinstance(merged[key], dict) and 
                isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
                
        return merged

    def save_config(self, config: Dict[str, Any]):
        """保存配置到文件，使用递归合并保持现有配置
        
        Args:
            config: 要保存的新配置
        """
        config_dir = os.path.join(self.install_dir, '.lobe-setup')
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, 'config.json')
        try:
            # 读取现有配置
            existing_config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            
            # 递归合并配置
            merged_config = self._deep_merge(existing_config, config)
                
            # 保存合并后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {config_file}: {e}")
            raise

    def save_credentials(self, credentials: Dict[str, str]):
        """保存凭据信息，确保不覆盖其他配置
        
        Args:
            credentials: 凭据字典，包含各种密码和密钥
        """
        # 只更新 credentials 部分
        self.save_config({'credentials': credentials})

    def load_config(self) -> Dict[str, Any]:
        """从文件加载配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config_file = os.path.join(self.install_dir, '.lobe-setup', 'config.json')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config from {config_file}: {e}")
        return {}

    def load_credentials(self) -> Dict[str, str]:
        """加载凭据信息
        
        Returns:
            Dict[str, str]: 凭据字典
        """
        config = self.load_config()
        return config.get('credentials', {})
