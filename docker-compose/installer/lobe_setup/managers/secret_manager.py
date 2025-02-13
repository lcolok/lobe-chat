import subprocess
import secrets
import string
import inquirer
from typing import Dict

class SecretManager:
    def __init__(self, i18n):
        self.i18n = i18n
        self.secrets_regenerated = False
        self.configs = {}

    def generate_random_string(self, length: int = 32) -> str:
        """生成随机字符串"""
        try:
            # 尝试使用 openssl 生成随机字符串
            result = subprocess.run(
                ['openssl', 'rand', '-hex', str(length // 2)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            # 如果 openssl 命令失败，使用 Python 的 secrets 模块
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(length))

    def regenerate_secrets(self, host: str) -> Dict[str, Dict[str, str]]:
        """重新生成密钥"""
        questions = [
            inquirer.Confirm('regenerate',
                           message=self.i18n.get("ask_regenerate_secrets"),
                           default=True)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers['regenerate']:
            return {}

        self.secrets_regenerated = True
        
        # 生成密钥
        auth_secret = self.generate_random_string(32)
        casdoor_secret = self.generate_random_string(32)
        casdoor_password = self.generate_random_string(10)
        minio_password = self.generate_random_string(8)

        # 保存配置
        self.configs = {
            "LobeChat": {
                "URL": f"{host}",
                "Username": "user",
                "Password": auth_secret[:10]
            },
            "Casdoor": {
                "URL": f"{host.replace('3210', '8000')}",
                "Username": "admin",
                "Password": auth_secret[:10]
            },
            "Minio": {
                "URL": f"{host.replace('3210', '9000')}",
                "Username": "admin",
                "Password": minio_password
            }
        }

        return self.configs

    def get_configs(self) -> Dict[str, Dict[str, str]]:
        """获取配置"""
        return self.configs

    def is_secrets_regenerated(self) -> bool:
        """是否重新生成了密钥"""
        return self.secrets_regenerated
