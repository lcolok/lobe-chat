import inquirer
import socket
import os
import secrets
import string
import subprocess
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
        # 首先尝试从配置文件加载凭据
        credentials = self.config_manager.load_credentials()
        if credentials:
            return credentials

        # 如果没有保存的凭据，生成新的
        def generate_key(length: int) -> str:
            try:
                result = subprocess.run(
                    ['openssl', 'rand', '-hex', str(length)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()[:length]
            except subprocess.CalledProcessError:
                return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

        # 生成密码
        casdoor_secret = generate_key(32)
        casdoor_password = generate_key(10)
        minio_password = generate_key(8)

        credentials = {
            'AUTH_CASDOOR_SECRET': casdoor_secret,
            'MINIO_ROOT_PASSWORD': minio_password,
            'CASDOOR_PASSWORD': casdoor_password,
            'LOBE_USERNAME': 'user',
            'LOBE_PASSWORD': casdoor_password,  # 使用相同的密码
            'CASDOOR_ADMIN_USER': 'admin',
            'CASDOOR_ADMIN_PASSWORD': casdoor_password,  # 使用相同的密码
            'MINIO_ROOT_USER': 'admin'
        }

        # 保存凭据到配置文件
        self.config_manager.save_credentials(credentials)

        # 更新 init_data.json 中的配置
        try:
            self.init_data_manager.update_casdoor_config(
                password=casdoor_password,
                client_secret=casdoor_secret,
                host=self.get_host()  # 获取当前主机地址
            )
        except Exception as e:
            print(f"Warning: Failed to update configuration in init_data.json: {e}")

        return credentials

    def get_host(self) -> str:
        """获取当前主机地址
        
        Returns:
            str: 主机地址
        """
        config = self.config_manager.load_config()
        host = config.get('host')
        if not host:
            host = 'localhost:3210'  # 默认值
        return host

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
        if mode == 'local':
            # 本地模式不需要更新重定向 URI
            pass
        elif mode == 'domain':
            # 域名模式：替换 example.com 为实际域名
            self.init_data_manager.update_redirect_uris('lobechat', [{
                'original': 'example.com',
                'host': host
            }])
        else:  # port mode
            # 端口模式：替换 localhost:3210 为实际主机和端口
            self.init_data_manager.update_redirect_uris('lobechat', [{
                'original': 'localhost:3210',
                'host': f"{host}:{port_config['lobe']}"
            }])
        
        # 保存配置
        self.config_manager.set('host', host)
        self.config_manager.set('mode', mode)
        
        return host, port_config

    def print_config_report(self):
        """打印配置报告"""
        credentials = self.config_manager.load_credentials()
        config = self.config_manager.load_config()
        
        print("\n=== 配置报告 ===")
        print(f"主机: {config.get('host', 'localhost')}")
        print(f"模式: {config.get('mode', 'port')}")
        print("\n端口配置:")
        ports = config.get('ports', {})
        for service, port in ports.items():
            print(f"  {service}: {port}")
        
        print("\n凭据信息:")
        print(f"  Lobe Chat 用户名: {credentials.get('LOBE_USERNAME', 'user')}")
        print(f"  Lobe Chat 密码: {credentials.get('LOBE_PASSWORD', '')}")
        print(f"  Casdoor 管理员用户名: {credentials.get('CASDOOR_ADMIN_USER', 'admin')}")
        print(f"  Casdoor 管理员密码: {credentials.get('CASDOOR_ADMIN_PASSWORD', '')}")
        print(f"  MinIO 用户名: {credentials.get('MINIO_ROOT_USER', 'admin')}")
        print(f"  MinIO 密码: {credentials.get('MINIO_ROOT_PASSWORD', '')}")
