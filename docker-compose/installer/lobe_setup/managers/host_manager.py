import inquirer
from typing import Dict, Tuple, Any
from .port_manager import PortManager
import os
import re

class HostManager:
    def __init__(self, config_manager, i18n):
        """初始化主机管理器
        
        Args:
            config_manager: 配置管理器实例
            i18n: 国际化实例
        """
        self.config_manager = config_manager
        self.i18n = i18n
        self.port_manager = PortManager(i18n, config_manager)
        
    def update_env_file(self, port_config: Dict[str, int], host: str) -> None:
        """更新 .env 文件中的端口配置
        
        Args:
            port_config: 端口配置字典
            host: 主机名
        """
        env_path = os.path.join(self.config_manager.install_dir, '.env')
        if not os.path.exists(env_path):
            env_example_path = os.path.join(self.config_manager.install_dir, '.env.example')
            if os.path.exists(env_example_path):
                with open(env_example_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                return
            
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        port_mapping = {
            'LOBE_PORT': port_config['lobe'],
            'CASDOOR_PORT': port_config['casdoor'],
            'MINIO_PORT': port_config['minio'],
        }
        
        # 更新端口和相关 URL
        new_lines = []
        for line in lines:
            # 跳过空行和注释
            if not line.strip() or line.strip().startswith('#'):
                new_lines.append(line)
                continue
                
            # 更新端口
            for env_key, port in port_mapping.items():
                if line.startswith(f'{env_key}='):
                    line = f'{env_key}={port}\n'
                    break
                    
            # 更新依赖于端口的 URL
            if line.startswith('APP_URL='):
                line = f'APP_URL=http://{host}:{port_config["lobe"]}\n'
            elif line.startswith('AUTH_URL='):
                line = f'AUTH_URL=http://{host}:{port_config["lobe"]}/api/auth\n'
            elif line.startswith('AUTH_CASDOOR_ISSUER='):
                line = f'AUTH_CASDOOR_ISSUER=http://{host}:{port_config["casdoor"]}\n'
            elif line.startswith('S3_PUBLIC_DOMAIN='):
                line = f'S3_PUBLIC_DOMAIN=http://{host}:{port_config["minio"]}\n'
            elif line.startswith('S3_ENDPOINT='):
                line = f'S3_ENDPOINT=http://{host}:{port_config["minio"]}\n'
            elif line.startswith('origin='):
                line = f'origin=http://{host}:{port_config["casdoor"]}\n'
                
            new_lines.append(line)
            
        # 写入更新后的内容
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
    def update_docker_compose(self, port_config: Dict[str, int]) -> None:
        """更新 docker-compose.yml 文件中的端口映射
        
        Args:
            port_config: 端口配置字典
        """
        compose_path = os.path.join(self.config_manager.install_dir, 'docker-compose.yml')
        if not os.path.exists(compose_path):
            return
            
        with open(compose_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 更新 network-service 的端口映射
        network_ports_pattern = r'(network-service:.*?ports:.*?)(.*?)(command:)'
        network_ports_replacement = f"""\\1
      - '{port_config["minio"]}:{port_config["minio"]}' # MinIO API
      - '{port_config["minio_console"]}:9001' # MinIO Console
      - '{port_config["casdoor"]}:{port_config["casdoor"]}' # Casdoor
      - '{port_config["lobe"]}:3210' # LobeChat
    \\3"""
        
        content = re.sub(
            network_ports_pattern,
            network_ports_replacement,
            content,
            flags=re.DOTALL
        )
        
        # 更新 postgresql 的端口映射
        postgres_ports_pattern = r'(postgresql:.*?ports:.*?)(.*?)(volumes:)'
        postgres_ports_replacement = f"""\\1
      - '{port_config["postgres"]}:5432'
    \\3"""
        
        content = re.sub(
            postgres_ports_pattern,
            postgres_ports_replacement,
            content,
            flags=re.DOTALL
        )
        
        # 写入更新后的内容
        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def configure_host(self) -> Tuple[str, Dict[str, int]]:
        """配置主机设置
        
        Returns:
            Tuple[str, Dict[str, int]]: 主机配置，包含 (host, port_config)
        """
        # 选择部署模式
        questions = [
            inquirer.List('mode',
                         message=self.i18n.get('ask_mode'),
                         choices=[
                             ('本地模式（localhost）', 'localhost'),
                             ('端口模式（自定义端口）', 'port'),
                             ('域名模式（自定义域名）', 'domain')
                         ])
        ]
        
        mode = inquirer.prompt(questions)['mode']
        
        # 根据模式设置主机名
        if mode == 'localhost':
            host = 'localhost'
        elif mode == 'port':
            host = 'localhost'
        else:  # domain mode
            questions = [
                inquirer.Text('domain',
                             message=self.i18n.get('ask_domain'))
            ]
            host = inquirer.prompt(questions)['domain']
            
        # 配置端口
        port_config = self.port_manager.configure_ports()
        
        # 更新配置文件
        self.update_env_file(port_config, host)
        self.update_docker_compose(port_config)
        
        # 保存配置
        self.config_manager.set('host', host)
        self.config_manager.set('mode', mode)
        
        return host, port_config
