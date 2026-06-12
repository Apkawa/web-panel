# run

`uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --client.toolbarMode hidden`

## Add service to systemctl

### web-panel.service

1. Write file`~/.config/systemd/user/web-panel.service`

```service
[Unit]
Description=Web panel

[Service]
Type=simple
# Actual path to web-panel
WorkingDirectory=/path/to/web-panel
# Actual path to installed uv (whereis uv)
ExecStart=%h/.local/bin/uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --client.toolbarMode hidden -- --config=./config.json
Restart=always

[Install]
WantedBy=default.target
```

2. Fill `config.json`

Example:

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

```

3. `systemctl --user daemon-reload`
4. `systemctl --user restart web-panel.service`

### Example services

All user service must be write to `~/.config/systemd/user/`


- `llama.cpp.service`

  ```service
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

- `marinara-engine.service`

  ```service
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
