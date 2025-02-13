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
        
        # 确保凭据已经生成并保存
        self._ensure_credentials()

    def _ensure_credentials(self):
        """确保凭据已经生成并保存"""
        credentials = self.config_manager.load_credentials()
        if not credentials:
            # 生成新的凭据
            credentials = self._generate_credentials()
            # 保存凭据
            self.config_manager.save_credentials(credentials)

    def _generate_credentials(self) -> Dict[str, str]:
        """生成新的凭据
        
        Returns:
            Dict[str, str]: 生成的凭据
        """
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

        return {
            'AUTH_CASDOOR_SECRET': casdoor_secret,
            'MINIO_ROOT_PASSWORD': minio_password,
            'CASDOOR_PASSWORD': casdoor_password,  # 使用相同的密码
            'LOBE_USERNAME': 'user',
            'LOBE_PASSWORD': casdoor_password,  # 使用相同的密码
            'CASDOOR_ADMIN_USER': 'admin',
            'CASDOOR_ADMIN_PASSWORD': casdoor_password,  # 使用相同的密码
            'MINIO_ROOT_USER': 'admin'
        }

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
        # 获取已保存的凭据
        credentials = self.config_manager.load_credentials()
        
        # 更新 init_data.json 中的配置
        try:
            self.init_data_manager.update_casdoor_config(
                password=credentials['CASDOOR_PASSWORD'],
                client_secret=credentials['AUTH_CASDOOR_SECRET'],
                host=self.get_host()
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
        # 获取现有配置
        existing_config = self.config_manager.load_config()
        
        # 1. 获取部署模式
        mode = self._get_mode()
        
        # 2. 获取主机配置
        host = self._get_host_config(mode)
        
        # 3. 获取端口配置
        if mode == 'port':
            port_config = self._get_port_config()
        else:
            port_config = self.port_manager.get_port_config()
        
        # 4. 获取配置值（凭据等）
        config_values = self._get_config_values()
        
        # 5. 更新 docker-compose.yml
        self.docker_compose_manager.update_docker_compose(port_config)
        
        # 6. 更新 .env 文件，使用实际的主机名和端口
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
        
        # 7. 更新 init_data.json 中的重定向 URI
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
        
        # 8. 保存配置（使用增量更新而不是覆盖）
        new_config = {
            'host': host,
            'mode': mode,
            'ports': port_config
        }
        self.config_manager.save_config(new_config)
        
        return host, port_config

    def _get_port_config(self) -> Dict[str, int]:
        """获取端口配置，保持现有端口配置
        
        Returns:
            Dict[str, int]: 端口配置
        """
        # 获取现有端口配置
        existing_config = self.config_manager.load_config()
        existing_ports = existing_config.get('ports', {})
        
        # 默认端口配置
        default_ports = {
            'lobe': 3210,
            'casdoor': 8000,
            'minio': 9000,
            'minio_console': 9001,
            'postgres': 5432
        }
        
        # 使用现有配置或默认值
        port_config = default_ports.copy()
        port_config.update(existing_ports)
        
        # 询问用户确认或修改端口
        questions = []
        for service, default_port in port_config.items():
            questions.append(
                inquirer.Text(
                    service,
                    message=self.i18n.get('ask_port').format(service, default_port),
                    default=str(default_port),
                    validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 65535
                )
            )
        
        answers = inquirer.prompt(questions)
        return {k: int(v) for k, v in answers.items()}

    def _get_mode(self) -> str:
        """获取部署模式
        
        Returns:
            str: 部署模式
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
        
        return mode

    def print_config_report(self):
        """打印配置报告"""
        config = self.config_manager.load_config()
        credentials = config.get('credentials', {})
        
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
