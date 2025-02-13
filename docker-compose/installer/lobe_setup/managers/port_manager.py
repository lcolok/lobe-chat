import socket
from typing import List, Tuple, Optional, Set
import inquirer
import psutil

class PortManager:
    def __init__(self, i18n, config_manager):
        """初始化端口管理器
        
        Args:
            i18n: 国际化实例
            config_manager: 配置管理器实例
        """
        self.i18n = i18n
        self.config_manager = config_manager
        self.default_ports = {
            'lobe': 3210,
            'casdoor': 7001,
            'minio': 9000,
            'minio_console': 9001,
            'postgres': 5432,
        }
        self.used_ports: Set[int] = set()  # 记录已分配的端口
        
    def get_used_ports(self) -> List[int]:
        """获取系统当前使用的所有端口"""
        used_ports = set()
        
        # 获取所有网络连接
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN':
                used_ports.add(conn.laddr.port)
                
        return sorted(list(used_ports))
        
    def is_port_available(self, port: int) -> bool:
        """检查指定端口是否可用
        
        Args:
            port: 要检查的端口号
            
        Returns:
            bool: 端口是否可用
        """
        # 检查是否已被其他服务使用
        if port in self.used_ports:
            return False
            
        try:
            # 尝试绑定端口
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)  # 设置超时时间为1秒
                result = s.connect_ex(('127.0.0.1', port))
                return result != 0  # 如果连接失败（端口未被使用），返回 True
        except (socket.error, OSError):
            return False
            
    def find_next_available_port(self, start_port: int) -> int:
        """从指定端口开始查找下一个可用端口
        
        Args:
            start_port: 起始端口号
            
        Returns:
            int: 找到的可用端口号
        """
        port = start_port
        while not self.is_port_available(port):
            port += 1
            if port > 65535:  # 防止无限循环
                raise ValueError(f"No available ports found after {start_port}")
        return port
        
    def prompt_for_port(self, service: str, default_port: int) -> int:
        """提示用户输入端口号
        
        Args:
            service: 服务名称
            default_port: 默认端口号
            
        Returns:
            int: 用户选择的端口号
        """
        while True:
            questions = [
                inquirer.Text(
                    'port',
                    message=self.i18n.get('ask_port').format(
                        service=service,
                        port=default_port
                    ),
                    default=str(default_port),
                    validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 65535
                )
            ]
            
            answers = inquirer.prompt(questions)
            port = int(answers['port'])
            
            # 检查端口是否已被其他服务使用
            if port in self.used_ports:
                print(self.i18n.get('port_already_allocated').format(port=port))
                continue
                
            # 检查端口是否被系统其他进程使用
            if not self.is_port_available(port):
                print(self.i18n.get('port_in_use').format(port=port))
                continue
                
            return port
        
    def configure_ports(self) -> dict:
        """配置所有服务的端口
        
        Returns:
            dict: 服务端口配置字典
        """
        port_config = {}
        self.used_ports.clear()  # 清空已使用端口列表
        
        for service, default_port in self.default_ports.items():
            # 检查默认端口是否可用
            if not self.is_port_available(default_port):
                # 找到下一个可用端口
                suggested_port = self.find_next_available_port(default_port)
                print(self.i18n.get('port_conflict').format(
                    service=service,
                    port=default_port
                ))
                # 让用户选择端口
                port = self.prompt_for_port(service, suggested_port)
            else:
                # 默认端口可用，询问用户是否要修改
                questions = [
                    inquirer.Confirm(
                        'use_default',
                        message=self.i18n.get('use_default_port').format(
                            service=service,
                            port=default_port
                        ),
                        default=True
                    )
                ]
                
                if inquirer.prompt(questions)['use_default']:
                    port = default_port
                else:
                    port = self.prompt_for_port(service, default_port)
            
            # 记录已分配的端口
            self.used_ports.add(port)
            
            # 保存端口配置
            port_config[service] = port
            
        # 更新配置
        self.config_manager.set('ports', port_config)
        return port_config
