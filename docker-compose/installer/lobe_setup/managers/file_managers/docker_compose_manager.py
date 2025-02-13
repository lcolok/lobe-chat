import os
import re
import shutil
from typing import Dict, List, Tuple
import requests

class DockerComposeManager:
    """Docker Compose 文件管理器"""
    
    def __init__(self, install_dir: str):
        """初始化 Docker Compose 文件管理器
        
        Args:
            install_dir: 安装目录
        """
        self.install_dir = install_dir
        
    def _update_network_service_ports(self, content: str, port_config: Dict[str, int]) -> str:
        """更新 network-service 的端口映射
        
        Args:
            content: docker-compose.yml 的内容
            port_config: 端口配置字典
            
        Returns:
            str: 更新后的内容
        """
        # 使用环境变量的端口映射格式
        ports = [
            ("${MINIO_PORT}:${MINIO_PORT}", "MinIO API"),
            ("9001:9001", "MinIO Console"),
            ("${CASDOOR_PORT}:8000", "Casdoor"),
            ("${LOBE_PORT}:3210", "LobeChat")
        ]
        
        ports_section = "\n".join([
            f"      - '{mapping}' # {comment}"
            for mapping, comment in ports
        ])
        
        pattern = r'(network-service:.*?ports:.*?)(.*?)(command:)'
        replacement = f"\\1\n{ports_section}\n    \\3"
        
        return re.sub(pattern, replacement, content, flags=re.DOTALL)
        
    def _remove_service_ports(self, content: str, service_names: List[str]) -> str:
        """移除指定服务的端口映射
        
        Args:
            content: docker-compose.yml 的内容
            service_names: 服务名称列表
            
        Returns:
            str: 更新后的内容
        """
        for service in service_names:
            # 匹配 ports: 部分直到下一个顶级配置项
            pattern = f'({service}:.*?)(ports:.*?)(volumes:|environment:|command:|healthcheck:|restart:|networks:)'
            replacement = r'\1\3'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
        return content
        
    def _backup_original_file(self) -> None:
        """将原始的 docker-compose.yml 备份为 docker-compose.yml.example"""
        compose_path = os.path.join(self.install_dir, 'docker-compose.yml')
        example_path = os.path.join(self.install_dir, 'docker-compose.yml.example')
        
        if os.path.exists(compose_path) and not os.path.exists(example_path):
            shutil.copy2(compose_path, example_path)
        
    def _download_file(self, url: str, target_path: str) -> None:
        """从 URL 下载文件
        
        Args:
            url: 文件的 URL
            target_path: 目标文件路径
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 写入文件
            with open(target_path, 'wb') as f:
                f.write(response.content)
                
        except Exception as e:
            print(f"Error downloading file from {url}: {e}")
            raise
            
    def download_files(self) -> None:
        """下载所需的文件"""
        # 下载 docker-compose.yml
        self._download_file(
            'https://raw.githubusercontent.com/lobehub/lobe-chat/main/docker-compose/docker-compose.yml',
            os.path.join(self.install_dir, 'docker-compose.yml')
        )
        
        # 下载 .env.example
        self._download_file(
            'https://raw.githubusercontent.com/lobehub/lobe-chat/main/docker-compose/local/.env.example',
            os.path.join(self.install_dir, '.env.example')
        )
        
        # 保存一份 docker-compose.yml.example
        shutil.copy2(os.path.join(self.install_dir, 'docker-compose.yml'), os.path.join(self.install_dir, 'docker-compose.yml.example'))
        
    def update_docker_compose(self, port_config: Dict[str, int]) -> None:
        """更新 docker-compose.yml 文件中的端口映射
        
        Args:
            port_config: 端口配置字典
        """
        compose_path = os.path.join(self.install_dir, 'docker-compose.yml')
        if not os.path.exists(compose_path):
            return
            
        # 在修改之前先备份原始文件
        self._backup_original_file()
            
        # 读取文件内容
        with open(compose_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. 更新 network-service 的端口映射（这些是需要对外暴露的端口）
        content = self._update_network_service_ports(content, port_config)
        
        # 2. 移除其他服务的端口映射，因为它们只需要容器间通信
        services_to_remove_ports = ['postgresql', 'minio', 'casdoor']
        content = self._remove_service_ports(content, services_to_remove_ports)
        
        # 写入更新后的内容
        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(content)
