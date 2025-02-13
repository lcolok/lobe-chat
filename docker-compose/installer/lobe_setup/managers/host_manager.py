import inquirer
from typing import Dict, Tuple, Any
from .port_manager import PortManager

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
        
        # 保存配置
        self.config_manager.set('host', host)
        self.config_manager.set('mode', mode)
        
        return host, port_config
