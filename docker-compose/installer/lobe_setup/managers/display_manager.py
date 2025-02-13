from rich.console import Console
from rich.panel import Panel
from typing import List, Dict

class DisplayManager:
    def __init__(self, i18n):
        self.i18n = i18n
        self.console = Console()

    def display_config_report(self, configs: Dict[str, Dict[str, str]], host: str):
        """显示配置报告"""
        self.console.print(f"\n[bold cyan]{self.i18n.get('config_report_title')}[/bold cyan]")
        
        # 显示基本配置
        for service, config in configs.items():
            self.console.print(f"\n[bold]{service}:[/bold]")
            for key, value in config.items():
                self.console.print(f"  - {key}: {value}")

        # 如果是域名模式，显示反向代理配置
        if "localhost" not in host:
            self.console.print(f"\n[bold cyan]{self.i18n.get('tips_add_reverse_proxy')}[/bold cyan]")
            base_host = host.replace("http://", "").replace("https://", "").replace(":3210", "")
            proxy_configs = {
                f"{base_host}:3210": "127.0.0.1:3210",
                f"{base_host}:8000": "127.0.0.1:8000",
                f"{base_host}:9000": "127.0.0.1:9000"
            }
            for domain, target in proxy_configs.items():
                self.console.print(f"  {domain} -> {target}")

        # 显示后续步骤
        self.console.print(f"\n[bold green]{self.i18n.get('next_steps')}:[/bold green]")
        self.console.print(self.i18n.get("tips_run_command"))
        self.console.print("[bold]docker compose up -d[/bold]")
        self.console.print(f"\n{self.i18n.get('tips_allow_ports')}")
        self.console.print(f"\n{self.i18n.get('tips_show_documentation')}")

    def display_setup_summary(self, install_dir: str, downloaded_files: List[str], secrets_regenerated: bool):
        """显示设置摘要"""
        self.console.print(Panel.fit(
            "\n".join([
                f"{self.i18n.get('install_dir')}: {install_dir}",
                f"{self.i18n.get('host_config')}:",
                f"{self.i18n.get('files_downloaded')}:",
                *[f"  • {file}" for file in downloaded_files],
                "✓ " + self.i18n.get("secrets_regenerated") if secrets_regenerated else ""
            ]),
            title=self.i18n.get("setup_summary"),
            border_style="blue"
        ))
