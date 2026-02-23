#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📢 Telegram бот для автопостинга в каналы
⏰ Поддержка новосибирского времени (NSK, UTC+7)
🗑 Автоудаление постов (минимум 1 день)
"""

import asyncio
import logging
import json
import os
import re
import html
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import uuid4

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from dotenv import load_dotenv

# Загрузка переменных окружения (только для токена)
load_dotenv()

# ==================== КОНФИГУРАЦИЯ ====================

class Config:
    """Конфигурация бота"""
    
    # Токен бота из .env файла
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # ID канала для публикации (УКАЗАТЬ СВОЙ!)
    # Для публичного канала: @channel_username
    # Для приватного канала: -1001234567890 (число с минусом)
    CHANNEL_ID = "@maslyanino"  # ⚠️ ИЗМЕНИТЕ НА СВОЙ КАНАЛ!
    
    # ID администратора (УКАЗАТЬ СВОЙ!)
    # Кому будут приходить уведомления об ошибках
    # Можно узнать у @userinfobot
    ADMIN_ID = 1174432700  # ⚠️ ИЗМЕНИТЕ НА СВОЙ ID!
    
    # Часовой пояс
    NSK_TIMEZONE = pytz.timezone('Asia/Novosibirsk')
    
    # Файл для хранения постов
    DATA_FILE = "scheduled_posts.json"
    
    # Настройки логирования
    LOG_LEVEL = logging.INFO
    
    # Настройки удаления
    MIN_DELETE_DAYS = 1
    MAX_DELETE_DAYS = 30
    
    @classmethod
    def validate(cls):
        """Проверка конфигурации"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не установлен в .env файле!")
        
        if not cls.CHANNEL_ID:
            errors.append("❌ CHANNEL_ID не указан в коде!")
        elif cls.CHANNEL_ID == "@your_channel_username":
            errors.append("❌ CHANNEL_ID не изменен! Укажите свой канал в коде.")
        
        if not cls.ADMIN_ID:
            errors.append("❌ ADMIN_ID не указан в коде!")
        elif cls.ADMIN_ID == 123456789:
            errors.append("❌ ADMIN_ID не изменен! Укажите свой ID в коде.")
        
        if errors:
            error_text = "\n".join(errors)
            raise ValueError(f"Ошибки конфигурации:\n{error_text}")
        
        # Логируем информацию о конфигурации
        logging.info(f"✅ Бот токен: {cls.BOT_TOKEN[:10]}...")
        logging.info(f"📢 Канал: {cls.CHANNEL_ID}")
        logging.info(f"👤 Администратор: {cls.ADMIN_ID}")

# ==================== МОДЕЛИ ДАННЫХ ====================

class PostStatus(Enum):
    """Статусы поста"""
    SCHEDULED = "📅 Запланирован"
    PUBLISHED = "✅ Опубликован"
    DELETED = "🗑 Удален"
    FAILED = "❌ Ошибка"

@dataclass
class ScheduledPost:
    """Класс запланированного поста"""
    id: str
    channel_id: str
    content: str
    publish_time: str
    delete_after_days: Optional[int] = None
    message_id: Optional[int] = None
    status: str = PostStatus.SCHEDULED.value
    created_at: str = None
    created_by: int = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(Config.NSK_TIMEZONE).isoformat()
    
    @property
    def publish_time_dt(self) -> datetime:
        """Время публикации как datetime"""
        return datetime.fromisoformat(self.publish_time)
    
    @property
    def delete_time(self) -> Optional[datetime]:
        """Время удаления как datetime"""
        if self.delete_after_days:
            return self.publish_time_dt + timedelta(days=self.delete_after_days)
        return None
    
    @property
    def is_expired(self) -> bool:
        """Проверка, истек ли срок поста"""
        now = datetime.now(Config.NSK_TIMEZONE)
        return self.publish_time_dt < now
    
    def time_until_publish(self) -> str:
        """Форматированное время до публикации"""
        now = datetime.now(Config.NSK_TIMEZONE)
        diff = self.publish_time_dt - now
        
        if diff.total_seconds() < 0:
            return "⏰ Время публикации прошло"
        
        return format_timedelta(diff)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return asdict(self)

