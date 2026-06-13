# AGENTS.md

> Руководство для ИИ-агентов, работающих с проектом **web-panel**.

## О проекте

**web-panel** — веб-панель управления LLM-сервисами на базе **Streamlit**. Позволяет
запускать, останавливать и мониторить systemd user-сервисы (llama.cpp, ComfyUI, AceStep.cpp и др.)
через веб-интерфейс на Linux-сервере.

## Стек

| Компонент      | Технология                            |
| -------------- | ------------------------------------- |
| Фреймворк      | [Streamlit](https://streamlit.io/) >= 1.57.0 |
| Язык           | Python >= 3.14                        |
| Менеджер пакетов | [uv](https://github.com/astral-sh/uv) |
| Управление сервисами | systemd (user services)           |
| Мониторинг     | `systemctl --user`, `journalctl --user`, `nvidia-smi` |

## Структура

```
web-panel/
├── AGENTS.md                 # ← этот файл
├── TODO.md                   # План работ
├── README.md                 # Описание проекта
├── pyproject.toml            # Зависимости (uv)
├── uv.lock                   # Lock-файл uv
├── .python-version           # Версия Python
├── .gitignore
├── config.json               # Конфигурация сервисов (JSON)
├── examples/                 # Примеры юнит-файлов сервисов
│   ├── config.json
│   ├── llama.cpp.service
│   ├── marinara-engine.service
│   └── web-panel.service
└── src/
    └── web_panel/            # Пакет приложения (src-layout)
        ├── __init__.py
        ├── main.py             # CLI-точка входа (uv run web-panel)
        ├── app.py              # Основной код Streamlit
        └── utils.py            # Утилиты (load_config и др.)
```

## Точка входа

Основной CLI-модуль — **`web_panel.main`**. Запуск:

```bash
uv run web-panel --config ./config.json
```

Для работы на удалённом сервере:

```bash
uv run web-panel --port 8501 --listen 0.0.0.0 --config ./config.json
```

Файл `main.py` в корне больше не используется.

## Архитектура

### Текущее состояние

Пакет `src/web_panel/` содержит три модуля:

#### `main.py` — CLI-обёртка

Запускает Streamlit как отдельный процесс, передавая путь к конфигу через
переменную окружения `WEB_PANEL_CONFIG`.

- **`--config`** — путь к JSON-конфигу (по умолчанию `src/web_panel/config.json`).
- **`--port`** — порт (по умолчанию `8502`).
- **`--listen`** — адрес привязки (по умолчанию `0.0.0.0`).

Запускает `streamlit run src/web_panel/app.py` с параметрами `--server.port`,
`--server.address`, `--client.toolbarMode hidden`.

#### `app.py` — Streamlit-приложение

##### Загрузка конфигурации

- **`load_config(path)`** (из `utils.py`) — чтение JSON-файла.
- Путь к конфиги берётся из переменной окружения `WEB_PANEL_CONFIG` (устанавливается `main.py`).
- **`DEFAULT_SERVICES`** — fallback-словарь `{systemd_name: {display, port}}`.
- **`SERVICES`** — загружается из `config.json` (`config.get("services", DEFAULT_SERVICES)`).
- **`ALLOWED_IPS`** — список разрешённых IP-адресов/подсетей.

##### Проверка IP-адреса

- **`is_ip_allowed(ip_str)`** — проверка IP пользователя по списку `ALLOWED_IPS`.
  Поддерживаются точные IP, CIDR-подсети и маски со звёздочкой (`192.168.0.*`).
- Если IP не разрешён — выводится ошибка 403 и приложение завершается.

##### Управление сервисами

- **`get_status(service_name)`** — проверка `systemctl --user is-active`.
- **`render_service(service_id, config)`** — отрисовка карточки: название, статус, кнопки, ссылка на UI.
- Кнопки запуска/остановки/перезапуска через `systemctl --user start|stop|restart`.

##### Логи

- **`get_logs(service_name, n_lines)`** — `journalctl --user -u <service> --no-pager -n <N> --output cat`.
- **`render_log(service_id, config)`** — аккордеон с логами, динамическая подгрузка (±25 строк).
- Состояние хранится в `st.session_state`.

##### Метрики системы

- **`get_gpu_stats()`** — парсинг `nvidia-smi` (VRAM used/total, utilization %, temperature).
- **`get_memory_stats()`** — парсинг `/proc/meminfo` (RAM used/total/available).
- **`render_system_metrics()`** — отображение в 3 колонки над карточками сервисов.
- **`clean_mem()`** — `sudo sync; sudo sysctl -w vm.drop_caches=3`.

##### Автообновление

- **`@st.fragment(run_every=run_every)`** — реактивный фрагмент для периодического обновления.
- **`st.session_state.auto_refresh`** — переключатель в боковой панели.
- Слайдер для интервала обновления (0.5–5.0 с).

##### Кеширование

- **`@st.cache_resource`** — `reload_systemd_services()` (один раз при старте).
- **`@st.cache_data(ttl=5)`** — `get_gpu_stats()`, `get_memory_stats()` (обновление каждые 5 с).

#### `utils.py` — утилиты

- **`load_config(path)`** — чтение и парсинг JSON-конфига.

### Конфигурация

Файл `config.json` имеет следующую структуру:

```json
{
  "title": "Мой Сервер управления LLM",
  "allowed_ips": ["127.0.0.1", "192.168.1.0/24", "10.0.0.0/8", "192.168.0.*"],
  "services": {
    "llama.cpp": {
      "display": "Llama.cpp",
      "port": 8080
    }
  }
}
```

- **`title`** — заголовок панели.
- **`allowed_ips`** — список разрешённых IP/подсетей.
- **`services`** — маппинг systemd-имён на отображаемое имя и порт.

### Ключевые замечания

- Никаких внешних API ключей **не требуется** — всё через локальные системные вызовы.
- Приложение **предполагает Linux-сервер** с systemd, опционально GPU NVIDIA.
- `st.rerun()` — ручное обновление; `st.fragment(run_every=...)` — автообновление.
- `subprocess` вызовы напрямую влияют на систему — будьте осторожны.
- `sudo` используется в `clean_mem()` — убедитесь, что пользователь в группе sudo без пароля.
- Конфигурация сервисов вынесена в **`config.json`**.

## systemd-сервис

Юнит-файл `web-panel.service` размещается в `~/.config/systemd/user/`:

```ini
[Unit]
Description=My Custom Web Panel

[Service]
Type=simple
WorkingDirectory=/path/to/web-panel
ExecStart=%h/.local/bin/uv run web-panel --port 8501 --listen 0.0.0.0 --config=./config.json
Restart=always

[Install]
WantedBy=default.target
```

Установка:

```bash
cp examples/web-panel.service ~/.config/systemd/user/web-panel.service
# Отредактируйте WorkingDirectory и ExecStart
systemctl --user daemon-reload
systemctl --user enable --now web-panel.service
```

Для кнопки `Clean mem` настройте sudoers:

```bash
echo '%sudo ALL=NOPASSWD: /usr/bin/sync, /usr/sbin/sysctl -w vm.drop_caches=3' \
  | sudo tee /etc/sudoers.d/clean_mem
```

## Рекомендации для ИИ-агентов

1. **Не ломайте существующий UI** — Streamlit имеет специфичный паттерн ререндера.
2. **Сохраняйте обратную совместимость** — при рефакторинге `SERVICES` / `DEFAULT_SERVICES` обновляйте все места использования.
3. **Конфиг в `config.json`** — при добавлении нового сервиса обновите `config.json` (в корне и в `examples/`).
4. **Проверяйте diagnostics** после каждого изменения кода.
5. **Код пакета** — все модули в `src/web_panel/`. Не создавайте дополнительные файлы вне пакета без необходимости.
6. **Зависимости** — добавляйте через `uv add <package>`, не редактируйте `pyproject.toml` вручную.
7. **Состояние в session_state** — при добавлении новых UI-состояний используйте `st.session_state` с проверкой на существование.
8. **Стиль документации** — не использовать эмодзи, быть лаконичным.

## Виртуальное окружение

Проект использует `uv` для управления окружением.

```bash
# Установка зависимостей
uv sync

# Запуск (локальная разработка)
uv run streamlit run src/web_panel/app.py

# Запуск через CLI
uv run web-panel --config ./config.json
```
