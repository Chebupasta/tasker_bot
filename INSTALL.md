# Установка и запуск

1. Установите Python 3.8+ и pip.
2. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <repo-url>
   cd it
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Скопируйте пример переменных окружения:
   ```bash
   cp env.example .env
   # Впишите свой TELEGRAM_BOT_TOKEN в .env
   ```
5. Запустите бота:
   ```bash
   python bot.py
   ```

Для управления администраторами используйте:
```bash
python manage_admins.py
```

Подробности и вклад — см. README.md и CONTRIBUTING.md. 