# ==================== ХРАНИЛИЩЕ ДАННЫХ ====================

class PostStorage:
    """Хранилище постов с автосохранением"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.posts: Dict[str, ScheduledPost] = {}
        self.load()
    
    def load(self):
        """Загрузка из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for post_id, post_data in data.items():
                        self.posts[post_id] = ScheduledPost(**post_data)
                logging.info(f"📂 Загружено {len(self.posts)} постов")
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки: {e}")
    
    def save(self):
        """Сохранение в файл"""
        try:
            data = {pid: p.to_dict() for pid, p in self.posts.items()}
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения: {e}")
    
    def add(self, post: ScheduledPost) -> str:
        """Добавление поста"""
        self.posts[post.id] = post
        self.save()
        return post.id
    
    def update(self, post_id: str, **kwargs):
        """Обновление поста"""
        if post_id in self.posts:
            for key, value in kwargs.items():
                if hasattr(self.posts[post_id], key):
                    setattr(self.posts[post_id], key, value)
            self.save()
    
    def get(self, post_id: str) -> Optional[ScheduledPost]:
        """Получение поста по ID"""
        return self.posts.get(post_id)
    
    def get_active(self) -> List[ScheduledPost]:
        """Получение активных постов"""
        now = datetime.now(Config.NSK_TIMEZONE)
        return [
            p for p in self.posts.values()
            if p.status == PostStatus.SCHEDULED.value and p.publish_time_dt > now
        ]
    
    def get_all(self) -> List[ScheduledPost]:
        """Получение всех постов"""
        return list(self.posts.values())
    
    def get_by_user(self, user_id: int) -> List[ScheduledPost]:
        """Получение постов конкретного пользователя"""
        return [p for p in self.posts.values() if p.created_by == user_id]
    
    def get_history(self, limit: int = 10) -> List[ScheduledPost]:
        """Получение истории постов"""
        return sorted(
            self.posts.values(),
            key=lambda x: x.publish_time_dt,
            reverse=True
        )[:limit]
    
    def remove(self, post_id: str):
        """Удаление поста"""
        if post_id in self.posts:
            del self.posts[post_id]
            self.save()

# ==================== УТИЛИТЫ ====================

def escape_html(text: str) -> str:
    """Экранирование HTML специальных символов"""
    return html.escape(text)

def format_timedelta(delta: timedelta) -> str:
    """Форматирование временного интервала"""
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} {pluralize(days, 'день', 'дня', 'дней')}")
    if hours > 0:
        parts.append(f"{hours} {pluralize(hours, 'час', 'часа', 'часов')}")
    if minutes > 0 and days == 0:
        parts.append(f"{minutes} {pluralize(minutes, 'минута', 'минуты', 'минут')}")
    
    return " ".join(parts) if parts else "менее минуты"

def pluralize(n: int, one: str, few: str, many: str) -> str:
    """Склонение существительных после числительных"""
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return few
    else:
        return many

