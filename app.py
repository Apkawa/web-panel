import streamlit as st
import subprocess
import socket

# Конфигурация сервиса
# TODO добавить автоопределение
HOST = "192.168.1.69"
# (НЕ РАБОТАЕТ) Для автоопределения IP: socket.gethostbyname(socket.gethostname())

# Список ваших сервисов
# display - отображаемое имя, port - порт сервера
SERVICES = {
    "llama.cpp": {
        "display": "Llama.cpp",
        "port": 8080,
    },
    "comfyui": {
        "display": "ComfyUI",
        "port": 8188,
    },
    "comfyui-nocache": {
        "display": "ComfyUI No cache",
        "port": 8189,
    },
    "acestep.cpp": {
        "display": "AceStep.cpp",
        "port": 9090,
    },
}

st.set_page_config(page_title="LLM Node Control", page_icon="🤖", layout="centered")
st.title("📟 Мой Сервер управления LLM")

def get_status(service_name):
    """Проверяет, работает ли служба в данный момент"""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", service_name],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "active"

# Отрисовка интерфейса
for service_id, config in SERVICES.items():
    display_name = config["display"]
    port = config["port"]
    is_running = get_status(service_id)

    # Создаем визуальный блок для каждого сервиса
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            status_emoji = "🟢 Запущен" if is_running else "🔴 Остановлен"
            st.markdown(f"### {display_name}\nСтатус: **{status_emoji}**")

        with col2:
            if st.button("▶️ Старт", key=f"start_{service_id}", disabled=is_running, use_container_width=True):
                subprocess.run(["systemctl", "--user", "start", service_id])
                st.rerun()

        with col3:
            if st.button("⏹️ Стоп", key=f"stop_{service_id}", disabled=not is_running, use_container_width=True):
                subprocess.run(["systemctl", "--user", "stop", service_id])
                st.rerun()

        with col4:
            url = f"http://{HOST}:{port}"
            st.markdown(f'[🔗 OPEN]({url})', unsafe_allow_html=True)
