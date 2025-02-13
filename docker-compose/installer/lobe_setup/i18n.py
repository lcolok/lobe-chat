from typing import Dict, Any

class I18n:
    def __init__(self, language='en'):
        self.language = language
        self.translations = {
            'en': {
                'ask_install_dir': 'Installation directory (last: {last_dir})',
                'install_dir_exists': 'Directory exists, use it?',
                'creating_dir': 'Creating directory: {dir}',
                'setup_cancelled': 'Setup cancelled.',
                'ask_port': 'Enter port for {service} (default: {port})',
                'port_conflict': '⚠️ Default port {port} for {service} is in use.',
                'use_default_port': 'Use default port {port} for {service}?',
                'port_in_use': '⚠️ Port {port} is already in use by another process.',
                'port_already_allocated': '⚠️ Port {port} is already allocated to another service.',
                'ask_regenerate_secrets': 'Regenerate security keys?',
                'config_report_title': '🔑 Configuration Report',
                'next_steps': '''
Next Steps:
Run the following command to start services:
docker compose up -d

Make sure required ports are open in your firewall.

For more information, visit: https://github.com/lobehub/lobe-chat''',
                'setup_complete': 'Setup complete!',
                'ask_mode': 'Select deployment mode:',
                'mode_localhost': 'Local mode (localhost)',
                'mode_port': 'Port mode (custom port)',
                'mode_domain': 'Domain mode (custom domain)',
            },
            'zh_CN': {
                'ask_install_dir': '安装目录（上次：{last_dir}）',
                'install_dir_exists': '目录已存在，是否使用？',
                'creating_dir': '正在创建目录：{dir}',
                'setup_cancelled': '安装已取消。',
                'ask_port': '请输入 {service} 的端口号（默认：{port}）',
                'port_conflict': '⚠️ {service} 的默认端口 {port} 已被占用。',
                'use_default_port': '是否使用默认端口 {port} 用于 {service}？',
                'port_in_use': '⚠️ 端口 {port} 已被其他进程占用。',
                'port_already_allocated': '⚠️ 端口 {port} 已被分配给其他服务。',
                'ask_regenerate_secrets': '是否重新生成安全密钥？',
                'config_report_title': '🔑 配置报告',
                'next_steps': '''
下一步：
运行以下命令启动服务：
docker compose up -d

请确保防火墙已开放所需端口。

更多信息请访问：https://github.com/lobehub/lobe-chat''',
                'setup_complete': '安装完成！',
                'ask_mode': '请选择部署模式：',
                'mode_localhost': '本地模式（localhost）',
                'mode_port': '端口模式（自定义端口）',
                'mode_domain': '域名模式（自定义域名）',
            }
        }

    def get(self, key: str, **kwargs) -> str:
        """获取翻译文本
        
        Args:
            key: 翻译键名
            
        Returns:
            str: 翻译后的文本
        """
        translation = self.translations.get(self.language, self.translations['en'])
        text = translation.get(key, key)
        return text.format(**kwargs) if kwargs else text

    @staticmethod
    def get_supported_languages() -> dict:
        """获取支持的语言列表"""
        return {
            'en': 'English',
            'zh_CN': '简体中文'
        }
