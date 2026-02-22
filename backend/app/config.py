import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict, field_validator
from typing import Optional, List

import os
from pathlib import Path
default_db_path = str(Path(__file__).parent.parent/'data'/'db.sqlite3').replace('\\', '/')

class Settings(BaseSettings):
    app_name: str = "Akari Task Scheduler"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    # AKARI_PATH 为存放backend, frontend文件的目录
    db_url: str = f"sqlite://{default_db_path}"
    db_modules: dict = {"models": ["app.models.task", "app.models.log"]}

    # Scheduler
    scheduler_max_workers: int = 10
    scheduler_job_defaults: dict = {
        "coalesce": False,
        "max_instances": 3,
        "misfire_grace_time": 60
    }

    # Task execution
    task_timeout_default: int = 300  # seconds
    task_max_concurrent: int = 5

    # Logging
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_ips: str = "127.0.0.1/32,192.168.0.0/16,172.17.0.1/32"  # IP和子网掩码标识，半角逗号分割，例如 "192.168.1.0/24,10.0.0.0/8"

    def get_allowed_ips(self) -> List[str]:
        """解析allowed_ips字符串为IP列表"""
        if not self.allowed_ips:
            return []
        return [ip.strip() for ip in self.allowed_ips.split(",") if ip.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",  # 从.env文件加载
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分大小写
        
    )
settings = Settings()
print(settings)