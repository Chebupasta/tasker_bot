# Быстрая установка

1. Скачай проект:
   ```bash
   git clone https://github.com/Chebupasta/tasker_bot/
   cd tasker_bot
   ```
2. Установи библиотеки:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируй настройки:
   ```bash
   cp env.example .env
   # Впиши свой TELEGRAM_BOT_TOKEN в .env
   ```
4. Запусти бота:
   ```bash
   python bot.py
   ```

Чтобы добавить администратора, запусти:
```bash
python manage_admins.py
```

Все секреты и настройки — только в .env (он не попадает в git).

Подробности и вклад — см. README.md и CONTRIBUTING.md. 
