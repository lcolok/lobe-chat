import inquirer
import socket
import os
import secrets
import string
from typing import Dict, List, Tuple
from .port_manager import PortManager
from .file_managers import EnvManager, DockerComposeManager, InitDataManager

class HostManager:
    def __init__(self, config_manager, i18n):
        """初始化主机配置管理器
        
        Args:
            config_manager: 配置管理器
            i18n: 国际化管理器
        """
        self.config_manager = config_manager
        self.i18n = i18n
        self.port_manager = PortManager(i18n, config_manager)
        
        # 使用配置管理器提供的安装目录
        self.env_manager = EnvManager(config_manager.install_dir)
        self.docker_compose_manager = DockerComposeManager(config_manager.install_dir)
        self.init_data_manager = InitDataManager(config_manager.install_dir)
        
    def _generate_password(self, length: int = 10) -> str:
        """生成随机密码
        
        Args:
            length: 密码长度
            
        Returns:
            str: 生成的密码
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    def _get_host_config(self, mode: str) -> str:
        """获取主机配置
        
        Args:
            mode: 部署模式
            
        Returns:
            str: 主机配置
        """
        if mode == 'local':
            return 'localhost'
            
        # 获取保存的主机名或询问用户
        questions = [
            inquirer.Text(
                'host',
                message=self.i18n.get('ask_host'),
                validate=lambda _, x: len(x) > 0 and x != 'localhost',
                default=self.config_manager.get('host') or 'example.com'
            )
        ]
        answers = inquirer.prompt(questions)
        return answers['host']
        
    def _get_config_values(self) -> Dict[str, str]:
        """获取配置值
        
        Returns:
            Dict[str, str]: 配置值字典
        """
        # 生成或获取配置值
        auth_casdoor_secret = self.config_manager.get_generated_value('auth_casdoor_secret')
        minio_root_password = self.config_manager.get_generated_value('minio_root_password')
        
        # 生成 Casdoor 管理员密码
        try:
            casdoor_password = self._generate_password()
            print(f"Generated new user password")
            # 更新 init_data.json 中的密码
            self.init_data_manager.update_casdoor_password(casdoor_password)
        except Exception as e:
            print(f"Warning: Failed to generate user password: {e}")
            casdoor_password = "123"  # 使用默认密码
            
        return {
            'AUTH_CASDOOR_SECRET': auth_casdoor_secret,
            'MINIO_ROOT_PASSWORD': minio_root_password,
            'CASDOOR_PASSWORD': casdoor_password  # 添加 Casdoor 密码到配置中
        }
        
    def configure_host(self) -> Tuple[str, Dict[str, int]]:
        """配置主机
        
        Returns:
            Tuple[str, Dict[str, int]]: 主机名和端口配置
        """
        # 选择部署模式
        questions = [
            inquirer.List('mode',
                         message=self.i18n.get('ask_mode'),
                         choices=[
                             ('本地模式（localhost）', 'local'),
                             ('端口模式（自定义端口）', 'port'),
                             ('域名模式（自定义域名）', 'domain')
                         ])
        ]
        
        mode = inquirer.prompt(questions)['mode']
        
        # 1. 获取主机配置（对于端口模式和域名模式，会询问用户）
        host = self._get_host_config(mode)
        
        # 2. 获取端口配置
        if mode == 'port':
            port_config = self.port_manager.configure_ports()
        else:
            port_config = self.port_manager.get_port_config()
        
        # 3. 获取配置值
        config_values = self._get_config_values()
        
        # 4. 更新 docker-compose.yml
        self.docker_compose_manager.update_docker_compose(port_config)
        
        # 5. 更新 .env 文件，使用实际的主机名和端口
        env_updates = {
            'APP_URL': f"http://{host}:{port_config['lobe']}",
            'AUTH_URL': f"http://{host}:{port_config['lobe']}/api/auth",
            'AUTH_CASDOOR_ISSUER': f"http://{host}:{port_config['casdoor']}",
            'S3_PUBLIC_DOMAIN': f"http://{host}:{port_config['minio']}",
            'S3_ENDPOINT': f"http://{host}:{port_config['minio']}",
            'origin': f"http://{host}:{port_config['casdoor']}"
        }
        config_values.update(env_updates)
        self.env_manager.update_env_file(port_config, host, config_values)
        
        # 6. 更新 init_data.json 中的重定向 URI
        redirect_configs = []
        
        # 添加主域名配置
        redirect_configs.append({
            'host': host,
            'port': str(port_config['lobe'])
        })
        
        # 如果是端口模式，也添加 localhost 配置用于本地开发
        if mode == 'port':
            redirect_configs.append({
                'host': 'localhost',
                'port': str(port_config['lobe'])
            })
            
        self.init_data_manager.update_redirect_uris('lobechat', redirect_configs)
        
        # 保存配置
        self.config_manager.set('host', host)
        self.config_manager.set('mode', mode)
        
        return host, port_config
