import socket
from typing import List, Tuple, Optional, Set, Dict
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
        
        # 清除之前的端口配置
        self.config_manager.set('ports', {})

    def get_used_ports(self) -> Set[int]:
        """获取系统当前使用的所有端口
        
        Returns:
            Set[int]: 已使用的端口集合
        """
        used_ports = set()
        try:
            # 使用 psutil 获取所有网络连接
            for conn in psutil.net_connections():
                # 收集所有本地端口，不管状态如何
                if conn.laddr:
                    used_ports.add(conn.laddr.port)
        except (psutil.Error, OSError):
            pass
        return used_ports
        
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
                    message=self.i18n.get('ask_new_port').format(
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
        
    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用
        
        Args:
            port: 要检查的端口号
            
        Returns:
            bool: 如果端口被占用返回 True，否则返回 False
        """
        try:
            # 使用 psutil 获取所有网络连接
            for conn in psutil.net_connections():
                # 检查任何状态的连接，只要端口匹配就认为是被占用
                if conn.laddr.port == port:
                    return True
            return False
        except (psutil.Error, OSError):
            # 如果获取连接信息失败，使用 socket 作为备选方案
            try:
                # 尝试同时绑定 IPv4 和 IPv6
                # 先尝试 IPv4
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                # 再尝试 IPv6
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                    s.bind(('::1', port))
                return False
            except socket.error:
                return True
                
    def _validate_port(self, port_str: str, system_ports: Set[int]) -> bool:
        """验证端口号是否有效
        
        Args:
            port_str: 端口号字符串
            system_ports: 系统已使用的端口集合
            
        Returns:
            bool: 端口号是否有效
        """
        try:
            port = int(port_str)
            if not 1 <= port <= 65535:
                print(self.i18n.get('invalid_port'))
                return False
                
            # 检查端口是否已被使用
            if port in system_ports or port in self.used_ports or self._is_port_in_use(port):
                print(self.i18n.get('port_in_use').format(port))
                return False
                
            return True
        except ValueError:
            print(self.i18n.get('invalid_port'))
            return False

    def _get_postgres_port(self) -> int:
        """获取 PostgreSQL 的端口号
        
        Returns:
            int: PostgreSQL 端口号
        """
        default_port = self.default_ports['postgres']
        system_ports = self.get_used_ports()
        
        # 检查默认端口是否被占用
        if default_port in system_ports or self._is_port_in_use(default_port):
            print(self.i18n.get('postgres_port_conflict').format(default_port))
            # 找到下一个可用端口作为建议
            next_port = self.find_next_available_port(default_port)
            
            while True:
                questions = [
                    inquirer.Text(
                        'port',
                        message=self.i18n.get('postgres_port_prompt').format(next_port),
                        default=str(next_port),
                        validate=lambda _, x: self._validate_port(x, system_ports)
                    )
                ]
                
                answers = inquirer.prompt(questions)
                if answers is None:  # 用户按了 Ctrl+C
                    continue
                    
                port = int(answers['port'])
                # 由于验证函数已经检查过端口可用性，这里可以直接使用
                self.used_ports.add(port)
                return port
        
        # 如果默认端口可用，直接使用
        self.used_ports.add(default_port)
        return default_port

    def configure_ports(self) -> Dict[str, int]:
        """配置所有服务的端口

        Returns:
            Dict[str, int]: 服务端口配置字典
        """
        port_config = {}
        self.used_ports.clear()  # 清空已使用端口列表
        
        # 获取当前系统已使用的端口列表
        system_ports = self.get_used_ports()
        
        for service, default_port in self.default_ports.items():
            if service == 'postgres':
                port = self._get_postgres_port()
            else:
                # 首先检查默认端口是否被占用
                if self._is_port_in_use(default_port):
                    # 找到下一个可用端口作为建议值
                    suggested_port = self.find_next_available_port(default_port)
                    print(self.i18n.get('ask_port_conflict').format(service, default_port))
                    questions = [
                        inquirer.Text(
                            'port',
                            message=self.i18n.get('ask_port').format(service, suggested_port),
                            default=str(suggested_port),
                            validate=lambda _, x: self._validate_port(x, system_ports)
                        )
                    ]
                else:
                    questions = [
                        inquirer.Text(
                            'port',
                            message=self.i18n.get('ask_port').format(service, default_port),
                            default=str(default_port),
                            validate=lambda _, x: self._validate_port(x, system_ports)
                        )
                    ]

                while True:
                    answers = inquirer.prompt(questions)
                    if answers is None:  # 用户按了 Ctrl+C
                        continue
                        
                    port = int(answers['port'])
                    # 由于验证函数已经检查过端口可用性，这里可以直接使用
                    self.used_ports.add(port)
                    break
            
            # 保存端口配置
            port_config[service] = port
            
        # 更新配置
        self.config_manager.set('ports', port_config)
        return port_config

    def get_port_config(self) -> Dict[str, int]:
        """获取端口配置
        
        Returns:
            Dict[str, int]: 端口配置字典
        """
        # 每次获取配置时都重新检查端口可用性
        port_config = self.config_manager.get('ports', {})
        if not port_config:
            return self.configure_ports()
            
        system_ports = self.get_used_ports()
        needs_reconfigure = False
        
        # 检查已保存的端口是否仍然可用
        for service, port in port_config.items():
            if port in system_ports or self._is_port_in_use(port):
                print(self.i18n.get('port_in_use').format(port))
                needs_reconfigure = True
                break
                
        if needs_reconfigure:
            return self.configure_ports()
            
        return port_config
