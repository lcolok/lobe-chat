import os
from typing import Dict

class EnvManager:
    """环境变量文件管理器"""
    
    def __init__(self, install_dir: str):
        """初始化环境变量文件管理器
        
        Args:
            install_dir: 安装目录
        """
        self.install_dir = install_dir
        
    def update_env_file(self, port_config: Dict[str, int], host: str, config_values: Dict[str, str]) -> None:
        """从 .env.example 创建新的 .env 文件
        
        Args:
            port_config: 端口配置字典
            host: 主机名
            config_values: 配置值字典，包含如 AUTH_CASDOOR_SECRET, MINIO_ROOT_PASSWORD 等需要替换的值
        """
        env_example_path = os.path.join(self.install_dir, '.env.example')
        env_path = os.path.join(self.install_dir, '.env')
        
        if not os.path.exists(env_example_path):
            print(f"Error: {env_example_path} not found")
            return
            
        # 读取 .env.example 文件
        with open(env_example_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        port_mapping = {
            'LOBE_PORT': port_config['lobe'],
            'CASDOOR_PORT': port_config['casdoor'],
            'MINIO_PORT': port_config['minio'],
        }
        
        # 处理每一行并创建新的配置
        new_lines = []
        section = None  # 用于跟踪当前配置部分
        
        for line in lines:
            # 检测配置部分
            if line.strip().startswith('# ===== 预设配置 ====='):
                section = 'preset'
            elif line.strip().startswith('# Postgres'):
                section = 'postgres'
            elif line.strip().startswith('# Casdoor'):
                section = 'casdoor'
                line = '# Casdoor secret\n'  # 修正注释格式
            elif line.strip().startswith('# MinIO'):
                section = 'minio'
            elif line.strip().startswith('# 在下方配置'):
                section = 's3'
            elif line.strip().startswith('# 为 casdoor'):
                section = 'casdoor_extra'
                
            # 跳过我们不想要的配置项
            if any(line.startswith(skip) for skip in [
                'CASDOOR_HOSTNAME=',
                'CASDOOR_ORGANIZATION_NAME=',
                'CASDOOR_APPLICATION_NAME=',
                'NEXTAUTH_URL='
            ]):
                continue
                
            # 更新配置值
            if line.strip() and not line.strip().startswith('#'):
                # 首先检查是否是预定义的配置值
                key = line.split('=')[0].strip()
                if key in config_values:
                    line = f'{key}={config_values[key]}\n'
                # 然后检查 URL 和端口配置
                elif line.startswith('APP_URL='):
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
                else:
                    # 更新端口
                    for env_key, port in port_mapping.items():
                        if line.startswith(f'{env_key}='):
                            line = f'{env_key}={port}\n'
                            break
            
            new_lines.append(line)
            
        # 写入新的 .env 文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
