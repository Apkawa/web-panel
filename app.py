import streamlit as st
import subprocess

# Список ваших сервисов: (Красивое имя, Системное имя службы)
SERVICES = {
    "Llama.cpp": "llama.cpp",
    "ComfyUI": "comfyui",
    "ComfyUI No cache": "comfyui-nocache",
    "AceStep.cpp": "acestep.cpp",
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
for display_name, service_id in SERVICES.items():
    is_running = get_status(service_id)

    # Создаем визуальный блок для каждого сервиса
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])

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

