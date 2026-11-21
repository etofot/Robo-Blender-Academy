# 01. Руководство по Управлению Blender через MCP и CLI

ИИ-агент может управлять Blender двумя взаимодополняющими путями:
1. **Headless CLI (Безголовый запуск)** — идеален для автоматических тестов, пакетных экспортов и генерации ассетов в фоне.
2. **Live WebSocket MCP Server (Интерактивный режим)** — агент отправляет Python-код в уже открытое окно Blender разработчика и мгновенно видит изменения.

---

## 1. Режим Headless CLI (Рекомендуемый для скриптов)

Запуск Blender в фоновом режиме через PowerShell:
```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --factory-startup -b -P "script.py"
```

### ⚠️ Критическое правило флага `--factory-startup`
Если запускать Blender без флага `--factory-startup`, сторонние установленные пользовательские плагины (spring_bones, rigify, clean_mesh и др.) могут выбросить исключение при выходе из безголового режима (`unregister() exception`), что приведет к коду возврата ошибки процесса, даже если твой скрипт отработал на 100% идеально! **Всегда добавляй `--factory-startup`.**

---

## 2. Интерактивный MCP Сервер (WebSocket Port 9876 / 5656)

В папке `01_MCP_AND_BLENDER_CONTROL` содержатся два готовых решения:
- `antigravity-blender-mcp/` — сервер MCP для интеграции с современными агентскими средами через протокол JSON-RPC / stdio.
- `blender-live-addon/blender_bridge_addon.py` — аддон для Blender, поднимающий WebSocket-сервер на порту `9876`.

### Установка аддона в Blender:
1. Открой Blender $\to$ Edit $\to$ Preferences $\to$ Add-ons $\to$ Install $\to$ выбери `blender_bridge_addon.py`.
2. Включи галочку «Blender Bridge MCP».
3. В боковой панели (N-Panel) появится вкладка **Blender MCP Server** $\to$ нажми **Start Server**.
4. Любой скрипт теперь может отправлять команды по сокету:
```python
import socket, json

def send_to_blender(code_str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 9876))
    payload = json.dumps({"command": "execute", "code": code_str})
    s.sendall(payload.encode("utf-8"))
    res = s.recv(65536)
    s.close()
    return json.loads(res.decode("utf-8"))
```

---

## 3. Захват скриншотов и рендеров вьюпорта

Для визуальной проверки геометрии агент всегда может сделать быстрый скриншот сцены:
```python
import bpy

def capture_viewport(output_path):
    cam = bpy.context.scene.camera
    if not cam:
        cam_data = bpy.data.cameras.new("AgentCam")
        cam = bpy.data.objects.new("AgentCam", cam_data)
        bpy.context.collection.objects.link(cam)
        bpy.context.scene.camera = cam
        cam.location = (4.0, -5.0, 3.5)
        cam.rotation_euler = (math.radians(60), 0, math.radians(45))
        
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720
    bpy.ops.render.render(write_still=True)
    print(f"Viewport captured: {output_path}")
```
