#!/usr/bin/env python3
import argparse
import os
import platform
import sys
import shutil
import secrets
import string
import signal
import requests
import inquirer
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import print as rprint
from .config import Config
from .i18n import I18n

class LobeSetup:
    def __init__(self):
        self.source_url = "https://raw.githubusercontent.com/lobehub/lobe-chat/main"
        self.host = ""
        self.config = Config()
        self.i18n = I18n(self.config.get("language"))
        self.console = Console()
        self.install_dir = self.config.get("last_install_dir")
        self._setup_signal_handlers()
        self.downloaded_files = []
        self.secrets_regenerated = False
        self.configs = {}

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """处理中断信号"""
        self.console.print(self.i18n.get("setup_cancelled"), style="bold red")
        sys.exit(1)

    def _ask_question(self, questions: list) -> Dict[str, Any]:
        """使用 inquirer 提问并处理可能的中断"""
        try:
            return inquirer.prompt(questions)
        except KeyboardInterrupt:
            self.console.print(self.i18n.get("setup_cancelled"), style="bold red")
            sys.exit(1)

    def configure_language(self):
        """配置语言偏好"""
        if not self.config.get("language_selected"):
            questions = [
                inquirer.List('language',
                            message=self.i18n.get("ask_language"),
                            choices=[
                                ("English", "en"),
                                ("简体中文", "zh_CN"),
                            ],
                            default=self.i18n.language),
            ]
            
            answers = self._ask_question(questions)
            self.i18n.set_language(answers['language'])
            self.config.set("language", answers['language'])
            self.config.set("language_selected", True)
            self.config.save()

    def check_install_dir(self, dir_path: Path) -> Tuple[bool, str]:
        """检查安装目录是否已经包含 Lobe Chat 安装"""
        details = []
        if (dir_path / "data").exists():
            details.append("data/")
        if (dir_path / "s3_data").exists():
            details.append("s3_data/")
        return bool(details), ", ".join(details)

    def configure_install_dir(self):
        """配置安装目录"""
        last_dir = self.config.get("last_install_dir")
        questions = [
            inquirer.Text('install_dir',
                         message=self.i18n.get("ask_install_dir", last_dir=last_dir),
                         default=last_dir)
        ]
        
        while True:
            answers = self._ask_question(questions)
            install_dir = Path(os.path.expanduser(answers['install_dir']))
            
            # 如果目录存在，检查是否已安装
            if install_dir.exists():
                is_installed, details = self.check_install_dir(install_dir)
                if is_installed:
                    self.console.print(
                        self.i18n.get("tips_already_installed", 
                                    dir=str(install_dir),
                                    details=details),
                        style="bold yellow"
                    )
                    return False
                
                # 目录存在但未安装，询问是否使用
                confirm = self._ask_question([
                    inquirer.Confirm('use_existing',
                                   message=self.i18n.get("install_dir_exists"),
                                   default=True)
                ])
                
                if confirm['use_existing']:
                    self.install_dir = str(install_dir)
                    self.config.set("last_install_dir", self.install_dir)
                    self.config.save()
                    break
                else:
                    return False
            else:
                # 目录不存在，创建新目录
                self.install_dir = str(install_dir)
                self.config.set("last_install_dir", self.install_dir)
                self.config.save()
                self.console.print(self.i18n.get("creating_dir", dir=self.install_dir))
                os.makedirs(self.install_dir)
                break
        
        return True

    def download_file(self, url: str, local_path: str):
        """下载文件到指定目录，如果文件已存在则覆盖
        
        Args:
            url: 源文件URL
            local_path: 目标文件相对路径（相对于安装目录）
        """
        filename = os.path.basename(local_path)
        full_path = os.path.join(self.install_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 如果文件已存在，直接删除
        if os.path.exists(full_path):
            os.remove(full_path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                self.i18n.get("download_progress").format(filename=filename),
                total=100
            )

            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(full_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for data in response.iter_content(block_size):
                        downloaded += len(data)
                        f.write(data)
                        progress.update(task, completed=int(100 * downloaded / total_size))

        self.downloaded_files.append(filename)
        self.console.print(f"[green]✓[/green] {self.i18n.get('extracted_success')}: {filename}")

    def generate_random_string(self, length: int = 32) -> str:
        """生成随机字符串"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def generate_configs(self):
        """生成所有配置"""
        auth_secret = self.generate_random_string(6)  # 生成6位密码
        minio_password = self.generate_random_string(8)  # 生成8位密码

        # 准备配置信息
        self.configs = {
            "LobeChat": {
                "URL": self.host,
                "Username": "user",
                "Password": auth_secret
            },
            "Casdoor": {
                "URL": f"{self.host.replace('3210', '8000')}",
                "Username": "admin",
                "Password": auth_secret
            },
            "Minio": {
                "URL": f"{self.host.replace('3210', '9000')}",
                "Username": "admin",
                "Password": minio_password
            }
        }

        return auth_secret, minio_password

    def save_configs(self, auth_secret: str, minio_password: str):
        """保存配置到 .env 文件"""
        env_file = Path(self.install_dir) / ".env"
        env_example = Path(self.install_dir) / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)

        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()

            # 替换或添加配置
            replacements = {
                "AUTH_SECRET=": f"AUTH_SECRET={auth_secret}",
                "MINIO_ROOT_PASSWORD=": f"MINIO_ROOT_PASSWORD={minio_password}"
            }

            for key, value in replacements.items():
                if key in content:
                    content = content.replace(key, value)
                else:
                    content += f"\n{value}"

            with open(env_file, 'w') as f:
                f.write(content)
            
            self.secrets_regenerated = True

    def display_config_report(self):
        """显示配置报告"""
        self.console.print(f"\n[bold cyan]{self.i18n.get('config_report_title')}[/bold cyan]")
        
        for service, config in self.configs.items():
            self.console.print(f"\n[bold]{service}:[/bold]")
            for key, value in config.items():
                self.console.print(f"  - {key}: {value}")

    def configure_host(self):
        questions = [
            inquirer.List('mode',
                         message=self.i18n.get("ask_deploy_mode"),
                         choices=[
                             (self.i18n.get("deploy_modes.local"), "local"),
                             (self.i18n.get("deploy_modes.port"), "port"),
                             (self.i18n.get("deploy_modes.domain"), "domain"),
                         ],
                         default="local"),
        ]
        
        answers = self._ask_question(questions)
        mode = answers['mode']

        if mode == "local":
            self.host = "http://localhost:3210"
        elif mode == "port":
            questions = [
                inquirer.Text('port',
                            message=self.i18n.get("enter_port"),
                            default="3210",
                            validate=lambda _, x: x.isdigit())
            ]
            port_answer = self._ask_question(questions)
            self.host = f"http://localhost:{port_answer['port']}"
        else:  # domain mode
            questions = [
                inquirer.Text('domain',
                            message=self.i18n.get("enter_domain"),
                            validate=lambda _, x: len(x.strip()) > 0)
            ]
            domain_answer = self._ask_question(questions)
            self.host = f"https://{domain_answer['domain']}"

    def regenerate_secrets(self):
        """重新生成密钥"""
        questions = [
            inquirer.Confirm('regenerate',
                           message=self.i18n.get("ask_regenerate_secrets"),
                           default=True),
        ]
        
        answers = self._ask_question(questions)
        if answers['regenerate']:
            # 生成新的配置
            auth_secret, minio_password = self.generate_configs()
            # 保存配置
            self.save_configs(auth_secret, minio_password)
            # 显示配置报告
            self.display_config_report()

    def display_summary(self):
        """显示设置摘要"""
        summary = [
            f"[bold cyan]{self.i18n.get('install_dir')}:[/bold cyan] {self.install_dir}",
            f"[bold cyan]{self.i18n.get('host_config')}:[/bold cyan] {self.host}",
            f"[bold cyan]{self.i18n.get('files_downloaded')}:[/bold cyan]",
            *[f"  • {file}" for file in self.downloaded_files],
        ]
        if self.secrets_regenerated:
            summary.append(f"[bold green]✓ {self.i18n.get('secrets_regenerated')}[/bold green]")

        self.console.print(Panel(
            "\n".join(summary),
            title=self.i18n.get("setup_summary"),
            expand=False
        ))

    def setup(self):
        try:
            parser = argparse.ArgumentParser(description='Lobe Chat Setup Script')
            parser.add_argument('-l', '--lang', choices=['en', 'zh_CN'], default=None,
                            help='Language selection (en or zh_CN)')
            parser.add_argument('--url', default=self.source_url,
                            help='Source URL for downloading files')
            parser.add_argument('--host', help='Server host')
            parser.add_argument('--dir', help='Installation directory')
            
            args = parser.parse_args()
            
            # 如果命令行指定了语言，覆盖配置文件的设置
            if args.lang:
                self.i18n.set_language(args.lang)
                self.config.set("language", args.lang)
                self.config.set("language_selected", True)
                self.config.save()
            elif not self.config.get("language_selected"):
                self.configure_language()

            self.source_url = args.url
            self.host = args.host if args.host else self.host
            self.install_dir = args.dir if args.dir else self.install_dir

            # Configure installation directory
            if not self.configure_install_dir():
                sys.exit(1)

            # Download necessary files
            self.console.print(f"[bold blue]{self.i18n.get('downloading')}...[/bold blue]")
            
            # 下载 docker-compose.yml
            self.download_file(f"{self.source_url}/docker-compose/local/docker-compose.yml", "docker-compose.yml")
            
            # 根据语言选择下载不同的 .env.example 文件
            env_example_file = ".env.zh-CN.example" if self.i18n.language == "zh_CN" else ".env.example"
            self.download_file(
                f"{self.source_url}/docker-compose/local/{env_example_file}",
                ".env.example"  # 保存为 .env.example，方便后续使用
            )

            # Regenerate secrets
            self.regenerate_secrets()

            # Display summary
            self.console.print(f"\n{self.i18n.get('setup_complete')}")
            self.display_summary()
            
        except Exception as e:
            self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
            sys.exit(1)
