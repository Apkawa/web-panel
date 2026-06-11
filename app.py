import subprocess

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

st.set_page_config(
    page_title="LLM Node Control",
    page_icon="🤖",
    layout="wide",
)

st.title("📟 Мой Сервер управления LLM")


@st.cache_data(ttl=5)
def get_gpu_stats():
    """Парсит вывод nvidia-smi для получения статистики GPU."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        # Формат: "X MiB, Y MiB, Z %, T"
        parts = result.stdout.strip().split(",")
        used = int(parts[0].strip())
        total = int(parts[1].strip())
        util = int(parts[2].strip())
        temp = int(parts[3].strip())
        return {"used": used, "total": total, "util": util, "temp": temp}
    except Exception:
        return None


@st.cache_data(ttl=5)
def get_memory_stats():
    """Парсит /proc/meminfo для получения статистики RAM."""
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.split()[0])  # kB
        total = meminfo["MemTotal"]
        available = meminfo.get("MemAvailable", meminfo["MemFree"])
        used = total - available
        return {"used": used, "total": total, "available": available}
    except Exception:
        return None


def render_system_metrics():
    """Отрисовывает метрики системы в строку над сервисами."""
    gpu = get_gpu_stats()
    mem = get_memory_stats()

    cols = st.columns(3)

    # GPU Load
    with cols[0]:
        if gpu:
            st.metric(
                label="💻 GPU Load",
                value=f"{gpu['util']}%",
                help=f"Temperature: {gpu['temp']}°C",
            )
        else:
            st.metric(label="💻 GPU Load", value="—", help="nvidia-smi not available")

    # GPU Memory
    with cols[1]:
        if gpu:
            st.metric(
                label="🧠 GPU Memory",
                value=f"{gpu['used'] / 1024:.1f} / {gpu['total'] / 1024:.1f} GB",
            )
        else:
            st.metric(label="🧠 GPU Memory", value="—")

    # RAM
    with cols[2]:
        if mem:
            mem_used_gb = mem["used"] / 1024 / 1024
            mem_total_gb = mem["total"] / 1024 / 1024
            st.metric(
                label="🧮 RAM",
                value=f"{mem_used_gb:.1f} / {mem_total_gb:.1f} GB",
                help=f"Available: {mem['available'] / 1024 / 1024:.1f} GB",
            )
        else:
            st.metric(label="🧮 RAM", value="—")



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


# ── Автообновление ──────────────────────────────────────────────────

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

def toggle_auto_refresh():
    st.session_state.auto_refresh = not st.session_state.auto_refresh

st.sidebar.slider(
    "Обновление каждые (с)", 0.5, 5.0, value=2.0, key="run_every"
)
st.sidebar.button(
    "▶ Автообновление",
    disabled=st.session_state.auto_refresh,
    on_click=toggle_auto_refresh,
    type="primary",
)
st.sidebar.button(
    "⏹ Стоп",
    disabled=not st.session_state.auto_refresh,
    on_click=toggle_auto_refresh,
)

if st.session_state.auto_refresh:
    run_every = st.session_state.run_every
else:
    run_every = None


@st.fragment(run_every=run_every)
def render_services():
    render_system_metrics()

    for service_id, config in SERVICES.items():
        display_name = config["display"]
        port = config["port"]
        is_running = get_status(service_id)

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

            ss_key = f"logs_open_{service_id}"
            ss_n_key = f"logs_n_{service_id}"
            btn_key = f"logs_btn_{service_id}"

            if ss_key not in st.session_state:
                st.session_state[ss_key] = False
            if ss_n_key not in st.session_state:
                st.session_state[ss_n_key] = 100

            LOGS_PAGE = 50

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
                        st.session_state[ss_n_key] = current_n + LOGS_PAGE
                        st.rerun()


render_services()
