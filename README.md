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
uv run streamlit run app.py
```

Для работы на удалённом сервере:

```bash
uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --client.toolbarMode hidden
```

## Установка systemd-сервиса

### Подготовка

1. Скопируйте юнит-файл в директорию user-сервисов:

   ```bash
   cp web-panel.service ~/.config/systemd/user/web-panel.service
   ```

2. Отредактируйте `~/.config/systemd/user/web-panel.service`:

   - `WorkingDirectory` — путь к директории проекта
   - `ExecStart` — путь к `uv` (проверьте через `which uv`)

3. Настройте сервисы в `config.json`. Пример:

   ```json
   {
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
   ```

### Примеры сервисов

Все пользовательские сервисы размещаются в `~/.config/systemd/user/`.

#### llama.cpp.service

```ini
[Unit]
Description=llama.cpp server

[Service]
Type=simple
WorkingDirectory=/path/to/workdir/
ExecStart=/path/to/script/llama-cpp-run.sh
Restart=no

# Отключаем лимиты памяти systemd
MemoryAccounting=yes
MemoryMax=infinity
MemoryHigh=infinity

# Запрещаем systemd убивать сервис при нехватке памяти
OOMPolicy=continue

# Защищаем от системного OOM-killer
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
WorkingDirectory=/path/to/Marinara-Engine
ExecStart=/path/to/Marinara-Engine/start.sh
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
  "services": {
    "systemd-name": {
      "display": "Отображаемое имя",
      "port": 8080
    }
  }
}
```

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
├── main.py                   # Заглушка, не используется
├── app.py                    # Основной код приложения
├── config.json               # Конфигурация сервисов
├── web-panel.service         # systemd unit для панели
└── scripts/
    └── update_llama.sh       # Скрипты обслуживания
```
