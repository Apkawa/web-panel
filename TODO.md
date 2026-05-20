* app.py отображение кликабельного урла сервиса, открывается в новой вкладке
отрефакторить конфиг 
```python

SERVICES = {
  "<service_name>": {
    'display': "<display_name>",
    'port': 8080 # порт сервера, на странице выводить как http://<ip сервера>:<port>
  },
    "llama.cpp": {
      'display': "Llama.cpp",
      'port': 8080
    }
}
```

* просмотр логов `journalctl --user -u llama.cpp` и динамическая подгрузка последних строк по типу `journalctl --user -u comfyui -f`. Логи по умолчанию свернуты в аккардеон и не подгружаются.

* отображение статистики хоста, сверху
  - GPU %
  - VRAM <used>\<total> Gb (<percent>%) 
  - CPU %
  - RAM <used>\<total> Gb (<percent>%)

* изучить возможность вывести статистику ресурсов по сервисам
