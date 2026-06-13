import os
import sys
import argparse
import subprocess

CONFIG_PATH = os.environ.get("WEB_PANEL_CONFIG",
    os.path.join(os.path.dirname(__file__), "config.json"))

def main(args: argparse.Namespace):
    # Получаем абсолютный путь к config.json, чтобы streamlit его нашел

    abs_config_path = os.path.abspath(args.config or CONFIG_PATH)

    # Находим, где лежит наш app.py внутри пакета
    current_dir = os.path.dirname(__file__)
    app_path = os.path.join(current_dir, "app.py")

    # Формируем команду для запуска streamlit
    cmd = [
        "streamlit", "run", app_path,
        "--server.port", "8502",
        "--server.address", "0.0.0.0",
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Node Control Panel")
    parser.add_argument(
        "--config",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config.json"),
        help="Path to JSON config file with services definition",
    )
    try:
        args = parser.parse_args()
    except SystemExit as e:
        os._exit(e.code)
    main(args)