def parse_time(input_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Парсинг времени из строки
    Возвращает (datetime, сообщение об ошибке)
    """
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    input_str = input_str.lower().strip()
    
    # Шаблоны для регулярных выражений
    patterns = [
        # Абсолютное время сегодня: "14:30", "в 14:30", "сегодня 14:30"
        (r'^(?:в|сегодня)?\s*(\d{1,2}):(\d{2})$', 'today'),
        
        # Завтра: "завтра 14:30", "tomorrow 14:30"
        (r'^завтра\s*(\d{1,2}):(\d{2})$', 'tomorrow'),
        (r'^tomorrow\s*(\d{1,2}):(\d{2})$', 'tomorrow'),
        
        # Дата: "15.01.2024 14:30", "2024-01-15 14:30"
        (r'^(\d{1,2})[.](\d{1,2})[.](\d{4})\s+(\d{1,2}):(\d{2})$', 'date_dot'),
        (r'^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$', 'date_dash'),
        
        # Относительное время: "1ч", "2ч", "3часа", "5д", "7дней"
        (r'^(\d+)\s*ч(?:ас(?:а|ов)?)?$', 'hours'),
        (r'^(\d+)\s*д(?:ень|ня|ней)?$', 'days'),
        (r'^(\d+)\s*м(?:инут(?:а|ы)?)?$', 'minutes'),
    ]
    
    for pattern, type_ in patterns:
        match = re.match(pattern, input_str)
        if not match:
            continue
        
        try:
            if type_ == 'today':
                hours, minutes = map(int, match.groups())
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    return None, "❌ Неверное время (часы: 0-23, минуты: 0-59)"
                
                target = Config.NSK_TIMEZONE.localize(
                    datetime.combine(now_nsk.date(), datetime.min.time().replace(hour=hours, minute=minutes))
                )
                
                if target < now_nsk:
                    target += timedelta(days=1)
                    return target, "⏰ Время уже прошло, пост запланирован на завтра"
                return target, None
            
            elif type_ == 'tomorrow':
                hours, minutes = map(int, match.groups())
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    return None, "❌ Неверное время"
                
                target = Config.NSK_TIMEZONE.localize(
                    datetime.combine(now_nsk.date() + timedelta(days=1), 
                                   datetime.min.time().replace(hour=hours, minute=minutes))
                )
                return target, None
            
            elif type_ in ['date_dot', 'date_dash']:
                if type_ == 'date_dot':
                    day, month, year, hours, minutes = map(int, match.groups())
                else:
                    year, month, day, hours, minutes = map(int, match.groups())
                
                if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 2024):
                    return None, "❌ Неверная дата"
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    return None, "❌ Неверное время"
                
                target = Config.NSK_TIMEZONE.localize(
                    datetime(year, month, day, hours, minutes)
                )
                
                if target < now_nsk:
                    return None, "❌ Дата не может быть в прошлом"
                return target, None
            
            elif type_ == 'hours':
                hours = int(match.group(1))
                if hours > 168:
                    return None, "❌ Максимум 168 часов (7 дней)"
                return now_nsk + timedelta(hours=hours), None
            
            elif type_ == 'days':
                days = int(match.group(1))
                if days > 30:
                    return None, "❌ Максимум 30 дней"
                return now_nsk + timedelta(days=days), None
            
            elif type_ == 'minutes':
                minutes = int(match.group(1))
                if minutes > 1440:
                    return None, "❌ Максимум 1440 минут (24 часа)"
                return now_nsk + timedelta(minutes=minutes), None
                
        except ValueError as e:
            return None, f"❌ Ошибка парсинга: {e}"
    
    return None, "❌ Неверный формат времени.\nИспользуйте:\n• 14:30 (сегодня/завтра)\n• завтра 14:30\n• 15.01.2024 14:30\n• 2ч, 5д, 30м"

def format_post_info(post: ScheduledPost, detailed: bool = False) -> str:
    """Форматирование информации о посте (без HTML разметки)"""
    publish_time = post.publish_time_dt
    time_str = publish_time.strftime("%d.%m.%Y %H:%M")
    
    if detailed:
        info = [
            f"🆔 ID: {post.id}",
            f"📅 Публикация: {time_str} NSK",
            f"⏳ До публикации: {post.time_until_publish()}",
        ]
        
        if post.delete_after_days:
            delete_time = post.delete_time.strftime("%d.%m.%Y %H:%M")
            info.append(f"🗑 Удаление: через {post.delete_after_days} дн. ({delete_time} NSK)")
        else:
            info.append(f"🗑 Удаление: не требуется")
        
        # Экранируем содержимое поста
        escaped_content = escape_html(post.content[:200])
        info.append(f"📝 Текст:\n{escaped_content}{'...' if len(post.content) > 200 else ''}")
        info.append(f"📊 Статус: {post.status}")
    else:
        info = [
            f"🆔 {post.id[:8]}...",
            f"📅 {time_str}",
            f"⏳ {post.time_until_publish()}",
        ]
        
        if post.delete_after_days:
            info.append(f"🗑 {post.delete_after_days} дн.")
    
    return "\n".join(info)

async def notify_admin(message: str):
    """Отправка уведомления администратору"""
    if Config.ADMIN_ID:
        try:
            await bot.send_message(Config.ADMIN_ID, message)
        except Exception as e:
            logging.error(f"❌ Не удалось отправить уведомление админу: {e}")

# ==================== СОСТОЯНИЯ FSM ====================

class PostStates(StatesGroup):
    """Состояния создания поста"""
    waiting_for_content = State()
    waiting_for_publish_time = State()
    waiting_for_delete_days = State()
    confirming = State()

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Новый пост", callback_data="new_post"),
        InlineKeyboardButton("📋 Список", callback_data="list_posts")
    )
    keyboard.add(
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
        InlineKeyboardButton("🗑 Удалить пост", callback_data="delete_post")
    )
    
    # Добавляем кнопку статистики только для админа
    if Config.ADMIN_ID:
        keyboard.add(InlineKeyboardButton("📊 Статистика", callback_data="stats"))
    
    return keyboard

def get_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Быстрые варианты времени
    times = [
        ("⏰ Через 1ч", "1ч"),
        ("⏰ Через 2ч", "2ч"),
        ("⏰ Через 3ч", "3ч"),
        ("📅 Сегодня 18:00", "сегодня 18:00"),
        ("📅 Завтра 10:00", "завтра 10:00"),
        ("📅 Завтра 12:00", "завтра 12:00"),
    ]
    
    for text, callback in times:
        keyboard.insert(InlineKeyboardButton(text, callback_data=f"time_{callback}"))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_content"))
    return keyboard

def get_delete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени удаления"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    for days in [1, 3, 7, 14, 21, 30]:
        keyboard.insert(InlineKeyboardButton(
            f"🗑 {days} {pluralize(days, 'день', 'дня', 'дней')}",
            callback_data=f"delete_{days}"
        ))
    
    keyboard.add(InlineKeyboardButton("🚫 Не удалять", callback_data="delete_0"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_time"))
    
    return keyboard

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Опубликовать", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")
    )
    return keyboard

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

# Проверка конфигурации
Config.validate()

# Инициализация бота
bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Настройка логирования
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Хранилище постов
post_storage = PostStorage(Config.DATA_FILE)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    welcome_text = f"""
🌟 Добро пожаловать в бота для автопостинга!

Я помогу вам планировать посты в канале с учетом новосибирского времени (NSK, UTC+7).

📢 Канал для публикации: {escape_html(str(Config.CHANNEL_ID))}
👤 Ваш ID: {user_id}
{"👑 Роль: Администратор" if is_admin else "👤 Роль: Пользователь"}

Доступные команды:
• /post - создать новый пост
• /list - список запланированных постов
• /delete &lt;id&gt; - удалить запланированный пост
• /help - подробная справка
• /cancel - отменить текущее действие

💡 Быстрые действия: используйте кнопки ниже
    """
    
    await message.reply(welcome_text, reply_markup=get_main_keyboard())

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Команда /help"""
    help_text = f"""
❓ Справка по использованию

📝 Создание поста:
1. Нажмите "Новый пост" или отправьте /post
2. Введите текст поста (можно использовать HTML)
3. Укажите время публикации
4. Выберите через сколько дней удалить (минимум 1 день)
5. Подтвердите публикацию

⏰ Форматы времени:
• 14:30 - сегодня в 14:30 (или завтра если прошло)
• завтра 10:00 - завтра в 10:00
• 15.01.2024 14:30 - конкретная дата
• 2ч - через 2 часа
• 3д - через 3 дня
• 30м - через 30 минут

🗑 Удаление постов:
• Минимальный срок: {Config.MIN_DELETE_DAYS} день
• Максимальный срок: {Config.MAX_DELETE_DAYS} дней
• Можно выбрать из предложенных вариантов

📋 Управление:
• /list - показать все запланированные посты
• /delete &lt;id&gt; - удалить пост по ID
• /cancel - отменить текущее действие

🕐 Часовой пояс: Новосибирск (NSK, UTC+7)
📢 Канал: {escape_html(str(Config.CHANNEL_ID))}
    """
    
    await message.reply(help_text, reply_markup=get_main_keyboard())

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    """Команда /post - создание нового поста"""
    await message.reply(
        "📝 Отправьте текст поста\n\n"
        "Можно использовать HTML-разметку:\n"
        "• &lt;b&gt;жирный&lt;/b&gt;\n"
        "• &lt;i&gt;курсив&lt;/i&gt;\n"
        "• &lt;code&gt;код&lt;/code&gt;\n"
        "• &lt;a href='url'&gt;ссылка&lt;/a&gt;\n\n"
        "Или нажмите кнопку ниже для отмены",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        )
    )
    await PostStates.waiting_for_content.set()

