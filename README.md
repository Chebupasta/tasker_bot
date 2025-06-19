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
4. Запустите бота:
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

## Лицензия
MIT. Подробнее — в [LICENSE](LICENSE). 