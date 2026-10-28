
from pathlib import Path

ROOT = Path(__file__).resolve().parent

folders = [
    "config",
    "foodbot",
    "foodbot/templates/foodbot",
    "foodbot/static/foodbot",
]

files = [
    "manage.py",
    "config/settings.py",
    "config/urls.py",
    "foodbot/__init__.py",
    "foodbot/apps.py",
    "foodbot/models.py",
    "foodbot/views.py",
    "foodbot/urls.py",
    "foodbot/admin.py",
    "foodbot/templates/foodbot/home.html",
    "foodbot/static/foodbot/style.css",
    "foodbot/static/foodbot/app.js",
]

for folder in folders:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)

for filename in files:
    path = ROOT / filename

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        print(f"[+] Түзүлдү: {filename}")
    else:
        print(f"[=] Бар, өзгөргөн жок: {filename}")

print("\nFoodBot структурасы даяр!")
