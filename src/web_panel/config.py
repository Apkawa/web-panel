import json
import os
from typing import TypedDict


class ServiceConfig(TypedDict):
    display: str
    port: int


class Config(TypedDict):
    title: str
    port: str
    listen: str
    allowed_ips: list[str]
    services: dict[str, ServiceConfig]


DEFAULT_CONFIG: Config = {
    "title": "📟 Мой Сервер управления LLM",
    "port": "8501",
    "listen": "0.0.0.0",
    "services": {
        "web-panel": {"display": "Web panel (this)", "port": 8501},
    },
    "allowed_ips": [
        "127.0.0.1",
        "192.168.1.0/24",  # Разрешит всю сеть от 192.168.1.0 до 192.168.1.255
        "10.0.0.0/8",  # Разрешит всю сеть 10.*.*.*
        "192.168.0.*",  # Маска со звездочкой (автоматически превратится в /24)
    ],
}


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    with open(path, "r") as f:
        default_config = DEFAULT_CONFIG.copy()
        raw_config: Config = json.load(f)
        config = default_config
        config.update(raw_config)
        return config
