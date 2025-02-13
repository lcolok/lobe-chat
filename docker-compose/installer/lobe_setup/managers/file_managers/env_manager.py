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
        
    def update_env_file(self, port_config: Dict[str, int], host: str) -> None:
        """更新 .env 文件中的配置
        
        Args:
            port_config: 端口配置字典
            host: 主机名
        """
        env_path = os.path.join(self.install_dir, '.env')
        if not os.path.exists(env_path):
            env_example_path = os.path.join(self.install_dir, '.env.example')
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
