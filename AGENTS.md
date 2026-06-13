# AGENTS.md

> Руководство для ИИ-агентов, работающих с проектом **web-panel**.

## О проекте

**web-panel** — веб-панель управления LLM-сервисами на базе **Streamlit**. Позволяет
запускать, останавливать и мониторить systemd user-сервисы (llama.cpp, ComfyUI, AceStep.cpp и др.)
через удобное веб-интерфейс на Linux-сервере.

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
├── main.py                   # Заглушка, не используется
├── app.py                    # Основной код приложения Streamlit
├── config.json               # Конфигурация сервисов (JSON)
├── web-panel.service         # systemd unit для самой панели
└── scripts/
    └── update_llama.sh       # Скрипты обслуживания
```

## Точка входа

Основной файл приложения — **`app.py`**. Запуск:

```bash
uv run streamlit run app.py
```

Файл `main.py` — заглушка, не используется (пустой `main()`).

## Архитектура

### Текущее состояние

`app.py` содержит следующие компоненты:

#### Загрузка конфигурации

- **`argparse`** — поддержка аргумента `--config` для указания JSON-конфига (по умолчанию `config.json`).
- **`DEFAULT_SERVICES`** — словарь маппинга `{systemd_name: {display, port}}` как fallback.
- **`SERVICES`** — загружается из `config.json` (`raw.get("services", DEFAULT_SERVICES)`).

#### Управление сервисами

- **`get_status(service_name)`** — проверка `systemctl --user is-active`.
- **`render_service(service_id, config)`** — отрисовка карточки: название, статус, кнопки ▶/⏹/🔄, ссылка на UI.
- Кнопки запуска/остановки/перезапуска через `systemctl --user start|stop|restart`.

#### Логи

- **`get_logs(service_name, n_lines)`** — `journalctl --user -u <service> --no-pager -n <N> --output cat`.
- **`render_log(service_id, config)`** — аккордеон с логами, динамическая подгрузка (±25 строк).
- Состояние хранится в `st.session_state`.

#### Метрики системы

- **`get_gpu_stats()`** — парсинг `nvidia-smi` (VRAM used/total, utilization %, temperature).
- **`get_memory_stats()`** — парсинг `/proc/meminfo` (RAM used/total/available).
- **`render_system_metrics()`** — отображение в 3 колонки над карточками сервисов.
- **`clean_mem()`** — `sudo sync; sudo sysctl -w vm.drop_caches=3`.

#### Автообновление

- **`st.fragment(run_every=run_every)`** — реактивный фремм для периодического обновления.
- **`st.session_state.auto_refresh`** — переключатель в боковой панели.
- Слайдер для интервала обновления (0.5–5.0 с).

#### Кеширование

- **`@st.cache_resource`** — `reload_systemd_services()` (один раз при старте).
- **`@st.cache_data(ttl=5)`** — `get_gpu_stats()`, `get_memory_stats()` (обновление каждые 5 с).

### Ключевые замечания

- Никаких внешних API ключей **не требуется** — всё через локальные системные вызовы.
- Приложение **предполагает Linux-сервер** с systemd, опционально GPU NVIDIA.
- `st.rerun()` — ручное обновление; `st.fragment(run_every=...)` — автообновление.
- `subprocess` вызовы напрямую влияют на систему — будьте осторожны.
- `sudo` используется в `clean_mem()` — убедитесь, что пользователь в группе sudo без пароля.
- Конфигурация сервисов вынесена в **`config.json`** — не забудьте обновить его при добавлении сервисов.


## Рекомендации для ИИ-агентов

1. **Не ломайте существующий UI** — Streamlit имеет специфичный паттерн ререндера.
2. **Сохраняйте обратную совместимость** — при рефакторинге `SERVICES` / `DEFAULT_SERVICES` обновляйте все места использования.
3. **Конфиг в `config.json`** — при добавлении нового сервиса обновите и `config.json`, и `DEFAULT_SERVICES` в `app.py`.
4. **Проверяйте diagnostics** после каждого изменения кода.
5. **Питон-код в `app.py`** — всё в одном файле на данном этапе. Не создавайте дополнительные модули без необходимости.
6. **Зависимости** — добавляйте через `uv add <package>`, не редактируйте `pyproject.toml` вручную.
7. **Состояние в session_state** — при добавлении новых UI-состояний используйте `st.session_state` с проверкой на существование (`if key not in st.session_state: st.session_state[key] = default`).

## Виртуальное окружение

Проект использует `uv` для управления окружением.

```bash
# Установка зависимостей
uv sync

# Запуск приложения
uv run streamlit run app.py
```
