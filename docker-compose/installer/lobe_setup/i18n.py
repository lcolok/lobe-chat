from typing import Dict, Any

class I18n:
    def __init__(self, language: str = 'en'):
        """初始化国际化实例
        
        Args:
            language: 语言代码 ('en' 或 'zh_CN')
        """
        self.language = language
        self.translations = {
            'en': {
                'ask_install_dir': 'Installation directory (last: {last_dir})',
                'ask_dir_exists': 'Directory exists, use it?',
                'ask_mode': 'Please select deployment mode',
                'ask_host': 'Please enter your hostname (domain mode example: example.com, port mode example: localhost)',
                'ask_port': 'Please enter {} port (default: {})',
                'ask_port_conflict': '{} default port {} is already in use.',
                'ask_new_port': 'Please enter {} port number (default: {})',
                'ask_regenerate_secrets': 'Regenerate security keys?',
                'generating_secrets': 'Generating security keys...',
                'secrets_generated': 'Security keys generated successfully.',
                'install_dir_exists': 'Directory already exists, use it?',
                'creating_dir': 'Creating directory: {dir}',
                'setup_cancelled': '\nSetup cancelled.',
                'setup_complete': 'Setup completed successfully!',
                'config_report_title': '=== Configuration Report ===',
                'next_steps': '\nNext Steps:\n1. Start the services with: docker compose up -d\n2. Access LobeChat at the configured URL',
                'invalid_port': 'Invalid port number. Please enter a number between 1 and 65535.',
                'port_in_use': 'Port {} is already in use.',
                'invalid_host': 'Invalid host. Please enter a valid domain name or IP address.',
                'mode_local': 'Local mode (localhost)',
                'mode_port': 'Port mode (custom port)',
                'mode_domain': 'Domain mode (custom domain)',
                'postgres_port_conflict': 'PostgreSQL default port {} is already in use.',
                'postgres_port_prompt': 'Please enter PostgreSQL port number (default: {})',
                'ask_add_custom_host': 'Do you want to add another hostname?',
                'ask_custom_host': 'Please enter the hostname (e.g., example.com)',
                'error_dir_not_empty': 'Directory is not empty and user chose not to use it',
                'error_config_host': 'Error configuring host',
                'error_config_env': 'Error configuring environment variables',
            },
            'zh_CN': {
                'ask_install_dir': '安装目录（上次：{last_dir}）',
                'ask_dir_exists': '目录已存在，是否使用？',
                'ask_mode': '请选择部署模式',
                'ask_host': '请输入您的主机名（域名模式示例：example.com，端口模式示例：localhost）',
                'ask_port': '请输入 {} 端口号（默认：{}）',
                'ask_port_conflict': '{} 的默认端口 {} 已被占用。',
                'ask_new_port': '请输入 {} 端口号（默认：{}）',
                'ask_regenerate_secrets': '是否重新生成安全密钥？',
                'generating_secrets': '正在生成安全密钥...',
                'secrets_generated': '安全密钥生成成功。',
                'install_dir_exists': '目录已存在，是否使用？',
                'creating_dir': '正在创建目录：{dir}',
                'setup_cancelled': '\n安装已取消。',
                'setup_complete': '安装成功完成！',
                'config_report_title': '=== 配置报告 ===',
                'next_steps': '\n后续步骤：\n1. 使用以下命令启动服务：docker compose up -d\n2. 使用配置的 URL 访问 LobeChat',
                'invalid_port': '无效的端口号。请输入 1-65535 之间的数字。',
                'port_in_use': '端口 {} 已被占用。',
                'invalid_host': '无效的主机名。请输入有效的域名或 IP 地址。',
                'mode_local': '本地模式（localhost）',
                'mode_port': '端口模式（自定义端口）',
                'mode_domain': '域名模式（自定义域名）',
                'postgres_port_conflict': 'PostgreSQL 默认端口 {} 已被占用。',
                'postgres_port_prompt': '请输入 PostgreSQL 端口号（默认：{}）',
                'ask_add_custom_host': '是否需要添加其他主机名？',
                'ask_custom_host': '请输入主机名（例如：example.com）',
                'error_dir_not_empty': '目录不为空且用户选择不使用',
                'error_config_host': '配置主机时出错',
                'error_config_env': '配置环境变量时出错',
            }
        }
        
    def get(self, key: str, **kwargs) -> str:
        """获取翻译文本
        
        Args:
            key: 翻译键
            **kwargs: 格式化参数
            
        Returns:
            str: 翻译后的文本
        """
        translation = self.translations.get(self.language, self.translations['en'])
        text = translation.get(key, self.translations['en'][key])
        return text.format(**kwargs) if kwargs else text

    @staticmethod
    def get_supported_languages() -> dict:
        """获取支持的语言列表"""
        return {
            'en': 'English',
            'zh_CN': '简体中文'
        }
