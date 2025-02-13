from typing import Dict, Any

MESSAGES = {
    "en": {
        "downloading": "Downloading required files",
        "download_progress": "Downloading {filename}",
        "download_complete": "✨ Download complete",
        "extracted_success": "Downloaded successfully",
        "tips_already_installed": "Cannot proceed: A Lobe Chat installation already exists in this directory ({dir})\nFound: {details}",
        "ask_deploy_mode": "Please select deployment mode",
        "ask_install_dir": "Installation directory (last used: {last_dir})",
        "ask_language": "Please select your preferred language",
        "install_dir_exists": "Directory exists. Do you want to use it?",
        "creating_dir": "Creating directory: {dir}",
        "deploy_modes": {
            "local": "Local Mode",
            "port": "Port Mode",
            "domain": "Domain Mode"
        },
        "languages": {
            "en": "English",
            "zh_CN": "简体中文"
        },
        "ask_regenerate_secrets": "Do you want to generate a new AUTH_SECRET?",
        "enter_port": "Enter the port number",
        "enter_domain": "Enter your domain (e.g., chat.example.com)",
        "setup_cancelled": "\n🚫 Setup cancelled by user.",
        "invalid_choice": "Invalid choice. Please try again.",
        "setup_complete": "✨ Setup completed successfully!",
        "setup_summary": "Setup Summary",
        "host_config": "Host Configuration",
        "install_dir": "Installation Directory",
        "files_downloaded": "Files Downloaded",
        "secrets_regenerated": "New AUTH_SECRET Generated",
        "config_report": "Configuration Report",
        "config_report_title": "Security Configuration Generated:",
        "proxy_config": "Reverse Proxy Configuration",
        "next_steps": "Next Steps",
        "run_command": "Run the following command to start services:",
        "tips_add_reverse_proxy": "Please add the following reverse proxy configurations:",
        "tips_run_command": "Run the following command to start the service:",
        "tips_allow_ports": "Make sure the required ports (3210, 8000, 9000) are open in your firewall.",
        "tips_show_documentation": "For more information, please visit: https://github.com/lobehub/lobe-chat"
    },
    "zh_CN": {
        "downloading": "正在下载所需文件",
        "download_progress": "正在下载 {filename}",
        "download_complete": "✨ 下载完成",
        "extracted_success": "下载成功",
        "tips_already_installed": "无法继续：该目录 ({dir}) 已存在 Lobe Chat 安装\n发现：{details}",
        "ask_deploy_mode": "请选择部署模式",
        "ask_install_dir": "安装目录（上次：{last_dir}）",
        "ask_language": "请选择您偏好的语言",
        "install_dir_exists": "目录已存在，是否使用？",
        "creating_dir": "正在创建目录：{dir}",
        "deploy_modes": {
            "local": "本地模式",
            "port": "端口模式",
            "domain": "域名模式"
        },
        "languages": {
            "en": "English",
            "zh_CN": "简体中文"
        },
        "ask_regenerate_secrets": "是否要生成新的 AUTH_SECRET？",
        "enter_port": "请输入端口号",
        "enter_domain": "请输入您的域名（例如：chat.example.com）",
        "setup_cancelled": "\n🚫 设置已被用户取消。",
        "invalid_choice": "无效的选择，请重试。",
        "setup_complete": "✨ 设置成功完成！",
        "setup_summary": "设置摘要",
        "host_config": "主机配置",
        "install_dir": "安装目录",
        "files_downloaded": "已下载文件",
        "secrets_regenerated": "已生成新的 AUTH_SECRET",
        "config_report": "配置报告",
        "config_report_title": "安全密钥生成结果如下：",
        "proxy_config": "反向代理配置",
        "next_steps": "下一步",
        "run_command": "运行以下命令启动服务：",
        "tips_add_reverse_proxy": "请添加以下反向代理配置：",
        "tips_run_command": "运行以下命令启动服务：",
        "tips_allow_ports": "请确保防火墙已开放所需端口（3210、8000、9000）。",
        "tips_show_documentation": "更多信息请访问：https://github.com/lobehub/lobe-chat"
    }
}

class I18n:
    def __init__(self, language: str = "en"):
        self.language = language

    def set_language(self, language: str):
        """设置当前语言"""
        self.language = language

    def get(self, key: str, **kwargs) -> str:
        """获取指定语言的消息
        
        Args:
            key: 消息键，支持点号分隔的嵌套键，如 'deploy_modes.local'
            **kwargs: 格式化参数
        
        Returns:
            str: 格式化后的消息
        """
        keys = key.split('.')
        msg = MESSAGES[self.language]
        for k in keys:
            msg = msg.get(k, MESSAGES["en"].get(k, key))
        return msg.format(**kwargs) if kwargs else msg

    @staticmethod
    def get_supported_languages() -> Dict[str, str]:
        """获取支持的语言列表"""
        return {
            "en": "English",
            "zh_CN": "简体中文"
        }
