# web-panel

Веб-панель управления LLM-сервисами на базе **Streamlit**. Позволяет запускать,
останавливать и мониторить systemd user-сервисы (llama.cpp, ComfyUI, AceStep.cpp
и др.) через удобный веб-интерфейс на Linux-сервере.

## Требования

- Linux с systemd
- Python >= 3.14
- [uv](https://github.com/astral-sh/uv) — менеджер пакетов
- Опционально: GPU NVIDIA (для отображения метрик)

## Быстрый старт

```bash
uv sync
uv run web-panel --config ./config.json
```

Для работы на удалённом сервере:

```bash
uv run web-panel --port 8501 --listen 0.0.0.0 --config ./config.json
```

Или напрямую через Streamlit (для локальной разработки):

```bash
uv run streamlit run src/web_panel/app.py
```

## Установка systemd-сервиса

### Подготовка

1. Скопируйте юнит-файл из `examples/` в директорию user-сервисов:

   ```bash
   cp examples/web-panel.service ~/.config/systemd/user/web-panel.service
   ```

2. Отредактируйте `~/.config/systemd/user/web-panel.service`:

   - `WorkingDirectory` — путь к директории проекта
   - `ExecStart` — путь к `uv` (проверьте через `which uv`)

3. Настройте сервисы в `config.json`. Пример:

   ```json
   {
     "title": "Мой Сервер управления LLM",
     "allowed_ips": ["127.0.0.1", "192.168.1.0/24", "10.0.0.0/8", "192.168.0.*"],
     "services": {
       "web-panel": {
         "display": "Web panel (this)",
         "port": 8501
       },
       "llama.cpp": {
         "display": "Llama.cpp",
         "port": 8080
       },
       "marinara-engine": {
         "display": "Marinara Engine",
         "port": 7860
       }
     }
   }
   ```

4. Перезапустите systemd и запустите сервис:

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now web-panel.service
   systemctl --user restart web-panel.service
   ```

5. Для корректной работы кнопки `Clean mem` добавьте исключения для команд в sudoers:

   ```bash
   echo '%sudo ALL=NOPASSWD: /usr/bin/sync, /usr/sbin/sysctl -w vm.drop_caches=3' \
     | sudo tee /etc/sudoers.d/clean_mem
   ```

### Примеры сервисов

Все пользовательские сервисы размещаются в `~/.config/systemd/user/`.
Файлы примеров находятся в директории `examples/`.

#### llama.cpp.service

```ini
[Unit]
Description=llama.cpp server

[Service]
Type=simple
WorkingDirectory=/path/to/workdir/
ExecStart=/path/to/script/llama-cpp-run.sh
Restart=no

# 1. Отключаем лимиты памяти (снимает ограничения systemd)
MemoryAccounting=yes
MemoryMax=infinity
MemoryHigh=infinity

# 2. Запрещаем systemd убивать сервис при нехватке памяти
OOMPolicy=continue

# 3. Защищаем от системного OOM-killer ядра Linux
OOMScoreAdjust=-1000

[Install]
WantedBy=default.target
```

#### marinara-engine.service

```ini
[Unit]
Description=Marinara Engine server

[Service]
Type=simple
WorkingDirectory=/path/to/marinara-engine/Marinara-Engine
ExecStart=/path/to/marinara-engine/Marinara-Engine/start.sh
Restart=no

[Install]
WantedBy=default.target
```

## Управление сервисами через панель

- **Статус** — показывает текущее состояние systemd-сервиса (active/inactive)
- **Запуск / Остановка / Перезапуск** — через `systemctl --user`
- **Логи** — просмотр и динамическая подгрузка из journalctl
- **Метрики** — VRAM, загрузка GPU, температура, RAM
- **Автообновление** — настраиваемый интервал обновления в боковой панели

## Конфигурация

Сервисы задаются в `config.json` в формате:

```json
{
  "title": "Мой Сервер управления LLM",
  "allowed_ips": ["127.0.0.1", "192.168.1.0/24", "10.0.0.0/8", "192.168.0.*"],
  "services": {
    "systemd-name": {
      "display": "Отображаемое имя",
      "port": 8080
    }
  }
}
```

- **`title`** — заголовок панели.
- **`allowed_ips`** — список разрешённых IP-адресов/подсетей (поддерживаются точные IP, CIDR-подсети и маски со звёздочкой).
- **`services`** — маппинг systemd-имён на отображаемое имя и порт.

При добавлении нового сервиса не забудьте создать соответствующий юнит-файл
в `~/.config/systemd/user/` и перезагрузить daemon.

## Структура проекта

```
web-panel/
├── AGENTS.md                 # Руководство для ИИ-агентов
├── TODO.md                   # План работ
├── README.md                 # Этот файл
├── pyproject.toml            # Зависимости (uv)
├── uv.lock                   # Lock-файл uv
├── .python-version           # Версия Python
├── .gitignore
├── config.json               # Конфигурация сервисов
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
