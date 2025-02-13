import os
from pathlib import Path
import requests
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from typing import List

class FileManager:
    def __init__(self, install_dir: str, source_url: str):
        self.install_dir = install_dir
        self.source_url = source_url
        self.downloaded_files = []

    def download_file(self, url: str, filename: str) -> bool:
        """下载文件"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            file_size = int(response.headers.get('content-length', 0))
            
            target_path = Path(self.install_dir) / filename
            
            with Progress(
                TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(
                    "download",
                    total=file_size,
                    filename=filename
                )
                
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
                            
            self.downloaded_files.append(filename)
            return True
            
        except Exception as e:
            print(f"Error downloading {filename}: {str(e)}")
            return False

    def download_required_files(self, language: str):
        """下载所需文件"""
        # 下载 docker-compose.yml
        self.download_file(f"{self.source_url}/docker-compose/local/docker-compose.yml", "docker-compose.yml")
        
        # 下载 init_data.json
        self.download_file(f"{self.source_url}/docker-compose/local/init_data.json", "init_data.json")
        
        # 根据语言选择下载不同的 .env.example 文件
        env_example_file = ".env.zh-CN.example" if language == "zh_CN" else ".env.example"
        self.download_file(
            f"{self.source_url}/docker-compose/local/{env_example_file}",
            ".env.example"  # 保存为 .env.example，方便后续使用
        )

    def get_downloaded_files(self) -> List[str]:
        """获取已下载的文件列表"""
        return self.downloaded_files
