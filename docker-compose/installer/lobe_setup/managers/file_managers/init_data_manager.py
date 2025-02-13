import json
import os
import shutil
import requests
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

class InitDataManager:
    """初始化数据管理器，用于管理 init_data.json 文件"""
    
    def __init__(self, install_dir: str):
        """初始化管理器
        
        Args:
            install_dir: 安装目录
        """
        self.install_dir = install_dir
        # 直接在安装目录根目录使用 init_data.json
        self.init_data_path = os.path.join(install_dir, 'init_data.json')
        # 从主分支获取初始配置
        self.source_url = "https://raw.githubusercontent.com/lobehub/lobe-chat/main/docker-compose/local/init_data.json"
        
    def _ensure_directory_exists(self) -> None:
        """确保目录存在"""
        os.makedirs(os.path.dirname(self.init_data_path), exist_ok=True)
        
    def _download_init_data(self) -> Dict:
        """从 GitHub 下载 init_data.json
        
        Returns:
            Dict: 下载的数据
        """
        try:
            print(f"Downloading init_data.json from {self.source_url}")
            response = requests.get(self.source_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error downloading init_data.json: {e}")
            return {}
            
    def _load_init_data(self) -> Dict:
        """加载 init_data.json 文件
        
        Returns:
            Dict: 加载的数据
        """
        # 如果文件不存在，从网络下载
        if not os.path.exists(self.init_data_path):
            print(f"init_data.json not found at {self.init_data_path}")
            data = self._download_init_data()
            if data:  # 如果下载成功，保存到文件
                self._ensure_directory_exists()
                self._save_init_data(data)
                print(f"Successfully downloaded and saved init_data.json to {self.init_data_path}")
            return data
            
        # 如果文件存在，读取它
        try:
            print(f"Loading existing init_data.json from {self.init_data_path}")
            with open(self.init_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading init_data.json: {e}")
            return {}
            
    def _save_init_data(self, data: Dict) -> None:
        """保存数据到 init_data.json 文件
        
        Args:
            data: 要保存的数据
        """
        try:
            # 确保目录存在
            self._ensure_directory_exists()
            
            print(f"Saving init_data.json to {self.init_data_path}")
            # 保存文件
            with open(self.init_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved init_data.json")
            
            # 删除 local 目录下的 init_data.json（如果存在）
            local_init_data = os.path.join(self.install_dir, 'local', 'init_data.json')
            if os.path.exists(local_init_data):
                try:
                    os.remove(local_init_data)
                    print(f"Removed redundant init_data.json at {local_init_data}")
                except Exception as e:
                    print(f"Warning: Could not remove redundant init_data.json: {e}")
                    
        except Exception as e:
            print(f"Error saving init_data.json: {e}")
            
    def _normalize_url(self, url: str) -> str:
        """标准化 URL，移除末尾的斜杠
        
        Args:
            url: 要标准化的 URL
            
        Returns:
            str: 标准化后的 URL
        """
        return url.rstrip('/')
            
    def update_application_config(self, app_name: str, updates: Dict) -> None:
        """更新应用配置
        
        Args:
            app_name: 应用名称
            updates: 要更新的配置字典
        """
        data = self._load_init_data()
        
        # 查找并更新应用配置
        for app in data.get('applications', []):
            if app.get('name') == app_name:
                app.update(updates)
                break
                
        self._save_init_data(data)
        
    def update_redirect_uris(self, app_name: str, configs: List[Dict[str, str]]) -> None:
        """更新应用的重定向 URI
        
        Args:
            app_name: 应用名称
            configs: 配置列表，每个配置包含 host 和 port，例如：
                    [
                        {'host': 'localhost', 'port': '3210'},
                        {'host': 'example.com', 'port': '3211'}
                    ]
        """
        data = self._load_init_data()
        
        # 确保 applications 列表存在
        if 'applications' not in data:
            data['applications'] = []
            
        # 查找应用
        app_found = False
        for app in data.get('applications', []):
            if app.get('name') == app_name:
                app_found = True
                
                # 创建新的重定向 URI 列表
                redirect_uris = set()
                
                # 添加新的重定向 URI
                for config in configs:
                    host = config['host']
                    port = config['port']
                    
                    # 构建 HTTP URL
                    http_url = self._normalize_url(f"http://{host}:{port}/api/auth/callback/casdoor")
                    redirect_uris.add(http_url)
                    
                    # 如果主机名不是 localhost，也添加 HTTPS URL
                    if host != 'localhost':
                        https_url = self._normalize_url(f"https://{host}:{port}/api/auth/callback/casdoor")
                        redirect_uris.add(https_url)
                
                # 完全替换应用的重定向 URI
                app['redirectUris'] = sorted(list(redirect_uris))
                print(f"Updated redirect URIs for {app_name}: {app['redirectUris']}")
                break
                
        # 如果没有找到应用，创建一个新的
        if not app_found:
            redirect_uris = set()
            for config in configs:
                host = config['host']
                port = config['port']
                http_url = self._normalize_url(f"http://{host}:{port}/api/auth/callback/casdoor")
                redirect_uris.add(http_url)
                if host != 'localhost':
                    https_url = self._normalize_url(f"https://{host}:{port}/api/auth/callback/casdoor")
                    redirect_uris.add(https_url)
                    
            new_app = {
                'name': app_name,
                'redirectUris': sorted(list(redirect_uris))
            }
            data['applications'].append(new_app)
            print(f"Created new application {app_name} with redirect URIs: {new_app['redirectUris']}")
                
        self._save_init_data(data)
        
    def update_casdoor_password(self, new_password: str) -> None:
        """更新所有用户密码和 LDAP 密码
        
        Args:
            new_password: 新密码
        """
        data = self._load_init_data()
        
        # 1. 更新所有用户密码
        users = data.get('users', [])
        updated_users = []
        
        for user in users:
            # 更新所有普通用户的密码
            if user.get('type') == 'normal-user':
                user['password'] = new_password
                updated_users.append(f"{user.get('owner')}/{user.get('name')}")
                
        if updated_users:
            print(f"Updated passwords for users: {', '.join(updated_users)}")
        else:
            print("Warning: No users found to update in init_data.json")
            
        # 2. 更新 LDAP 密码
        ldaps = data.get('ldaps', [])
        ldap_found = False
        
        for ldap in ldaps:
            if ldap.get('owner') == 'built-in' and ldap.get('id') == 'ldap-built-in':
                ldap_found = True
                ldap['password'] = new_password
                print(f"Updated LDAP server password")
                break
                
        if not ldap_found:
            print("Warning: Could not find built-in LDAP server in init_data.json")
            
        self._save_init_data(data)
        
    def get_application_config(self, app_name: str) -> Optional[Dict]:
        """获取应用配置
        
        Args:
            app_name: 应用名称
            
        Returns:
            Optional[Dict]: 应用配置，如果找不到则返回 None
        """
        data = self._load_init_data()
        
        for app in data.get('applications', []):
            if app.get('name') == app_name:
                return app
                
        return None
