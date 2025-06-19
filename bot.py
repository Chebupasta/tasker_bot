import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
import os
import sys

# Настройка логирования - записываем все в файл bot.log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Создаем базу данных SQLite
Base = declarative_base()
engine = create_engine('sqlite:///requests.db')
Session = sessionmaker(bind=engine)

# Токен нашего бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')  # API токен теперь берется из переменной окружения

# Состояния для создания заявки
EQUIPMENT, QUANTITY, DESCRIPTION, PRIORITY = range(4)

# Класс для пользователей в базе данных
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    is_admin = Column(Boolean, default=False)  # По умолчанию пользователь не админ
    created_at = Column(DateTime, default=func.now())
    # Основные заявки пользователя
    requests = relationship('Request', back_populates='user', foreign_keys='Request.user_id')
    # Заявки, которые пользователь принял
    completed_requests = relationship('Request', foreign_keys='Request.completed_by_id')
    # Заявки, которые пользователь отклонил/отменил
    cancelled_requests = relationship('Request', foreign_keys='Request.cancelled_by_id')

# Класс для заявок в базе данных
class Request(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    equipment_name = Column(String)
    quantity = Column(Integer)
    description = Column(Text)
    priority = Column(String)
    status = Column(String, default='new')  # new, in_progress, completed, cancelled
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)  # Для дополнительных заметок
    estimated_completion = Column(DateTime, nullable=True)  # Ожидаемая дата выполнения
    # Новые поля для отслеживания действий
    completed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Кто принял
    cancelled_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Кто отклонил/отменил
    # Отношения
    user = relationship('User', back_populates='requests', foreign_keys=[user_id])
    completed_by = relationship('User', foreign_keys=[completed_by_id])
    cancelled_by = relationship('User', foreign_keys=[cancelled_by_id])

# Создаем таблицы в базе данных
Base.metadata.create_all(engine)

# Константы для статусов и приоритетов
STATUSES = {
    'new': '🆕 Новые',
    'in_progress': '⏳ В процессе', 
    'completed': '✅ Выполненные',
    'cancelled': '❌ Отмененные'
}

PRIORITIES = {
    'high': '🔴 Высокий',
    'medium': '🟡 Средний', 
    'low': '🟢 Низкий'
}

