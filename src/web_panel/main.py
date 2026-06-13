import os
import sys
import argparse
import subprocess

from web_panel.utils import load_config

CONFIG_PATH = os.environ.get("WEB_PANEL_CONFIG",
    os.path.join(os.path.dirname(__file__), "config.json"))

def get_option(key, args, config):
    try:
        return getattr(args, key)
    except AttributeError:
        return config[key]


def run(args: argparse.Namespace):
    # Получаем абсолютный путь к config.json, чтобы streamlit его нашел

    abs_config_path = os.path.abspath(args.config or CONFIG_PATH)

    # Находим, где лежит наш app.py внутри пакета
    current_dir = os.path.dirname(__file__)
    app_path = os.path.join(current_dir, "app.py")

    default_config = {
        "port": "8501",
        "listen": "0.0.0.0",
    }
    user_config = load_config(abs_config_path)

    config = dict(default_config)
    config.update(user_config)


    port = get_option("port", args, config)
    listen = get_option("listen", args, config)

    # Формируем команду для запуска streamlit
    cmd = [
        "streamlit", "run", app_path,
        "--server.port", port,
        "--server.address", listen,
        "--client.toolbarMode", "hidden"
    ]

    # Передаем путь к конфигу через переменную окружения.
    # Это чище, чем прокидывать аргументы через CLI самого streamlit.
    env = os.environ.copy()
    env["WEB_PANEL_CONFIG"] = abs_config_path

    try:
        # Запускаем процесс и ждем его окончания
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="LLM Node Control Panel")
    parser.add_argument(
        "--config",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config.json"),
        help="Path to JSON config file with services definition",
    )
    parser.add_argument(
        "--port",
        type=str,
        default="8502",
        help="Port to run the panel on (default: 8502)",
    )
    parser.add_argument(
        "--listen",
        type=str,
        default="0.0.0.0",
        help="Address to listen on (default: 0.0.0.0)",
    )
    try:
        args = parser.parse_args()
    except SystemExit as e:
        os._exit(e.code)
    run(args)


if __name__ == "__main__":
    main()
