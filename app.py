import select
import subprocess
import time
import socket

import streamlit as st

# Конфигурация сервиса
# TODO добавить автоопределение
HOST = "192.168.1.69"
# (НЕ РАБОТАЕТ) Для автоопределения IP: socket.gethostbyname(socket.gethostname())

# Список ваших сервисов
# display - отображаемое имя, port - порт сервера
SERVICES = {
    "web-panel": {"display": "Web panel (this)", "port": 8501},
    "llama.cpp": {
        "display": "Llama.cpp",
        "port": 8080,
    },
    "silly-tavern": {
        "display": "Silly Tavern",
        "port": 8000,
    },
    "marinara-engine": {
        "display": "Marinara Engine",
        "port": 7860,
    },
    "comfyui": {
        "display": "ComfyUI",
        "port": 8188,
    },
    "comfyui-nocache": {
        "display": "ComfyUI No cache",
        "port": 8188,
    },
    "acestep.cpp": {
        "display": "AceStep.cpp",
        "port": 8085,
    },
}

@st.cache_resource
def reload_systemd_services():
    """Выполняется один раз при запуске приложения."""
    try:
        # Выполняем команду перечитывания конфигурации
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=True,
            capture_output=True,
            text=True,
            # Обязательно, так как streamlit может не иметь доступа к XDG_RUNTIME_DIR
            # env={"XDG_RUNTIME_DIR": "/run/user/1000"},  # Замените 1000 на UID вашего пользователя
        )
        return "Сервисы успешно обновлены!"
    except subprocess.CalledProcessError as e:
        return f"Ошибка обновления: {e.stderr}"


# Streamlit вызывает эту функцию сразу.
# Благодаря @st.cache_resource, реальный запуск systemctl произойдет только 1 раз.
init_message = reload_systemd_services()

# Выводим статус в интерфейс (по желанию)
st.sidebar.info(init_message)

st.set_page_config(page_title="LLM Node Control", page_icon="🤖", layout="wide")
st.title("📟 Мой Сервер управления LLM")


def get_status(service_name):
    """Проверяет, работает ли служба в данный момент"""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", service_name],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "active"


def get_logs(service_name, n_lines):
    """Получает последние N строк логов сервиса через journalctl"""
    if n_lines <= 0:
        return []
    result = subprocess.run(
        [
            "journalctl",
            "--user",
            "-u",
            service_name,
            "--no-pager",
            "-n",
            str(n_lines),
            "--output",
            "cat",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [
            f"⚠️ Ошибка journalctl (код {result.returncode}): {result.stderr.strip()}"
        ]
    text = result.stdout.strip()
    if not text:
        return ["Нет записей в логах."]
    return text.splitlines()




# Отрисовка интерфейса
for service_id, config in SERVICES.items():
    display_name = config["display"]
    port = config["port"]
    is_running = get_status(service_id)

    # Создаем визуальный блок для каждого сервиса
    with st.container(border=True):
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

        with col1:
            status_emoji = "🟢 Запущен" if is_running else "🔴 Остановлен"
            st.markdown(f"### {display_name}\nСтатус: **{status_emoji}**")

        with col2:
            if st.button(
                "▶️",
                key=f"start_{service_id}",
                disabled=is_running,
                use_container_width=True,
                help="Старт",
            ):
                subprocess.run(["systemctl", "--user", "start", service_id])
                st.rerun()

        with col3:
            if st.button(
                "⏹️",
                key=f"stop_{service_id}",
                disabled=not is_running,
                use_container_width=True,
                help="Стоп",
            ):
                subprocess.run(["systemctl", "--user", "stop", service_id])
                st.rerun()

        with col4:
            if st.button(
                "🔄",
                key=f"restart_{service_id}",
                disabled=not is_running,
                use_container_width=True,
                help="Рестарт",
            ):
                subprocess.run(["systemctl", "--user", "restart", service_id])
                st.rerun()

        # Состояние логов для каждого сервиса
        ss_key = f"logs_open_{service_id}"
        ss_n_key = f"logs_n_{service_id}"
        btn_key = f"logs_btn_{service_id}"

        if ss_key not in st.session_state:
            st.session_state[ss_key] = False
        if ss_n_key not in st.session_state:
            st.session_state[ss_n_key] = 100

        LOGS_PAGE = 50  # количество строк за один шаг

        with col5:
            if st.button("📋", key=btn_key, use_container_width=True, help="Логи"):
                st.session_state[ss_key] = not st.session_state[ss_key]
                st.rerun()

        with col6:
            url = f"http://{HOST}:{port}"
            st.markdown(f"[🔗]({url})", unsafe_allow_html=True)


        # Аккордион с логами
        if st.session_state[ss_key]:
            current_n = st.session_state[ss_n_key]
            lines = get_logs(service_id, current_n)

            with st.expander(f"📜 Логи ({len(lines)} строк)", expanded=True):
                display = list(lines)

                st.code("\n".join(display), language="text")

                if st.button(
                    "⬆️ Обновить",
                    key=f"older_{service_id}",
                    use_container_width=True,
                ):
                    # st.session_state[ss_n_key] = current_n + LOGS_PAGE
                    st.rerun()
