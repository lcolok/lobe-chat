from rich.console import Console
from rich.panel import Panel
from typing import Dict, List, Tuple

class DisplayManager:
    def __init__(self, i18n):
        """初始化显示管理器
        
        Args:
            i18n: 国际化实例
        """
        self.i18n = i18n
        self.console = Console()
        
    def display_config_report(self, configs: Dict[str, str], host_config: Tuple[str, Dict[str, int]]) -> None:
        """显示配置报告
        
        Args:
            configs: 配置字典，包含各种服务的用户名和密码
            host_config: 主机配置元组 (host, port_config)，包含主机名和端口配置
        """
        self.console.print("\n" + self.i18n.get('config_report_title') + "\n")
        
        host, port_config = host_config
        
        # LobeChat 配置
        self.console.print("LobeChat:")
        self.console.print(f"  - URL: {host}:{port_config.get('lobe', 3210)}")
        self.console.print(f"  - Username: {configs.get('LOBE_USERNAME', 'user')}")
        self.console.print(f"  - Password: {configs.get('LOBE_PASSWORD', '')}")
        
        # Casdoor 配置
        self.console.print("\nCasdoor:")
        self.console.print(f"  - URL: {host}:{port_config.get('casdoor', 7001)}")
        self.console.print(f"  - Username: {configs.get('CASDOOR_ADMIN_USER', 'admin')}")
        self.console.print(f"  - Password: {configs.get('CASDOOR_ADMIN_PASSWORD', '')}")
        
        # Minio 配置
        self.console.print("\nMinio:")
        self.console.print(f"  - URL: {host}:{port_config.get('minio', 9000)}")
        self.console.print(f"  - Username: {configs.get('MINIO_ROOT_USER', 'admin')}")
        self.console.print(f"  - Password: {configs.get('MINIO_ROOT_PASSWORD', '')}")
        
        # 显示下一步操作
        self.console.print("\n" + self.i18n.get('next_steps'))
        
    def display_setup_summary(self, install_dir: str, downloaded_files: List[str], secrets_regenerated: bool) -> None:
        """显示安装摘要
        
        Args:
            install_dir: 安装目录
            downloaded_files: 已下载的文件列表
            secrets_regenerated: 是否重新生成了密钥
        """
        summary = f"""
install_dir: {install_dir}
已下载文件：:
  {chr(8226)} """ + f"\n  {chr(8226)} ".join(downloaded_files)
        
        if secrets_regenerated:
            summary += "\n✓ 已重新生成安全密钥。"
            
        self.console.print(Panel(summary, title="setup_summary"))
