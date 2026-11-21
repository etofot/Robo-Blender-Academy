import os
import subprocess
import sys

MAX_FILE_SIZE_MB = 45
TOKEN = os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN")

def check_files():
    oversized = []
    for root, dirs, files in os.walk("."):
        if ".git" in root:
            continue
        for f in files:
            p = os.path.join(root, f)
            size_mb = os.path.getsize(p) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                oversized.append((p, size_mb))
    if oversized:
        print("[ОШИБКА] Обнаружены файлы больше 45 МБ! Пуш отменен:")
        for p, s in oversized:
            print(f"  - {p} ({s:.2f} МБ)")
        sys.exit(1)

def push_changes(message):
    check_files()
    subprocess.run(["git", "config", "user.name", "etofot"], check=True)
    subprocess.run(["git", "config", "user.email", "lovecyberboy@gmail.com"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    res = subprocess.run(["git", "commit", "-m", message])
    if res.returncode == 0:
        if TOKEN:
            repo_url = f"https://etofot:{TOKEN}@github.com/etofot/Robo-Blender-Academy.git"
            subprocess.run(["git", "push", repo_url, "main"], check=True)
            subprocess.run(["git", "remote", "set-url", "origin", "https://github.com/etofot/Robo-Blender-Academy.git"], check=True)
        else:
            subprocess.run(["git", "push", "origin", "main"], check=True)
        print("[УСПЕХ] Изменения успешно отправлены в Robo-Blender-Academy!")
    else:
        print("[INFO] Нет новых изменений для коммита.")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "feat(skills): добавлен скилл контрибьютора и скрипт безопасного пуша"
    push_changes(msg)
