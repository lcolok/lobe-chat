import json
import os
import shutil
import requests
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse
from i18n import I18n
from console import Console

class InitDataManager:
    """初始化数据管理器，用于管理 init_data.json 文件"""
    
    def __init__(self, install_dir: str, i18n: I18n, console: Console):
        """初始化管理器
        
        Args:
            install_dir: 安装目录
            i18n: 国际化翻译对象
            console: 控制台输出对象
        """
        self.install_dir = install_dir
        self.i18n = i18n
        self.console = console
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
            
    def _load_init_data(self) -> Dict[str, Any]:
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
            self.console.print(f"[red]{self.i18n.get('error_loading_init_data').format(str(e))}[/red]")
            raise
            
    def _save_init_data(self, data: Dict[str, Any]) -> None:
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
        except Exception as e:
            self.console.print(f"[red]{self.i18n.get('error_saving_init_data').format(str(e))}[/red]")
            raise
            
        print(f"Successfully saved init_data.json")
        
        # 删除 local 目录下的 init_data.json（如果存在）
        local_init_data = os.path.join(self.install_dir, 'local', 'init_data.json')
        if os.path.exists(local_init_data):
            try:
                os.remove(local_init_data)
                print(f"Removed redundant init_data.json at {local_init_data}")
            except Exception as e:
                print(f"Warning: Could not remove redundant init_data.json: {e}")
                
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
        
    def update_redirect_uris(self, host: str, port: int) -> None:
        """更新 init_data.json 中的重定向 URI
        
        Args:
            host: 主机地址
            port: 端口号
        """
        try:
            data = self._load_init_data()
            
            # 更新 Casdoor 配置
            casdoor_config = data.get('casdoor', {})
            if casdoor_config:
                redirect_uris = [
                    f"http://{host}:{port}/api/auth/callback/casdoor",
                    "http://localhost:3210/api/auth/callback/casdoor"
                ]
                casdoor_config['redirectUris'] = redirect_uris
                data['casdoor'] = casdoor_config
                
                self._save_init_data(data)
                self.console.print(f"[green]{self.i18n.get('updated_redirect_uris')}[/green]")
        except Exception as e:
            self.console.print(f"[red]{self.i18n.get('error_updating_casdoor_config').format(str(e))}[/red]")
            raise

    def update_casdoor_config(self, password: str, client_secret: str, host: str):
        """更新 Casdoor 配置，包括密码、客户端密钥和回调 URL
        
        Args:
            password: 新密码
            client_secret: 新的客户端密钥
            host: 新的主机地址
        """
        init_data_file = os.path.join(self.install_dir, 'init_data.json')
        
        try:
            with open(init_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. 更新客户端密钥
            if 'applications' in data:
                for app in data['applications']:
                    if app.get('clientSecret') == 'dbf205949d704de81b0b5b3603174e23fbecc354':
                        app['clientSecret'] = client_secret
            
            # 2. 更新所有用户的密码（从 "123" 更新为新密码）
            if 'users' in data:
                for user in data['users']:
                    if user.get('password') == '123':
                        user['password'] = password

            # 3. 更新 LDAP 配置
            if 'ldaps' in data:
                for ldap in data['ldaps']:
                    if ldap.get('id') == 'ldap-built-in' and ldap.get('owner') == 'built-in':
                        ldap['password'] = password
                        ldap['host'] = host.split(':')[0]  # 只使用主机名部分
            
            # 4. 更新回调 URL
            if 'applications' in data:
                for app in data['applications']:
                    if 'redirectUris' in app:
                        app['redirectUris'] = [uri.replace('example.com', host) for uri in app['redirectUris']]
            
            # 保存更新后的数据
            with open(init_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.console.print(f"[red]{self.i18n.get('error_updating_casdoor_config').format(str(e))}[/red]")
            raise

    def update_casdoor_password(self, new_password: str):
        """更新 Casdoor 密码（保留此方法以保持向后兼容）
        
        Args:
            new_password: 新密码
        """
        self.update_casdoor_config(
            password=new_password,
            client_secret='dbf205949d704de81b0b5b3603174e23fbecc354',  # 保持原值
            host='example.com'  # 保持原值
        )

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
