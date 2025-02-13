import sys
import os
import signal
import argparse
import traceback
from pathlib import Path
import inquirer
from rich.console import Console
from .config import Config
from .i18n import I18n
from .managers import (
    ConfigManager,
    FileManager,
    HostManager,
    SecretManager,
    DisplayManager
)

class LobeSetup:
    def __init__(self):
        """初始化安装程序"""
        self.source_url = "https://raw.githubusercontent.com/lobehub/lobe-chat/main"
        self.config = Config()
        self.i18n = I18n(self.config.get("language"))
        self.install_dir = self.config.get("last_install_dir")
        self.console = Console()
        
        try:
            # 初始化各个管理器
            self.project_config = None  # 在configure_install_dir后初始化
            self.file_manager = FileManager(self.install_dir, self.source_url)
            self.host_manager = None  # 在configure_install_dir后初始化
            self.secret_manager = SecretManager(self.i18n)
            self.display_manager = DisplayManager(self.i18n)
            
            self._setup_signal_handlers()
        except Exception as e:
            self.console.print(f"[red]Error during initialization: {str(e)}[/red]")
            traceback.print_exc()
            sys.exit(1)

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """处理信号"""
        self.console.print(f"\n{self.i18n.get('setup_cancelled')}")
        sys.exit(1)

    def configure_install_dir(self):
        """配置安装目录"""
        try:
            questions = [
                inquirer.Text('install_dir',
                             message=self.i18n.get("ask_install_dir").format(last_dir=self.install_dir),
                             default=self.install_dir)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:  # 用户按了 Ctrl+C
                return False
                
            self.install_dir = answers['install_dir']
            
            # 更新全局配置中的安装目录
            self.config.set("last_install_dir", self.install_dir)
            
            # 检查目录是否存在
            if os.path.exists(self.install_dir):
                questions = [
                    inquirer.Confirm('use_existing',
                                   message=self.i18n.get("install_dir_exists"),
                                   default=True)
                ]
                
                if not inquirer.prompt(questions)['use_existing']:
                    self.console.print(f"\n{self.i18n.get('setup_cancelled')}")
                    return False
            else:
                # 创建目录
                self.console.print(self.i18n.get("creating_dir").format(dir=self.install_dir))
                os.makedirs(self.install_dir)
            
            # 初始化依赖于安装目录的管理器
            self.project_config = ConfigManager(self.install_dir)
            self.host_manager = HostManager(self.project_config, self.i18n)
            
            # 更新文件管理器的安装目录
            self.file_manager = FileManager(self.install_dir, self.source_url)
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error configuring install directory: {str(e)}[/red]")
            traceback.print_exc()
            return False

    def run(self):
        """运行安装程序"""
        try:
            # 配置安装目录
            if not self.configure_install_dir():
                return
            
            # 下载所需文件
            self.file_manager.download_required_files(self.i18n.language)
            
            # 配置主机设置
            try:
                host_config = self.host_manager.configure_host()
            except Exception as e:
                self.console.print(f"[red]Error configuring host: {str(e)}[/red]")
                traceback.print_exc()
                return
            
            # 重新生成密钥
            try:
                configs = self.secret_manager.regenerate_secrets(host_config[0])  # 传入 host
            except Exception as e:
                self.console.print(f"[red]Error generating secrets: {str(e)}[/red]")
                traceback.print_exc()
                return
            
            # 显示配置报告和设置摘要
            try:
                self.display_manager.display_config_report(configs, host_config)
                self.display_manager.display_setup_summary(
                    self.install_dir,
                    self.file_manager.get_downloaded_files(),
                    self.secret_manager.is_secrets_regenerated()
                )
            except Exception as e:
                self.console.print(f"[red]Error displaying configuration: {str(e)}[/red]")
                traceback.print_exc()
                return
            
            self.console.print("\n✨ " + self.i18n.get("setup_complete"))
            
        except KeyboardInterrupt:
            self.console.print(f"\n{self.i18n.get('setup_cancelled')}")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
            traceback.print_exc()
            sys.exit(1)

    def setup(self):
        try:
            parser = argparse.ArgumentParser(description='Lobe Chat Setup Script')
            parser.add_argument('--language', choices=['en', 'zh_CN'], help='Set the language')
            args = parser.parse_args()

            if args.language:
                self.config.set("language", args.language)
                self.config.set("language_selected", True)
                self.config.save()
                self.i18n = I18n(args.language)

            self.run()
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    setup = LobeSetup()
    setup.setup()
