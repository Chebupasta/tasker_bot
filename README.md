# Telegram Equipment Request Bot

Управляйте заявками на оборудование в Telegram: создание, просмотр, выполнение и отмена заявок с разграничением прав (админ/пользователь).

## Быстрый старт

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <repo-url>
   cd it
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируйте пример переменных окружения и укажите свой токен:
   ```bash
   cp env.example .env
   # затем отредактируйте .env и вставьте TELEGRAM_BOT_TOKEN
   ```
<<<<<<< HEAD
4. Запустите бота:
=======
4. Create a `.env` file in the project root with your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=<your token>
   ```
5. Run the bot:
>>>>>>> 810f071d5d604bd42eab3c33a291e89643229a67
   ```bash
   python bot.py
   ```

## Управление администраторами

Для добавления/удаления админов используйте:
```bash
python manage_admins.py
```
Следуйте инструкциям в консоли.

## Требования
- Python 3.8+
- Telegram-бот токен (получить у [@BotFather](https://t.me/BotFather))

## Структура
- `bot.py` — основной бот
- `manage_admins.py` — управление администраторами
- `requirements.txt` — зависимости
- `env.example` — пример переменных окружения

## Вклад
Pull requests приветствуются! Подробнее — в [CONTRIBUTING.md](CONTRIBUTING.md).

<<<<<<< HEAD
## Лицензия
MIT. Подробнее — в [LICENSE](LICENSE). 
=======
### For Regular Users
- `/start` - Start the bot and get welcome message
- `/help` - Show help information
- `/list` - View your requests
- **NEW**: Can complete their own requests
- **NEW**: Can cancel their own requests (if not in progress)

## New Features (v2.0)

### User Permissions
- **Complete Requests**: Users can mark their own requests as completed
- **Cancel Requests**: Users can cancel their own requests if they haven't been taken into work yet

### Administrator Features
- **Action Tracking**: Administrators can see who completed or rejected each request
- **Delete Permissions**: Only administrators can permanently delete requests
- **Enhanced Visibility**: Full audit trail of who performed what actions

### Database Improvements
- Added `completed_by_id` field to track who completed requests
- Added `cancelled_by_id` field to track who rejected/cancelled requests
- Improved performance with database indexes

## Requirements

- Python 3.8 or higher
- Telegram account
- Bot token from @BotFather 
>>>>>>> 810f071d5d604bd42eab3c33a291e89643229a67
