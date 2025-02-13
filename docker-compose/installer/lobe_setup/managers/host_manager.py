import inquirer
from typing import Dict, Tuple
from .port_manager import PortManager
from .file_managers import EnvManager, DockerComposeManager

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
        self.env_manager = EnvManager(config_manager.install_dir)
        self.docker_compose_manager = DockerComposeManager(config_manager.install_dir)
        
    def _get_host_config(self, mode: str) -> str:
        """获取主机配置
        
        Args:
            mode: 部署模式 ('localhost', 'port', 'domain')
            
        Returns:
            str: 主机名
        """
        if mode == 'localhost':
            return 'localhost'
            
        # 端口模式和域名模式都需要配置域名
        questions = [
            inquirer.Text(
                'host',
                message=self.i18n.get('ask_host'),
                default='example.com' if mode == 'domain' else 'localhost'
            )
        ]
        
        host = inquirer.prompt(questions)['host']
        
        # 如果是域名模式，验证域名格式
        if mode == 'domain':
            # TODO: 添加域名格式验证
            pass
            
        return host
        
    def _get_config_values(self) -> Dict[str, str]:
        """获取配置值，从配置管理器中读取或生成新的值
        
        Returns:
            Dict[str, str]: 配置值字典
        """
        # 从配置管理器中获取已存在的值
        auth_secret = self.config_manager.get('auth_casdoor_secret')
        minio_password = self.config_manager.get('minio_root_password')
        
        # 如果值不存在，则使用配置管理器生成新的值
        config_values = {
            'AUTH_CASDOOR_SECRET': auth_secret or self.config_manager.get_generated_value('auth_casdoor_secret'),
            'MINIO_ROOT_PASSWORD': minio_password or self.config_manager.get_generated_value('minio_root_password')
        }
        
        # 保存生成的值到配置管理器
        self.config_manager.set('auth_casdoor_secret', config_values['AUTH_CASDOOR_SECRET'])
        self.config_manager.set('minio_root_password', config_values['MINIO_ROOT_PASSWORD'])
        
        return config_values
        
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
        
        # 获取主机配置
        host = self._get_host_config(mode)
            
        # 配置端口
        port_config = self.port_manager.configure_ports()
        
        # 获取配置值
        config_values = self._get_config_values()
        
        # 更新配置文件
        self.env_manager.update_env_file(port_config, host, config_values)
        self.docker_compose_manager.update_docker_compose(port_config)
        
        # 保存配置
        self.config_manager.set('host', host)
        self.config_manager.set('mode', mode)
        
        return host, port_config