# Функция для создания клавиатуры главного меню
def get_main_menu_keyboard(is_admin):
    if is_admin:
        keyboard = [
            ["📝 Создать заявку", "📋 Активные заявки"],
            ["✅ Выполненные заявки", "❌ Отмененные заявки"],
            ["❓ Помощь"]
        ]
    else:
        keyboard = [
            ["📋 Мои заявки"],
            ["❓ Помощь"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем сессию базы данных
        session = Session()
        
        # Ищем пользователя в базе
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        # Если пользователь не найден, создаем нового
        if not user:
            user = User(
                telegram_id=update.effective_user.id,
                username=update.effective_user.username,
                is_admin=False
            )
            session.add(user)
            session.commit()
            await update.message.reply_text(
                "👋 Добро пожаловать! Вы зарегистрированы как сотрудник. Используйте меню для работы с заявками.",
                reply_markup=get_main_menu_keyboard(False)
            )
        else:
            # Если пользователь уже есть, приветствуем его
            role = "администратор" if user.is_admin else "сотрудник"
            await update.message.reply_text(
                f"👋 Здравствуйте, {role}! Для работы с заявками используйте меню ниже.",
                reply_markup=get_main_menu_keyboard(user.is_admin)
            )
            
    except Exception as e:
        # Если что-то пошло не так, пишем в лог и сообщаем пользователю
        logger.error(f"Ошибка в start: {e}")
        await update.message.reply_text("Произошла ошибка при запуске. Попробуйте ещё раз или обратитесь к администратору.")
    finally:
        session.close()

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        is_admin = user.is_admin if user else False
        
        if is_admin:
            help_text = (
                "ℹ️ *Справка администратора*\n\n"
                "• Создавайте заявки через '📝 Создать заявку'\n"
                "• Просматривайте все заявки через '📋 Активные заявки'\n"
                "• Смотрите выполненные и отменённые заявки через соответствующие пункты меню\n"
                "• Для помощи используйте кнопку '❓ Помощь'\n\n"
                "Доступные команды:\n/start — начать заново\n/help — справка\n/cancel — отменить действие"
            )
        else:
            help_text = (
                "ℹ️ *Справка пользователя*\n\n"
                "• Просматривайте все активные заявки через '📋 Активные заявки'\n"
                "• Принимайте или отклоняйте заявки\n"
                "• Смотрите выполненные и отменённые заявки через соответствующие пункты меню\n"
                "• Для помощи используйте кнопку '❓ Помощь'\n\n"
                "Доступные команды:\n/start — начать заново\n/help — справка\n/cancel — отменить действие"
            )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    except Exception as e:
        logger.error(f"Ошибка в help: {e}")
        await update.message.reply_text("Произошла ошибка при загрузке справки. Попробуйте позже.")
    finally:
        session.close()

# Обработчик создания заявки
async def create_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        # Проверяем, админ ли пользователь
        if not user or not user.is_admin:
            await update.message.reply_text(
                "Доступ к созданию заявок разрешён только администраторам. Если вам нужна помощь, обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard(False)
            )
            return ConversationHandler.END

        # Очищаем старые данные
        context.user_data.clear()
        
        # Просим ввести название оборудования
        await update.message.reply_text(
            "Введите, пожалуйста, название оборудования или материала:"
        )
        return EQUIPMENT
        
    except Exception as e:
        logger.error(f"Ошибка в create_request: {e}")
        await update.message.reply_text("Произошла ошибка при создании заявки. Попробуйте позже.")
        return ConversationHandler.END
    finally:
        session.close()

# Обработчик ввода оборудования
async def equipment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Проверяем, не отменил ли пользователь
        if update.message.text == "❌ Отмена":
            return await cancel(update, context)

        # Сохраняем название оборудования
        context.user_data['equipment'] = update.message.text
        
        # Просим ввести количество
        await update.message.reply_text(
            "Пожалуйста, введите количество (целое число больше нуля):"
        )
        return QUANTITY
        
    except Exception as e:
        logger.error(f"Ошибка в equipment: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
        return ConversationHandler.END

# Обработчик ввода количества
async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "❌ Отмена":
            return await cancel(update, context)

        # Проверяем, что введено число
        try:
            quantity = int(update.message.text)
            if quantity <= 0:
                await update.message.reply_text(
                    "Пожалуйста, введите корректное количество (целое число больше нуля):"
                )
                return QUANTITY
            context.user_data['quantity'] = quantity
            await update.message.reply_text(
                "Теперь опишите, пожалуйста, суть заявки:"
            )
            return DESCRIPTION
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите число (например: 5, 10, 100):"
            )
            return QUANTITY
            
    except Exception as e:
        logger.error(f"Ошибка в quantity: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
        return ConversationHandler.END

# Обработчик ввода описания
async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "❌ Отмена":
            return await cancel(update, context)

        # Сохраняем описание
        context.user_data['description'] = update.message.text
        
        # Показываем кнопки выбора приоритета
        keyboard = [
            ["🔴 Высокий", "🟡 Средний"],
            ["🟢 Низкий", "❌ Отмена"]
        ]
        await update.message.reply_text(
            "Выберите приоритет заявки: 🔴 Высокий, 🟡 Средний или 🟢 Низкий.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PRIORITY
        
    except Exception as e:
        logger.error(f"Ошибка в description: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
        return ConversationHandler.END

# Обработчик выбора приоритета
async def priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "❌ Отмена":
            return await cancel(update, context)

        # Преобразуем текст приоритета в значение для базы данных
        priority_map = {
            "🔴 Высокий": "high",
            "🟡 Средний": "medium",
            "🟢 Низкий": "low"
        }

        if update.message.text not in priority_map:
            await update.message.reply_text(
                "Пожалуйста, выберите приоритет из предложенных вариантов."
            )
            return PRIORITY

        context.user_data['priority'] = priority_map[update.message.text]

        # Сохраняем заявку в базу данных
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
            if not user:
                await update.message.reply_text("Пользователь не найден в системе.")
                return

            # Создаем новую заявку
            request = Request(
                user_id=user.id,
                equipment_name=context.user_data['equipment'],
                quantity=context.user_data['quantity'],
                description=context.user_data['description'],
                priority=context.user_data['priority'],
                status='new'
            )
            session.add(request)
            session.commit()
            
            # Сохраняем ID заявки до закрытия сессии
            request_id = request.id
            equipment_name = request.equipment_name
            quantity = request.quantity
            priority_value = request.priority

            # Очищаем данные
            context.user_data.clear()

            await update.message.reply_text(
                "Ваша заявка успешно создана и появится в списке активных заявок.",
                reply_markup=get_main_menu_keyboard(user.is_admin)
            )
            return ConversationHandler.END
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка в priority: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении заявки. Попробуйте позже.")
        return ConversationHandler.END

# Обработчик отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = None
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        # Очищаем данные
        context.user_data.clear()

        await update.message.reply_text(
            "Создание заявки отменено. Вы можете начать заново в любое время.",
            reply_markup=get_main_menu_keyboard(user.is_admin if user else False)
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в cancel: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
        return ConversationHandler.END
    finally:
        session.close()

# Обработчик просмотра активных заявок (не выполненных и не удаленных)
async def list_active_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = None
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text(
                "У вас нет активных заявок.",
                reply_markup=get_main_menu_keyboard(user.is_admin)
            )
            return

        # Получаем только активные заявки (не выполненные, не отмененные, не удаленные)
        query = session.query(Request).filter(
            Request.is_deleted == False,
            Request.status.in_(['new', 'in_progress'])
        )
        requests = query.order_by(Request.created_at.desc()).all()

        if not requests:
            await update.message.reply_text(
                "Активных заявок не найдено. Если вы администратор, это значит, что все заявки выполнены или отменены. Если вы сотрудник, у вас пока нет активных заявок.",
                reply_markup=get_main_menu_keyboard(user.is_admin)
            )
            return

        # Отправляем каждую заявку отдельным сообщением с кнопками
        for request in requests:
            message = format_request_details(request)
            keyboard = []
            # Кнопки для всех работников (не только для своих заявок)
            if not user.is_admin:
                if request.status == 'new':
                    keyboard.append([
                        InlineKeyboardButton("✅ Принять", callback_data=f"complete_{request.id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"cancel_{request.id}")
                    ])
                elif request.status == 'in_progress':
                    keyboard.append([
                        InlineKeyboardButton("✅ Принять", callback_data=f"complete_{request.id}")
                    ])
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                reply_markup = None
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Ошибка в list_active_requests: {str(e)}")
        await update.message.reply_text(
            "Произошла ошибка при получении списка заявок. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user.is_admin if user else False)
        )
    finally:
        session.close()

# Обработчик просмотра выполненных заявок
async def show_completed_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user or not user.is_admin:
            await update.message.reply_text(
                "Доступ к выполненным заявкам разрешён только администраторам.",
                reply_markup=get_main_menu_keyboard(False)
            )
            return

        # Получаем только выполненные заявки за последние 30 дней
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        requests = session.query(Request).filter(
            Request.status == 'completed',
            Request.is_deleted == False,
            Request.completed_at >= thirty_days_ago
        ).order_by(Request.completed_at.desc()).all()

        if not requests:
            await update.message.reply_text(
                "Выполненных заявок за последние 30 дней не найдено.",
                reply_markup=get_main_menu_keyboard(True)
            )
            return

        for req in requests:
            # Убеждаемся, что даты имеют timezone
            if req.completed_at and req.completed_at.tzinfo is None:
                req.completed_at = req.completed_at.replace(tzinfo=timezone.utc)
            
            days_left = 30 - (datetime.now(timezone.utc) - req.completed_at).days if req.completed_at else 0
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(req.priority, '⚪️')

            # Информация о том, кто принял заявку
            completed_by_info = ""
            if req.completed_by:
                completed_by_info = f"👤 Принял: @{req.completed_by.username}" if req.completed_by.username else f"👤 Принял: ID {req.completed_by.telegram_id}"
            else:
                completed_by_info = "👤 Принял: Неизвестно"

            message = (
                f"✅ *Выполненная заявка #{req.id}*\n\n"
                f"📦 Оборудование: {req.equipment_name}\n"
                f"🔢 Количество: {req.quantity}\n"
                f"📝 Описание: {req.description}\n"
                f"{priority_emoji} Приоритет: {req.priority}\n"
                f"📅 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"✅ Выполнена: {req.completed_at.strftime('%d.%m.%Y %H:%M') if req.completed_at else 'Не указано'}\n"
                f"{completed_by_info}\n"
                f"⏳ Автоудаление через: {days_left} дней\n"
            )
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Восстановить", callback_data=f"restore_completed_{req.id}"),
                    InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_completed_{req.id}")
                ]
            ]
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        logger.error(f"Ошибка в show_completed_requests: {e}")
        await update.message.reply_text("Произошла ошибка при получении выполненных заявок. Попробуйте позже.")
    finally:
        session.close()

# Обработчик просмотра отмененных заявок
async def show_cancelled_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user or not user.is_admin:
            await update.message.reply_text(
                "Доступ к отменённым заявкам разрешён только администраторам.",
                reply_markup=get_main_menu_keyboard(False)
            )
            return

        # Получаем отмененные заявки за последние 30 дней
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        requests = session.query(Request).filter(
            Request.status == 'cancelled',
            Request.updated_at >= thirty_days_ago
        ).order_by(Request.updated_at.desc()).all()

        if not requests:
            await update.message.reply_text(
                "Отменённых заявок за последние 30 дней не найдено.",
                reply_markup=get_main_menu_keyboard(True)
            )
            return

        for req in requests:
            # Убеждаемся, что даты имеют timezone
            if req.updated_at and req.updated_at.tzinfo is None:
                req.updated_at = req.updated_at.replace(tzinfo=timezone.utc)
            
            days_left = 30 - (datetime.now(timezone.utc) - req.updated_at).days if req.updated_at else 0
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(req.priority, '⚪️')

            # Информация о том, кто отклонил/отменил заявку
            cancelled_by_info = ""
            if req.cancelled_by:
                cancelled_by_info = f"👤 Отклонил/отменил: @{req.cancelled_by.username}" if req.cancelled_by.username else f"👤 Отклонил/отменил: ID {req.cancelled_by.telegram_id}"
            else:
                cancelled_by_info = "👤 Отклонил/отменил: Неизвестно"

            message = (
                f"❌ *Отмененная заявка #{req.id}*\n\n"
                f"📦 Оборудование: {req.equipment_name}\n"
                f"🔢 Количество: {req.quantity}\n"
                f"📝 Описание: {req.description}\n"
                f"{priority_emoji} Приоритет: {req.priority}\n"
                f"📅 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"❌ Отменена: {req.updated_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"{cancelled_by_info}\n"
                f"⏳ Автоудаление через: {days_left} дней\n"
            )
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Восстановить", callback_data=f"restore_{req.id}"),
                    InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_now_{req.id}")
                ]
            ]
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        logger.error(f"Ошибка в show_cancelled_requests: {e}")
        await update.message.reply_text("Произошла ошибка при получении отменённых заявок. Попробуйте позже.")
    finally:
        session.close()

# Обработчик нажатий на кнопки меню
async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "📝 Создать заявку":
            return await create_request(update, context)
        elif update.message.text == "📋 Активные заявки":
            return await list_active_requests(update, context)
        elif update.message.text == "📋 Мои заявки":
            return await list_active_requests(update, context)
        elif update.message.text == "✅ Выполненные заявки":
            return await show_completed_requests(update, context)
        elif update.message.text == "❌ Отмененные заявки":
            return await show_cancelled_requests(update, context)
        elif update.message.text == "❓ Помощь":
            return await help_command(update, context)
        else:
            await update.message.reply_text(
                "Команда не распознана. Пожалуйста, используйте меню или кнопку '❓ Помощь'."
            )
    except Exception as e:
        logger.error(f"Ошибка в handle_menu_click: {e}")
        await update.message.reply_text("Произошла ошибка при обработке команды. Попробуйте позже.")

# Обработчик для inline кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
            if not user:
                await query.edit_message_text("Пользователь не найден в системе.")
                return

            # Разбираем callback_data
            parts = query.data.split('_')
            action = parts[0]
            
            if action == 'complete':
                request_id = int(parts[1])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Отмечаем заявку как выполненную
                request.status = 'completed'
                request.completed_at = datetime.now(timezone.utc)
                request.completed_by_id = user.id
                session.commit()

                # Формируем сообщение с информацией о том, кто принял
                action_info = f"👤 Принял: @{user.username}" if user.username else f"👤 Принял: ID {user.telegram_id}"
                
                await query.edit_message_text(
                    f"✅ *Заявка #{request.id} принята!*\n\n"
                    f"📦 Оборудование: {request.equipment_name}\n"
                    f"🔢 Количество: {request.quantity}\n"
                    f"✅ Статус изменен на 'Принято'\n"
                    f"📅 Дата принятия: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n"
                    f"{action_info}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'reject':
                if not user.is_admin:
                    await query.edit_message_text("🔒 Доступ ограничен\n\nУ вас нет прав для отклонения заявок.")
                    return
                    
                request_id = int(parts[1])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Отклоняем заявку (переводим в статус отмененных)
                request.status = 'cancelled'
                request.cancelled_by_id = user.id
                session.commit()

                # Формируем сообщение с информацией о том, кто отклонил
                action_info = f"👤 Отклонил: @{user.username}" if user.username else f"👤 Отклонил: ID {user.telegram_id}"

                await query.edit_message_text(
                    f"❌ *Заявка #{request.id} отклонена*\n\n"
                    f"📦 Оборудование: {request.equipment_name}\n"
                    f"🔢 Количество: {request.quantity}\n"
                    f"❌ Статус изменен на 'Отклонено'\n"
                    f"📅 Дата отклонения: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n"
                    f"{action_info}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'cancel':
                request_id = int(parts[1])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                request.status = 'cancelled'
                request.cancelled_by_id = user.id
                session.commit()

                # Формируем сообщение с информацией о том, кто отменил
                action_info = f"👤 Отменил: @{user.username}" if user.username else f"👤 Отменил: ID {user.telegram_id}"

                await query.edit_message_text(
                    f"❌ *Заявка #{request.id} отменена*\n\n"
                    f"📦 Оборудование: {request.equipment_name}\n"
                    f"🔢 Количество: {request.quantity}\n"
                    f"❌ Статус изменен на 'Отменено'\n"
                    f"📅 Дата отмены: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n"
                    f"{action_info}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'restore' and len(parts) > 1 and parts[1] == 'completed':
                if not user.is_admin:
                    await query.edit_message_text("🔒 Доступ ограничен\n\nУ вас нет прав для выполнения этого действия.")
                    return
                    
                request_id = int(parts[2])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Восстанавливаем выполненную заявку в статус "новые"
                request.status = 'new'
                request.completed_at = None
                request.completed_by_id = None
                session.commit()

                await query.edit_message_text(
                    f"🔄 *Заявка #{request.id} восстановлена*\n\n"
                    f"📦 Оборудование: {request.equipment_name}\n"
                    f"🔢 Количество: {request.quantity}\n"
                    f"🆕 Статус изменен на 'Новые'\n"
                    f"📅 Дата восстановления: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'restore':
                if not user.is_admin:
                    await query.edit_message_text("🔒 Доступ ограничен\n\nУ вас нет прав для выполнения этого действия.")
                    return
                    
                request_id = int(parts[1])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Восстанавливаем заявку из отмененных
                request.status = 'new'
                request.cancelled_by_id = None
                session.commit()

                await query.edit_message_text(
                    f"🔄 *Заявка #{request.id} восстановлена*\n\n"
                    f"📦 Оборудование: {request.equipment_name}\n"
                    f"🔢 Количество: {request.quantity}\n"
                    f"🆕 Статус изменен на 'Новые'\n"
                    f"📅 Дата восстановления: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'delete' and len(parts) > 1 and parts[1] == 'completed':
                if not user.is_admin:
                    await query.edit_message_text("🔒 Доступ ограничен\n\nУдаление доступно только администраторам.")
                    return
                    
                request_id = int(parts[2])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Удаляем выполненную заявку навсегда
                equipment_name = request.equipment_name
                session.delete(request)
                session.commit()

                await query.edit_message_text(
                    f"🗑 *Выполненная заявка #{request_id} удалена*\n\n"
                    f"📦 Оборудование: {equipment_name}\n"
                    f"🗑 Заявка удалена навсегда из системы\n"
                    f"📅 Дата удаления: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
                return

            elif action == 'delete' and len(parts) > 1 and parts[1] == 'now':
                if not user.is_admin:
                    await query.edit_message_text("🔒 Доступ ограничен\n\nУдаление доступно только администраторам.")
                    return
                    
                request_id = int(parts[2])
                request = session.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text("Заявка не найдена в системе.")
                    return

                # Удаляем заявку навсегда
                equipment_name = request.equipment_name
                session.delete(request)
                session.commit()

                await query.edit_message_text(
                    f"�� *Заявка #{request_id} удалена*\n\n"
                    f"📦 Оборудование: {equipment_name}\n"
                    f"🗑 Заявка удалена навсегда из системы\n"
                    f"📅 Дата удаления: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}",
                    parse_mode='Markdown'
                )
                return

            else:
                await query.edit_message_text("😔 Неизвестное действие. Пожалуйста, попробуйте еще раз.")
                return

        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")
        await query.edit_message_text("😔 Произошла ошибка при выполнении действия. Пожалуйста, попробуйте позже.")

# Вспомогательные функции для форматирования
def format_datetime(dt):
    if dt:
        # Убеждаемся, что дата имеет timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%d.%m.%Y %H:%M")
    return "Не указано"

def get_status_emoji(status):
    status_emojis = {
        'new': '🆕',
        'in_progress': '⏳',
        'completed': '✅',
        'cancelled': '❌'
    }
    return status_emojis.get(status, '❓')

def get_priority_emoji(priority):
    priority_emojis = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return priority_emojis.get(priority, '⚪️')

def format_request_details(request):
    # Получаем эмодзи для статуса и приоритета
    status_emoji = get_status_emoji(request.status)
    priority_emoji = get_priority_emoji(request.priority)
    
    # Форматируем статус для отображения
    status_display = {
        'new': 'Новые',
        'in_progress': 'В процессе',
        'completed': 'Выполнено',
        'cancelled': 'Отменено'
    }.get(request.status, request.status)
    
    # Форматируем приоритет для отображения
    priority_display = {
        'high': 'Высокий',
        'medium': 'Средний',
        'low': 'Низкий'
    }.get(request.priority, request.priority)
    
    # Информация о том, кто принял или отклонил заявку
    action_info = ""
    if request.status == 'completed' and request.completed_by:
        action_info = f"\n👤 Принял: @{request.completed_by.username}" if request.completed_by.username else f"\n👤 Принял: ID {request.completed_by.telegram_id}"
    elif request.status == 'cancelled' and request.cancelled_by:
        action_info = f"\n👤 Отклонил/отменил: @{request.cancelled_by.username}" if request.cancelled_by.username else f"\n👤 Отклонил/отменил: ID {request.cancelled_by.telegram_id}"
    
    return (
        f"📋 *Заявка #{request.id}*\n\n"
        f"📦 *Оборудование:* {request.equipment_name}\n"
        f"🔢 *Количество:* {request.quantity}\n"
        f"📝 *Описание:* {request.description}\n"
        f"⚡️ *Приоритет:* {priority_emoji} {priority_display}\n"
        f"📊 *Статус:* {status_emoji} {status_display}\n\n"
        f"🕒 *Создано:* {format_datetime(request.created_at)}\n"
        f"📅 *Обновлено:* {format_datetime(request.updated_at)}\n"
        f"✅ *Выполнено:* {format_datetime(request.completed_at)}\n"
        f"📌 *Заметки:* {request.notes if request.notes else 'Нет заметок'}{action_info}"
    )

# Функция для автоматического удаления старых отмененных и выполненных заявок
def cleanup_old_requests():
    try:
        session = Session()
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        # Находим отмененные заявки старше 30 дней
        old_cancelled_requests = session.query(Request).filter(
            Request.status == 'cancelled',
            Request.updated_at < thirty_days_ago
        ).all()
        # Находим выполненные заявки старше 30 дней
        old_completed_requests = session.query(Request).filter(
            Request.status == 'completed',
            Request.completed_at < thirty_days_ago
        ).all()
        for request in old_cancelled_requests:
            session.delete(request)
        for request in old_completed_requests:
            session.delete(request)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Ошибка при автоматической очистке старых заявок: {e}")

# Основная функция запуска бота
def main():
    try:
        # Создаем таблицы в базе данных
        Base.metadata.create_all(engine)
        
        # Очищаем старые отмененные и выполненные заявки при запуске
        cleanup_old_requests()
        
        # Создаем бота
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("cancel", cancel))

        # Обработчик создания заявки
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📝 Создать заявку$"), create_request)],
            states={
                EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment)],
                QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
                PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, priority)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        application.add_handler(conv_handler)

        # Обработчики меню
        application.add_handler(MessageHandler(filters.Regex("^(📋 Активные заявки|📋 Мои заявки)$"), list_active_requests))
        application.add_handler(MessageHandler(filters.Regex("^✅ Выполненные заявки$"), show_completed_requests))
        application.add_handler(MessageHandler(filters.Regex("^❌ Отмененные заявки$"), show_cancelled_requests))
        application.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), help_command))

        # Обработчик callback-запросов
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Запускаем бота
        print("🤖 Бот системы управления заявками запущен!")
        print("📊 Система готова к работе")
        print("💡 Для остановки нажмите Ctrl+C")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main: {e}")
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

# Запускаем бота
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1) 