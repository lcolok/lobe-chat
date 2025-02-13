import inquirer
from typing import Dict, Any, Tuple

class HostManager:
    def __init__(self, config_manager, i18n):
        self.config_manager = config_manager
        self.i18n = i18n
        self.host = ""

    def configure_host(self) -> Tuple[str, Dict[str, Any]]:
        """配置主机设置"""
        # 获取上次的部署模式
        last_mode = self.config_manager.get("deploy_mode", "local")
        
        questions = [
            inquirer.List('mode',
                         message=self.i18n.get("ask_deploy_mode"),
                         choices=[
                             (self.i18n.get("deploy_modes.local"), "local"),
                             (self.i18n.get("deploy_modes.port"), "port"),
                             (self.i18n.get("deploy_modes.domain"), "domain"),
                         ],
                         default=last_mode),
        ]
        
        answers = inquirer.prompt(questions)
        mode = answers['mode']
        
        # 保存选择的模式到项目配置
        self.config_manager.set("deploy_mode", mode)

        if mode == "local":
            self.host = "http://localhost:3210"
        elif mode == "port":
            # 获取上次使用的端口
            last_port = self.config_manager.get("port", "3210")
            questions = [
                inquirer.Text('port',
                            message=self.i18n.get("enter_port"),
                            default=last_port,
                            validate=lambda _, x: x.isdigit())
            ]
            port_answer = inquirer.prompt(questions)
            self.host = f"http://localhost:{port_answer['port']}"
            # 保存端口设置到项目配置
            self.config_manager.set("port", port_answer['port'])
        else:  # domain mode
            # 获取上次使用的域名
            last_domain = self.config_manager.get("domain", "")
            questions = [
                inquirer.Text('domain',
                            message=self.i18n.get("enter_domain"),
                            default=last_domain,
                            validate=lambda _, x: len(x.strip()) > 0)
            ]
            domain_answer = inquirer.prompt(questions)
            self.host = f"https://{domain_answer['domain']}"
            # 保存域名设置到项目配置
            self.config_manager.set("domain", domain_answer['domain'])

        return self.host, {"mode": mode}