@dp.message_handler(state=PostStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    """Обработка текста поста"""
    if not message.text:
        await message.reply("❌ Отправьте текстовое сообщение")
        return
    
    # Сохраняем оригинальный HTML
    await state.update_data(content=message.html_text)
    await message.reply(
        "⏰ Укажите время публикации\n\n"
        "Например:\n"
        "• 14:30 - сегодня\n"
        "• завтра 10:00 - завтра\n"
        "• 15.01.2024 14:30 - дата\n"
        "• 2ч - через 2 часа\n"
        "• 3д - через 3 дня",
        reply_markup=get_time_keyboard()
    )
    await PostStates.waiting_for_publish_time.set()

@dp.message_handler(state=PostStates.waiting_for_publish_time)
async def process_publish_time(message: types.Message, state: FSMContext):
    """Обработка времени публикации"""
    publish_time, error = parse_time(message.text)
    
    if error:
        await message.reply(error + "\n\nПопробуйте снова:", reply_markup=get_time_keyboard())
        return
    
    await state.update_data(publish_time=publish_time.isoformat())
    
    # Показываем предупреждение если время было скорректировано
    warning = f"\n{error}" if error else ""
    
    await message.reply(
        f"🗑 Через сколько дней удалить пост?\n"
        f"(минимум {Config.MIN_DELETE_DAYS} день, максимум {Config.MAX_DELETE_DAYS} дней){warning}",
        reply_markup=get_delete_keyboard()
    )
    await PostStates.waiting_for_delete_days.set()

@dp.callback_query_handler(lambda c: c.data.startswith('time_'), state=PostStates.waiting_for_publish_time)
async def process_time_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени через кнопки"""
    time_str = callback.data.replace('time_', '')
    publish_time, error = parse_time(time_str)
    
    if error and "уже прошло" not in error:
        await callback.answer(error, show_alert=True)
        return
    
    await state.update_data(publish_time=publish_time.isoformat())
    
    warning = f"\n{error}" if error else ""
    await callback.message.edit_text(
        f"🗑 Через сколько дней удалить пост?\n"
        f"(минимум {Config.MIN_DELETE_DAYS} день, максимум {Config.MAX_DELETE_DAYS} дней){warning}",
        reply_markup=get_delete_keyboard()
    )
    await PostStates.waiting_for_delete_days.set()
    await callback.answer()

@dp.message_handler(state=PostStates.waiting_for_delete_days)
async def process_delete_days(message: types.Message, state: FSMContext):
    """Обработка дней до удаления"""
    try:
        days = int(message.text)
        if days == 0:
            delete_days = None
        elif days < Config.MIN_DELETE_DAYS:
            await message.reply(f"❌ Минимальный срок удаления: {Config.MIN_DELETE_DAYS} день")
            return
        elif days > Config.MAX_DELETE_DAYS:
            await message.reply(f"❌ Максимальный срок удаления: {Config.MAX_DELETE_DAYS} дней")
            return
        else:
            delete_days = days
    except ValueError:
        await message.reply("❌ Введите число дней (0 - не удалять)")
        return
    
    await show_confirmation(message, state, delete_days)

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'), state=PostStates.waiting_for_delete_days)
async def process_delete_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора дней удаления через кнопки"""
    days = int(callback.data.replace('delete_', ''))
    delete_days = None if days == 0 else days
    
    await show_confirmation(callback.message, state, delete_days, is_callback=True)
    await callback.answer()

async def show_confirmation(message: types.Message, state: FSMContext, delete_days: Optional[int], is_callback: bool = False):
    """Показ подтверждения поста"""
    data = await state.get_data()
    content = data['content']
    publish_time = datetime.fromisoformat(data['publish_time'])
    
    # Создаем временный пост для предпросмотра
    temp_post = ScheduledPost(
        id="temp",
        channel_id=Config.CHANNEL_ID,
        content=content,
        publish_time=publish_time.isoformat(),
        delete_after_days=delete_days
    )
    
    preview = f"""
📝 Предпросмотр поста:

{escape_html(content[:500])}{'...' if len(content) > 500 else ''}

---
{format_post_info(temp_post, detailed=True)}

✅ Всё верно?
    """
    
    if is_callback:
        await message.edit_text(preview, reply_markup=get_confirmation_keyboard())
    else:
        await message.reply(preview, reply_markup=get_confirmation_keyboard())
    
    await state.update_data(delete_days=delete_days)
    await PostStates.confirming.set()

@dp.callback_query_handler(lambda c: c.data == 'confirm_yes', state=PostStates.confirming)
async def confirm_post(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение публикации"""
    data = await state.get_data()
    
    # Создаем пост
    post = ScheduledPost(
        id=str(uuid4())[:8],
        channel_id=Config.CHANNEL_ID,
        content=data['content'],
        publish_time=data['publish_time'],
        delete_after_days=data.get('delete_days'),
        created_by=callback.from_user.id
    )
    
    # Сохраняем
    post_id = post_storage.add(post)
    
    # Планируем публикацию
    asyncio.create_task(schedule_post_task(post))
    
    # Уведомляем админа о новом посте
    if Config.ADMIN_ID and Config.ADMIN_ID != callback.from_user.id:
        await notify_admin(
            f"📝 Новый пост создан пользователем {callback.from_user.id}\n\n"
            f"{format_post_info(post, detailed=True)}"
        )
    
    await callback.message.edit_text(
        f"✅ Пост успешно запланирован!\n\n"
        f"{format_post_info(post, detailed=True)}\n\n"
        f"🔔 Я уведомлю вас о публикации",
        reply_markup=get_main_keyboard()
    )
    
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'confirm_no', state=PostStates.confirming)
async def cancel_post(callback: types.CallbackQuery, state: FSMContext):
    """Отмена публикации"""
    await callback.message.edit_text(
        "❌ Создание поста отменено",
        reply_markup=get_main_keyboard()
    )
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_content')
async def back_to_content(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к вводу контента"""
    await callback.message.edit_text(
        "📝 Отправьте текст поста",
        reply_markup=None
    )
    await PostStates.waiting_for_content.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_time')
async def back_to_time(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    await callback.message.edit_text(
        "⏰ Укажите время публикации",
        reply_markup=get_time_keyboard()
    )
    await PostStates.waiting_for_publish_time.set()
    await callback.answer()

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    """Команда /list - список постов"""
    user_id = message.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    if is_admin:
        # Админ видит все посты
        active_posts = post_storage.get_active()
    else:
        # Пользователь видит только свои посты
        all_posts = post_storage.get_by_user(user_id)
        active_posts = [p for p in all_posts if p.status == PostStatus.SCHEDULED.value]
    
    if not active_posts:
        await message.reply(
            "📭 Нет запланированных постов\n\n"
            "Создайте новый пост с помощью /post",
            reply_markup=get_main_keyboard()
        )
        return
    
    response = ["📋 Запланированные посты:\n"]
    
    for i, post in enumerate(active_posts[:10], 1):
        response.append(f"{i}. {format_post_info(post)}")
    
    if len(active_posts) > 10:
        response.append(f"\n...и еще {len(active_posts) - 10} постов")
    
    response.append("\nИспользуйте /delete &lt;id&gt; для удаления")
    
    await message.reply("\n\n".join(response), reply_markup=get_main_keyboard())

@dp.message_handler(commands=['delete'])
async def cmd_delete(message: types.Message):
    """Команда /delete - удаление поста"""
    args = message.get_args()
    user_id = message.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    if not args:
        await message.reply(
            "❌ Укажите ID поста\n\n"
            "Пример: /delete abc123\n"
            "Список ID можно посмотреть в /list"
        )
        return
    
    post = post_storage.get(args)
    if not post:
        await message.reply(f"❌ Пост с ID {escape_html(args)} не найден")
        return
    
    # Проверяем права на удаление
    if not is_admin and post.created_by != user_id:
        await message.reply("❌ У вас нет прав на удаление этого поста")
        return
    
    if post.status != PostStatus.SCHEDULED.value:
        await message.reply(f"❌ Пост уже {post.status.lower()}")
        return
    
    # Удаляем пост
    post_storage.remove(args)
    
    # Уведомляем админа
    if is_admin and post.created_by != user_id:
        await notify_admin(
            f"🗑 Админ удалил пост пользователя {post.created_by}\n\n"
            f"{format_post_info(post, detailed=True)}"
        )
    
    await message.reply(f"✅ Пост {escape_html(args)} удален из расписания")

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    """Команда /stats - статистика (только для админа)"""
    if message.from_user.id != Config.ADMIN_ID:
        await message.reply("❌ У вас нет доступа к этой команде")
        return
    
    all_posts = post_storage.get_all()
    
    # Статистика по статусам
    status_counts = {}
    for post in all_posts:
        status_counts[post.status] = status_counts.get(post.status, 0) + 1
    
    # Статистика по пользователям
    user_stats = {}
    for post in all_posts:
        if post.created_by:
            user_stats[post.created_by] = user_stats.get(post.created_by, 0) + 1
    
    stats_text = f"""
📊 Статистика бота

📝 Всего постов: {len(all_posts)}

Статусы:
"""
    for status, count in status_counts.items():
        stats_text += f"  {status}: {count}\n"
    
    stats_text += f"\n👥 Пользователи:\n"
    for user_id, count in list(user_stats.items())[:10]:
        stats_text += f"  ID {user_id}: {count} постов\n"
    
    await message.reply(stats_text, reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'stats')
async def callback_stats(callback: types.CallbackQuery):
    """Кнопка статистики"""
    await cmd_stats(callback.message)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🌟 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def callback_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена действия через кнопку"""
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Команда /cancel - отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("🤷 Нет активного действия")
        return
    
    await state.finish()
    await message.reply("✅ Действие отменено", reply_markup=get_main_keyboard())

# ==================== ЗАДАЧИ ПЛАНИРОВЩИКА ====================

async def publish_post(post: ScheduledPost):
    """Публикация поста в канал"""
    try:
        # Добавляем информацию о времени публикации
        content = f"{post.content}\n\n---\n⏰ Опубликовано: {post.publish_time_dt.strftime('%d.%m.%Y %H:%M')} NSK"
        
        message = await bot.send_message(
            post.channel_id,
            content,
            parse_mode=ParseMode.HTML
        )
        
        # Обновляем статус
        post_storage.update(
            post.id,
            message_id=message.message_id,
            status=PostStatus.PUBLISHED.value
        )
        
        logging.info(f"✅ Пост {post.id} опубликован в канале {post.channel_id}")
        
        # Уведомляем создателя
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"✅ Пост опубликован!\n\n{format_post_info(post, detailed=True)}"
                )
            except:
                pass
        
        # Уведомляем админа
        if Config.ADMIN_ID and Config.ADMIN_ID != post.created_by:
            await notify_admin(
                f"✅ Пост опубликован пользователем {post.created_by}\n\n"
                f"{format_post_info(post, detailed=True)}"
            )
        
        # Планируем удаление
        if post.delete_after_days:
            await schedule_deletion(post)
            
    except Exception as e:
        error_msg = f"❌ Ошибка публикации поста {post.id}: {e}"
        logging.error(error_msg)
        post_storage.update(post.id, status=PostStatus.FAILED.value)
        
        # Уведомляем создателя
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"❌ Ошибка публикации поста\n\n{post.id}\n\nОшибка: {escape_html(str(e))}"
                )
            except:
                pass
        
        # Уведомляем админа
        await notify_admin(f"❌ Ошибка публикации\n\n{error_msg}")

async def schedule_deletion(post: ScheduledPost):
    """Планирование удаления поста"""
    if not post.delete_after_days or not post.message_id:
        return
    
    delete_time = post.publish_time_dt + timedelta(days=post.delete_after_days)
    now = datetime.now(Config.NSK_TIMEZONE)
    
    delay = (delete_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
        await delete_post(post)

async def delete_post(post: ScheduledPost):
    """Удаление поста из канала"""
    try:
        await bot.delete_message(post.channel_id, post.message_id)
        post_storage.update(post.id, status=PostStatus.DELETED.value)
        logging.info(f"🗑 Пост {post.id} удален из канала")
        
        # Уведомляем создателя
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"🗑 Пост удален\n\n{format_post_info(post)}"
                )
            except:
                pass
        
        # Уведомляем админа
        if Config.ADMIN_ID and Config.ADMIN_ID != post.created_by:
            await notify_admin(
                f"🗑 Пост удален пользователем {post.created_by}\n\n"
                f"{format_post_info(post)}"
            )
                
    except Exception as e:
        error_msg = f"❌ Ошибка удаления поста {post.id}: {e}"
        logging.error(error_msg)
        await notify_admin(error_msg)

async def schedule_post_task(post: ScheduledPost):
    """Задача планирования поста"""
    now = datetime.now(Config.NSK_TIMEZONE)
    publish_time = post.publish_time_dt
    
    delay = (publish_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
        await publish_post(post)

async def check_scheduled_posts():
    """Проверка запланированных постов при запуске"""
    now = datetime.now(Config.NSK_TIMEZONE)
    
    for post in post_storage.get_active():
        publish_time = post.publish_time_dt
        
        if publish_time < now:
            # Пропущенные посты публикуем сразу
            logging.info(f"⏰ Публикация пропущенного поста {post.id}")
            await publish_post(post)
        else:
            # Планируем будущие посты
            asyncio.create_task(schedule_post_task(post))
    
    logging.info(f"📊 Загружено {len(post_storage.get_active())} активных постов")
    
    # Уведомляем админа о запуске
    if Config.ADMIN_ID:
        active_count = len(post_storage.get_active())
        await notify_admin(
            f"🚀 Бот запущен\n\n"
            f"📢 Канал: {Config.CHANNEL_ID}\n"
            f"📊 Активных постов: {active_count}"
        )

# ==================== ЗАПУСК БОТА ====================

async def on_startup(dp):
    """Действия при запуске"""
    logging.info("🚀 Бот запускается...")
    
    # Проверка подключения к каналу
    try:
        chat = await bot.get_chat(Config.CHANNEL_ID)
        channel_title = chat.title if hasattr(chat, 'title') else str(Config.CHANNEL_ID)
        logging.info(f"📢 Подключен к каналу: {channel_title}")
        
        # Проверяем права бота в канале
        bot_member = await chat.get_member(bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("⚠️ Бот не является администратором канала!")
            if Config.ADMIN_ID:
                await notify_admin("⚠️ Бот не является администратором канала! Некоторые функции могут не работать.")
    except Exception as e:
        error_msg = f"❌ Ошибка подключения к каналу: {e}"
        logging.error(error_msg)
        if Config.ADMIN_ID:
            await notify_admin(error_msg)
        return
    
    # Проверка запланированных постов
    await check_scheduled_posts()
    
    logging.info("✅ Бот готов к работе!")

async def on_shutdown(dp):
    """Действия при остановке"""
    logging.info("🛑 Бот останавливается...")
    
    # Уведомляем админа об остановке
    if Config.ADMIN_ID:
        await notify_admin("🛑 Бот остановлен")
    
    await bot.close()
    logging.info("👋 До свидания!")

if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )