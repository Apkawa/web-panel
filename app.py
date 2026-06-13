import ipaddress
import json
import os
import subprocess

import streamlit as st

# Читаем переменную, которую передал наш main.py
config_path = os.environ.get("WEB_PANEL_CONFIG",
    os.path.join(os.path.dirname(__file__), "config.json"))

@st.cache_data
def load_config(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

config = load_config(config_path)

# ── Загрузка конфигурации сервисов ────────────────────────────────

DEFAULT_SERVICES = {
    "web-panel": {"display": "Web panel (this)", "port": 8501},
}

ALLOWED_IPS = [
    "127.0.0.1",
    "192.168.1.0/24",  # Разрешит всю сеть от 192.168.1.0 до 192.168.1.255
    "10.0.0.0/8",  # Разрешит всю сеть 10.*.*.*
    "192.168.0.*",  # Маска со звездочкой (автоматически превратится в /24)
]

SERVICES = config.get("services", DEFAULT_SERVICES)
ALLOWED_IPS = config.get("allowed_ips", ALLOWED_IPS)


def is_ip_allowed(ip_str):
    # Превращаем строку IP пользователя в специальный объект для сравнения
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False  # Некорректный IP-адрес

    # Список разрешенных сетей и одиночных IP
    # Сюда можно писать: точные IP, подсети со слэшем и маски со звездочкой

    for rule in ALLOWED_IPS:
        try:
            # Если в правиле есть звездочка, заменяем её на нули и слэш для библиотеки
            if "*" in rule:
                # Например, "192.168.2.*" превратится в "192.168.2.0/24"
                rule = rule.replace("*", "0") + "/24"

            # Создаем объект сети (или одиночного IP)
            network = ipaddress.ip_network(rule, strict=False)

            # Проверяем, входит ли IP пользователя в эту сеть
            if ip in network:
                return True
        except ValueError:
            continue  # Пропускаем ошибочные записи в списке правил

    return False


# st.json(dict(st.context.headers))
# Получаем IP-адрес пользователя из заголовков сервера
user_ip = st.context.ip_address

# Если вы заходите с самого сервера, адрес может быть равен None или "127.0.0.1"
if user_ip is None:
    user_ip = "127.0.0.1"

# Если IP в списке прокси (через запятую), берем первый
user_ip = user_ip.split(",")[0].strip()

st.write(f"Ваш текущий IP: `{user_ip}`")

# Проверка доступа
if not is_ip_allowed(user_ip):
    st.error("Доступ запрещен (403 Forbidden)")
    st.stop()




# Конфигурация интерфейса
HOST = st.context.headers["host"].split(":")[0]


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

title = config.get("title", "📟 Мой Сервер управления LLM")
st.set_page_config(
    page_title=title,
    page_icon="🤖",
    layout="wide",
)
st.title(title)


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


def clean_mem():
    with st.spinner("Processing.."):
        subprocess.run(
            ["sudo", "sync"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["sudo", "sysctl", "-w", "vm.drop_caches=3"],
            check=True,
            capture_output=True,
            text=True,
        )


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

        if st.button(
            "🧹 Clean mem",
            use_container_width=False,
            help="sudo sync; sysctl -w vm.drop_caches=3",
        ):
            clean_mem()
            st.rerun()


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
    st.session_state.auto_refresh = True


def toggle_auto_refresh():
    st.session_state.auto_refresh = not st.session_state.auto_refresh


st.sidebar.slider(
    "Обновление каждые (с)",
    0.5,
    5.0,
    value=1.0,
    key="run_every",
    step=0.5,
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


def render_service(service_id, config):
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

        with col6:
            url = f"http://{HOST}:{port}"
            st.markdown(f"[🔗]({url})", unsafe_allow_html=True)


def render_log(service_id, config):
    display_name = config["display"]

    ss_key = f"logs_open_{service_id}"
    ss_n_key = f"logs_n_{service_id}"

    if ss_key not in st.session_state:
        st.session_state[ss_key] = False
    if ss_n_key not in st.session_state:
        st.session_state[ss_n_key] = 25

    LOGS_PAGE = 25

    with st.expander(f"📜 Логи: {display_name}", expanded=st.session_state[ss_key]):
        current_n = st.session_state[ss_n_key]
        lines = get_logs(service_id, current_n)

        col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
        with col_a:
            st.caption(f"{len(lines)} строк")
        with col_b:
            if st.button(
                f"⬇️ -{LOGS_PAGE}",
                key=f"log_less_{service_id}",
                use_container_width=True,
                help="Уменьшить количество строк выводимого лога",
                disabled=current_n <= LOGS_PAGE,
            ):
                if current_n > LOGS_PAGE:
                    st.session_state[ss_n_key] = current_n - LOGS_PAGE
                    st.rerun()
        with col_c:
            if st.button(
                f"⬆️ +{LOGS_PAGE}",
                key=f"log_more_{service_id}",
                help="Увеличить количество строк выводимого лога",
                use_container_width=True,
            ):
                st.session_state[ss_n_key] = current_n + LOGS_PAGE
                st.rerun()

        with col_d:
            if st.button(
                f"🔁 ={LOGS_PAGE}",
                key=f"log_reset_{service_id}",
                help="Сбросить количество строк выводимого лога",
                use_container_width=True,
            ):
                st.session_state[ss_n_key] = LOGS_PAGE
                st.rerun()

        st.code("\n".join(lines), language="text")


@st.fragment(run_every=run_every)
def render_services():
    render_system_metrics()

    for service_id, config in SERVICES.items():
        render_service(service_id, config)
        render_log(service_id, config)


render_services()
