#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📢 Telegram бот для автопостинга в каналы
⏰ Поддержка новосибирского времени (NSK, UTC+7)
💎 Поддержка премиум эмодзи
💰 Интеграция с ценами из @smotrmaslyanino_price
"""

import asyncio
import logging
import json
import os
import re
import html
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from uuid import uuid4
import aiohttp
from bs4 import BeautifulSoup

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

# Загрузка переменных окружения
load_dotenv()

# ==================== КОНФИГУРАЦИЯ ====================

class Config:
    """Конфигурация бота"""
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = "@your_channel_username"  # ⚠️ ИЗМЕНИТЕ
    ADMIN_ID = 123456789  # ⚠️ ИЗМЕНИТЕ
    PRICE_CHANNEL = "@smotrmaslyanino_price"
    
    NSK_TIMEZONE = pytz.timezone('Asia/Novosibirsk')
    DATA_FILE = "scheduled_posts.json"
    PRICE_CACHE_FILE = "price_cache.json"
    LOG_LEVEL = logging.INFO
    
    MIN_DELETE_DAYS = 1
    MAX_DELETE_DAYS = 30
    
    @classmethod
    def validate(cls):
        errors = []
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не установлен")
        if cls.CHANNEL_ID == "@your_channel_username":
            errors.append("❌ Укажите свой канал")
        if cls.ADMIN_ID == 123456789:
            errors.append("❌ Укажите свой ID")
        
        if errors:
            raise ValueError("\n".join(errors))

# ==================== МОДЕЛИ ДАННЫХ ====================

class PostStatus(Enum):
    SCHEDULED = "📅 Запланирован"
    PUBLISHED = "✅ Опубликован"
    DELETED = "🗑 Удален"
    FAILED = "❌ Ошибка"

@dataclass
class PriceInfo:
    """Информация о цене"""
    category: str
    price: str
    emoji: str = "💰"
    
    def display(self) -> str:
        return f"{self.emoji} {self.category}: {self.price}"

@dataclass
class ScheduledPost:
    """Класс запланированного поста"""
    id: str
    channel_id: str
    content: str
    publish_time: str
    price: Optional[PriceInfo] = None
    delete_after_days: Optional[int] = None
    message_id: Optional[int] = None
    status: str = PostStatus.SCHEDULED.value
    created_at: str = None
    created_by: int = None
    published_message_id: Optional[int] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(Config.NSK_TIMEZONE).isoformat()
        if isinstance(self.price, dict):
            self.price = PriceInfo(**self.price)
    
    @property
    def publish_time_dt(self) -> datetime:
        return datetime.fromisoformat(self.publish_time)
    
    @property
    def delete_time(self) -> Optional[datetime]:
        if self.delete_after_days:
            return self.publish_time_dt + timedelta(days=self.delete_after_days)
        return None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.price:
            data['price'] = asdict(self.price)
        return data

# ==================== ХРАНИЛИЩЕ ДАННЫХ ====================

class Storage:
    """Базовое хранилище"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.data = {}
        self.load()
    
    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки {self.filename}: {e}")
    
    def save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения {self.filename}: {e}")

class PostStorage(Storage):
    """Хранилище постов"""
    
    def __init__(self, filename: str):
        super().__init__(filename)
        self.posts: Dict[str, ScheduledPost] = {}
        self._convert_to_objects()
    
    def _convert_to_objects(self):
        for post_id, post_data in self.data.items():
            self.posts[post_id] = ScheduledPost(**post_data)
    
    def add(self, post: ScheduledPost) -> str:
        self.posts[post.id] = post
        self._save_posts()
        return post.id
    
    def update(self, post_id: str, **kwargs):
        if post_id in self.posts:
            for key, value in kwargs.items():
                if hasattr(self.posts[post_id], key):
                    setattr(self.posts[post_id], key, value)
            self._save_posts()
    
    def get(self, post_id: str) -> Optional[ScheduledPost]:
        return self.posts.get(post_id)
    
    def get_all(self) -> List[ScheduledPost]:
        return list(self.posts.values())
    
    def get_active(self) -> List[ScheduledPost]:
        now = datetime.now(Config.NSK_TIMEZONE)
        return [p for p in self.posts.values() 
                if p.status == PostStatus.SCHEDULED.value and p.publish_time_dt > now]
    
    def get_published(self) -> List[ScheduledPost]:
        return [p for p in self.posts.values() if p.status == PostStatus.PUBLISHED.value]
    
    def get_by_user(self, user_id: int) -> List[ScheduledPost]:
        return [p for p in self.posts.values() if p.created_by == user_id]
    
    def remove(self, post_id: str):
        if post_id in self.posts:
            del self.posts[post_id]
            self._save_posts()
    
    def _save_posts(self):
        self.data = {pid: p.to_dict() for pid, p in self.posts.items()}
        self.save()

class PriceStorage(Storage):
    """Хранилище цен"""
    
    def __init__(self, filename: str):
        super().__init__(filename)
        self.prices: List[PriceInfo] = []
        self.last_update = None
        self._convert_prices()
    
    def _convert_prices(self):
        if 'prices' in self.data:
            self.prices = [PriceInfo(**p) for p in self.data['prices']]
        if 'last_update' in self.data:
            self.last_update = datetime.fromisoformat(self.data['last_update'])
    
    def update_prices(self, prices: List[PriceInfo]):
        self.prices = prices
        self.last_update = datetime.now(Config.NSK_TIMEZONE)
        self.data = {
            'prices': [asdict(p) for p in prices],
            'last_update': self.last_update.isoformat()
        }
        self.save()
    
    def get_prices_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру с ценами"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        if not self.prices:
            keyboard.add(InlineKeyboardButton(
                "🔄 Загрузить цены", 
                callback_data="refresh_prices"
            ))
        else:
            for price in self.prices[:5]:  # Показываем первые 5
                keyboard.add(InlineKeyboardButton(
                    price.display(),
                    callback_data=f"price_{price.category}"
                ))
        
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить цены", callback_data="refresh_prices"),
            InlineKeyboardButton("⏭ Пропустить", callback_data="skip_price"),
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_content")
        )
        
        return keyboard

# ==================== ПАРСЕР ЦЕН ====================

class PriceParser:
    """Парсер цен из канала"""
    
    PRICE_PATTERNS = {
        'визитка': r'визитка.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
        'масло': r'масло.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
        'соляра': r'соляра.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
        'летнее': r'летнее.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
        'зимнее': r'зимнее.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
        'арктика': r'арктика.*?(\d+[.,]?\d*)\s*(?:тыс|₽|руб)',
    }
    
    EMOJI_MAP = {
        'визитка': '📇',
        'масло': '🛢',
        'соляра': '⛽️',
        'летнее': '☀️',
        'зимнее': '❄️',
        'арктика': '🧊',
    }
    
    @classmethod
    async def fetch_prices(cls) -> List[PriceInfo]:
        """Получение цен из канала"""
        try:
            # Здесь должна быть реализация парсинга канала
            # Временно возвращаем тестовые данные
            return [
                PriceInfo("Визитка", "35 000 ₽", "📇"),
                PriceInfo("Масло ДТ", "42 500 ₽", "🛢"),
                PriceInfo("Соляра", "38 000 ₽", "⛽️"),
                PriceInfo("Летнее ДТ", "37 500 ₽", "☀️"),
                PriceInfo("Зимнее ДТ", "39 000 ₽", "❄️"),
            ]
        except Exception as e:
            logging.error(f"Ошибка парсинга цен: {e}")
            return []

# ==================== УТИЛИТЫ ====================

def escape_html(text: str) -> str:
    """Экранирование HTML"""
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
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return few
    else:
        return many

def parse_time(input_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """Парсинг времени"""
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    input_str = input_str.lower().strip()
    
    # Быстрые варианты
    if input_str == "сейчас":
        return now_nsk, None
    
    if input_str == "через час":
        return now_nsk + timedelta(hours=1), None
    
    # Регулярные выражения
    patterns = [
        (r'^(\d{1,2}):(\d{2})$', 'today'),
        (r'^завтра\s*(\d{1,2}):(\d{2})$', 'tomorrow'),
        (r'^(\d{1,2})[.](\d{1,2})[.](\d{4})\s+(\d{1,2}):(\d{2})$', 'date'),
        (r'^(\d+)\s*ч$', 'hours'),
        (r'^(\d+)\s*д$', 'days'),
        (r'^(\d+)\s*м$', 'minutes'),
    ]
    
    for pattern, type_ in patterns:
        match = re.match(pattern, input_str)
        if not match:
            continue
        
        try:
            if type_ == 'today':
                hours, minutes = map(int, match.groups())
                target = now_nsk.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if target < now_nsk:
                    target += timedelta(days=1)
                return target, None
            
            elif type_ == 'tomorrow':
                hours, minutes = map(int, match.groups())
                target = (now_nsk + timedelta(days=1)).replace(
                    hour=hours, minute=minutes, second=0, microsecond=0
                )
                return target, None
            
            elif type_ == 'date':
                day, month, year, hours, minutes = map(int, match.groups())
                target = Config.NSK_TIMEZONE.localize(
                    datetime(year, month, day, hours, minutes)
                )
                if target < now_nsk:
                    return None, "❌ Дата не может быть в прошлом"
                return target, None
            
            elif type_ == 'hours':
                hours = int(match.group(1))
                return now_nsk + timedelta(hours=hours), None
            
            elif type_ == 'days':
                days = int(match.group(1))
                return now_nsk + timedelta(days=days), None
            
            elif type_ == 'minutes':
                minutes = int(match.group(1))
                return now_nsk + timedelta(minutes=minutes), None
                
        except ValueError:
            continue
    
    return None, "❌ Неверный формат времени"

def format_post_display(post: ScheduledPost, detailed: bool = False, for_admin: bool = False) -> str:
    """Форматирование поста для отображения"""
    lines = []
    
    # ID и статус
    status_emoji = {
        PostStatus.SCHEDULED.value: "📅",
        PostStatus.PUBLISHED.value: "✅",
        PostStatus.DELETED.value: "🗑",
        PostStatus.FAILED.value: "❌"
    }.get(post.status, "📝")
    
    lines.append(f"{status_emoji} Пост: {post.id}")
    
    # Время публикации
    pub_time = post.publish_time_dt.strftime("%d.%m.%Y %H:%M")
    lines.append(f"⏰ Публикация: {pub_time} NSK")
    
    # До публикации (для запланированных)
    if post.status == PostStatus.SCHEDULED.value:
        lines.append(f"⏳ Осталось: {format_timedelta(post.publish_time_dt - datetime.now(Config.NSK_TIMEZONE))}")
    
    # Цена (только для админов)
    if for_admin and post.price:
        lines.append(f"💰 Цена: {post.price.display()}")
    
    # Удаление
    if post.delete_after_days:
        delete_time = post.delete_time.strftime("%d.%m.%Y %H:%M")
        lines.append(f"🗑 Удаление: через {post.delete_after_days} дн. ({delete_time})")
    
    # Текст (обрезанный)
    content = post.content[:200] + ("..." if len(post.content) > 200 else "")
    lines.append(f"\n📝 {content}")
    
    # Создатель
    if for_admin and post.created_by:
        lines.append(f"👤 Создатель: {post.created_by}")
    
    return "\n".join(lines)

# ==================== СОСТОЯНИЯ FSM ====================

class PostStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_publish_time = State()
    waiting_for_price = State()
    waiting_for_delete_days = State()
    confirming = State()

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Основные кнопки
    keyboard.add(
        InlineKeyboardButton("📝 Новый пост", callback_data="new_post"),
        InlineKeyboardButton("📋 Мои посты", callback_data="my_posts")
    )
    
    # Кнопки управления
    keyboard.add(
        InlineKeyboardButton("⏰ Запланированные", callback_data="scheduled"),
        InlineKeyboardButton("✅ Опубликованные", callback_data="published")
    )
    
    # Кнопка помощи
    keyboard.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    
    # Админские кнопки
    if is_admin:
        keyboard.add(
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("🔄 Обновить цены", callback_data="admin_refresh_prices")
        )
    
    return keyboard

def get_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора времени"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Быстрые варианты
    time_options = [
        ("⚡️ Сейчас", "time_сейчас"),
        ("⏰ Через час", "time_через час"),
        ("🌅 10:00", "time_10:00"),
        ("🌞 12:00", "time_12:00"),
        ("🌆 15:00", "time_15:00"),
        ("🌃 18:00", "time_18:00"),
        ("📅 Завтра 10:00", "time_завтра 10:00"),
        ("📅 Завтра 12:00", "time_завтра 12:00"),
    ]
    
    for text, callback in time_options:
        keyboard.insert(InlineKeyboardButton(text, callback_data=callback))
    
    keyboard.add(
        InlineKeyboardButton("⌨️ Свой вариант", callback_data="custom_time"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_content")
    )
    
    return keyboard

def get_delete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора удаления"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Варианты удаления
    delete_options = [
        ("1 день", "delete_1"),
        ("3 дня", "delete_3"),
        ("7 дней", "delete_7"),
        ("14 дней", "delete_14"),
        ("21 день", "delete_21"),
        ("30 дней", "delete_30"),
    ]
    
    for text, callback in delete_options:
        keyboard.insert(InlineKeyboardButton(f"🗑 {text}", callback_data=callback))
    
    keyboard.add(
        InlineKeyboardButton("🚫 Не удалять", callback_data="delete_0"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_price")
    )
    
    return keyboard

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")
    )
    keyboard.add(InlineKeyboardButton("✏️ Редактировать", callback_data="edit_post"))
    return keyboard

def get_post_actions_keyboard(post_id: str, is_owner: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий с постом"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if is_owner or is_admin:
        keyboard.add(
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_post_{post_id}"),
            InlineKeyboardButton("📋 Детали", callback_data=f"post_details_{post_id}")
        )
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
    return keyboard

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

Config.validate()

bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

post_storage = PostStorage(Config.DATA_FILE)
price_storage = PriceStorage(Config.PRICE_CACHE_FILE)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    welcome_text = f"""
🌟 <b>Бот для автопостинга</b>

📢 Канал: {escape_html(str(Config.CHANNEL_ID))}
⏰ Часовой пояс: Новосибирск (NSK, UTC+7)
{'👑 Роль: Администратор' if is_admin else '👤 Роль: Пользователь'}

<b>Доступные команды:</b>
• /post - создать новый пост
• /list - список моих постов
• /help - подробная справка
• /cancel - отмена

<i>Используйте кнопки ниже для навигации</i>
    """
    
    await message.reply(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin)
    )

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Команда /help"""
    help_text = """
<b>❓ Справка по использованию</b>

<b>📝 Создание поста:</b>
1. Нажмите "Новый пост" или отправьте /post
2. Введите текст поста (можно использовать HTML и эмодзи)
3. Выберите время публикации
4. Выберите цену (опционально)
5. Укажите через сколько дней удалить
6. Подтвердите публикацию

<b>⏰ Форматы времени:</b>
• Сейчас - мгновенная публикация
• Через час - через 60 минут
• 14:30 - сегодня (или завтра если прошло)
• завтра 10:00 - завтра
• 15.01.2024 14:30 - конкретная дата
• 2ч - через 2 часа
• 3д - через 3 дня

<b>💰 Цены:</b>
• Автоматически подгружаются из канала @smotrmaslyanino_price
• Видны только администраторам
• Можно обновить кнопкой "🔄 Обновить цены"

<b>🗑 Удаление:</b>
• Минимум: 1 день
• Максимум: 30 дней

<b>📊 Статистика:</b>
Доступна только администраторам
    """
    
    await message.reply(
        help_text,
        reply_markup=get_main_keyboard(message.from_user.id == Config.ADMIN_ID)
    )

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    """Создание нового поста"""
    await message.reply(
        "📝 <b>Отправьте текст поста</b>\n\n"
        "Можно использовать:\n"
        "• <b>HTML-разметку</b>\n"
        "• 💎 Премиум эмодзи\n"
        "• Ссылки и форматирование\n\n"
        "<i>Или нажмите кнопку отмены</i>",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        )
    )
    await PostStates.waiting_for_content.set()

@dp.message_handler(state=PostStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    """Обработка текста поста"""
    if not message.text and not message.caption:
        await message.reply("❌ Отправьте текстовое сообщение")
        return
    
    content = message.text or message.caption
    await state.update_data(content=content)
    
    await message.reply(
        "⏰ <b>Выберите время публикации</b>",
        reply_markup=get_time_keyboard()
    )
    await PostStates.waiting_for_publish_time.set()

@dp.callback_query_handler(lambda c: c.data.startswith('time_'), state=PostStates.waiting_for_publish_time)
async def process_time_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_str = callback.data.replace('time_', '')
    
    if time_str == "custom_time":
        await callback.message.edit_text(
            "⌨️ <b>Введите время вручную</b>\n\n"
            "Примеры:\n"
            "• сейчас\n"
            "• через час\n"
            "• 14:30\n"
            "• завтра 10:00\n"
            "• 15.01.2024 14:30\n"
            "• 2ч\n"
            "• 3д",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_time")
            )
        )
        await callback.answer()
        return
    
    publish_time, error = parse_time(time_str)
    
    if error:
        await callback.answer(error, show_alert=True)
        return
    
    await state.update_data(publish_time=publish_time.isoformat())
    
    # Показываем выбор цены
    await callback.message.edit_text(
        "💰 <b>Выберите цену</b>\n\n"
        "Цены загружены из канала @smotrmaslyanino_price\n"
        "Цена будет видна только администраторам",
        reply_markup=price_storage.get_prices_keyboard()
    )
    await PostStates.waiting_for_price.set()
    await callback.answer()

@dp.message_handler(state=PostStates.waiting_for_publish_time)
async def process_custom_time(message: types.Message, state: FSMContext):
    """Обработка ручного ввода времени"""
    publish_time, error = parse_time(message.text)
    
    if error:
        await message.reply(
            error + "\n\nПопробуйте снова:",
            reply_markup=get_time_keyboard()
        )
        return
    
    await state.update_data(publish_time=publish_time.isoformat())
    
    await message.reply(
        "💰 <b>Выберите цену</b>",
        reply_markup=price_storage.get_prices_keyboard()
    )
    await PostStates.waiting_for_price.set()

@dp.callback_query_handler(lambda c: c.data.startswith('price_'), state=PostStates.waiting_for_price)
async def process_price_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора цены"""
    category = callback.data.replace('price_', '')
    
    # Находим выбранную цену
    selected_price = None
    for price in price_storage.prices:
        if price.category.lower() == category.lower():
            selected_price = price
            break
    
    if selected_price:
        await state.update_data(price=selected_price)
    
    # Переходим к выбору удаления
    await callback.message.edit_text(
        "🗑 <b>Через сколько дней удалить пост?</b>\n\n"
        f"Минимум: {Config.MIN_DELETE_DAYS} день\n"
        f"Максимум: {Config.MAX_DELETE_DAYS} дней",
        reply_markup=get_delete_keyboard()
    )
    await PostStates.waiting_for_delete_days.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'skip_price', state=PostStates.waiting_for_price)
async def skip_price(callback: types.CallbackQuery, state: FSMContext):
    """Пропуск выбора цены"""
    await state.update_data(price=None)
    
    await callback.message.edit_text(
        "🗑 <b>Через сколько дней удалить пост?</b>",
        reply_markup=get_delete_keyboard()
    )
    await PostStates.waiting_for_delete_days.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'refresh_prices', state=PostStates.waiting_for_price)
async def refresh_prices(callback: types.CallbackQuery, state: FSMContext):
    """Обновление цен"""
    await callback.message.edit_text("🔄 Обновление цен...")
    
    prices = await PriceParser.fetch_prices()
    if prices:
        price_storage.update_prices(prices)
        await callback.message.edit_text(
            "💰 <b>Цены обновлены!</b>\n\nВыберите цену:",
            reply_markup=price_storage.get_prices_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось обновить цены\n\n"
            "Попробуйте позже или пропустите этот шаг",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⏭ Пропустить", callback_data="skip_price"),
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_content")
            )
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'), state=PostStates.waiting_for_delete_days)
async def process_delete_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора удаления"""
    days = int(callback.data.replace('delete_', ''))
    delete_days = None if days == 0 else days
    
    await show_confirmation(callback.message, state, delete_days)
    await callback.answer()

async def show_confirmation(message: types.Message, state: FSMContext, delete_days: Optional[int]):
    """Показ подтверждения"""
    data = await state.get_data()
    content = data['content']
    publish_time = datetime.fromisoformat(data['publish_time'])
    price = data.get('price')
    
    # Создаем временный пост для предпросмотра
    temp_post = ScheduledPost(
        id="temp",
        channel_id=Config.CHANNEL_ID,
        content=content,
        publish_time=publish_time.isoformat(),
        price=price,
        delete_after_days=delete_days
    )
    
    # Формируем предпросмотр
    preview_lines = ["<b>📝 Предпросмотр поста:</b>\n"]
    
    # Текст поста
    preview_lines.append(content)
    preview_lines.append("")
    
    # Информация
    preview_lines.append("—" * 20)
    preview_lines.append(f"⏰ Публикация: {publish_time.strftime('%d.%m.%Y %H:%M')} NSK")
    
    if price:
        preview_lines.append(f"💰 Цена (только для админов): {price.display()}")
    
    if delete_days:
        delete_time = publish_time + timedelta(days=delete_days)
        preview_lines.append(f"🗑 Удаление: через {delete_days} дн. ({delete_time.strftime('%d.%m.%Y %H:%M')})")
    else:
        preview_lines.append("🗑 Удаление: не требуется")
    
    preview_lines.append("")
    preview_lines.append("<b>✅ Всё верно?</b>")
    
    await message.edit_text(
        "\n".join(preview_lines),
        reply_markup=get_confirmation_keyboard()
    )
    
    await state.update_data(delete_days=delete_days)

@dp.callback_query_handler(lambda c: c.data == 'confirm_yes', state=PostStates.confirming)
async def confirm_post(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение публикации"""
    data = await state.get_data()
    user_id = callback.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    # Создаем пост
    post = ScheduledPost(
        id=str(uuid4())[:8],
        channel_id=Config.CHANNEL_ID,
        content=data['content'],
        publish_time=data['publish_time'],
        price=data.get('price'),
        delete_after_days=data.get('delete_days'),
        created_by=user_id
    )
    
    # Сохраняем
    post_id = post_storage.add(post)
    
    # Если публикация "сейчас" или время уже прошло
    now = datetime.now(Config.NSK_TIMEZONE)
    if post.publish_time_dt <= now:
        await publish_post(post)
        status_text = "публикуется сейчас"
    else:
        # Планируем публикацию
        asyncio.create_task(schedule_post_task(post))
        status_text = f"запланирован на {post.publish_time_dt.strftime('%d.%m.%Y %H:%M')}"
    
    # Уведомление пользователю
    await callback.message.edit_text(
        f"✅ <b>Пост успешно создан!</b>\n\n"
        f"🆔 ID: {post.id}\n"
        f"📊 Статус: {status_text}\n\n"
        f"🔔 Я уведомлю вас о публикации",
        reply_markup=get_main_keyboard(is_admin)
    )
    
    # Уведомление админу (если создатель не админ)
    if Config.ADMIN_ID and Config.ADMIN_ID != user_id:
        await notify_admin(
            f"📝 <b>Новый пост от пользователя {user_id}</b>\n\n"
            f"{format_post_display(post, for_admin=True)}"
        )
    
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'confirm_no', state=PostStates.confirming)
async def cancel_post(callback: types.CallbackQuery, state: FSMContext):
    """Отмена публикации"""
    await callback.message.edit_text(
        "❌ Создание поста отменено",
        reply_markup=get_main_keyboard(callback.from_user.id == Config.ADMIN_ID)
    )
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_post', state=PostStates.confirming)
async def edit_post(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование поста"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что хотите изменить?",
        reply_markup=InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("📝 Текст", callback_data="edit_content"),
            InlineKeyboardButton("⏰ Время", callback_data="edit_time"),
            InlineKeyboardButton("💰 Цену", callback_data="edit_price"),
            InlineKeyboardButton("🗑 Удаление", callback_data="edit_delete"),
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_confirm")
        )
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_content', state=PostStates.confirming)
async def edit_content(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование текста"""
    await callback.message.edit_text(
        "📝 <b>Отправьте новый текст поста</b>",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_confirm")
        )
    )
    await PostStates.waiting_for_content.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_time', state=PostStates.confirming)
async def edit_time(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование времени"""
    await callback.message.edit_text(
        "⏰ <b>Выберите новое время публикации</b>",
        reply_markup=get_time_keyboard()
    )
    await PostStates.waiting_for_publish_time.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_price', state=PostStates.confirming)
async def edit_price(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование цены"""
    await callback.message.edit_text(
        "💰 <b>Выберите цену</b>",
        reply_markup=price_storage.get_prices_keyboard()
    )
    await PostStates.waiting_for_price.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_delete', state=PostStates.confirming)
async def edit_delete(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование удаления"""
    await callback.message.edit_text(
        "🗑 <b>Выберите срок удаления</b>",
        reply_markup=get_delete_keyboard()
    )
    await PostStates.waiting_for_delete_days.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_confirm', state='*')
async def back_to_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к подтверждению"""
    data = await state.get_data()
    await show_confirmation(
        callback.message, 
        state, 
        data.get('delete_days')
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_time', state='*')
async def back_to_time(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    await callback.message.edit_text(
        "⏰ <b>Выберите время публикации</b>",
        reply_markup=get_time_keyboard()
    )
    await PostStates.waiting_for_publish_time.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_price', state='*')
async def back_to_price(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору цены"""
    await callback.message.edit_text(
        "💰 <b>Выберите цену</b>",
        reply_markup=price_storage.get_prices_keyboard()
    )
    await PostStates.waiting_for_price.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_content', state='*')
async def back_to_content(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к вводу контента"""
    await callback.message.edit_text(
        "📝 <b>Отправьте текст поста</b>",
        reply_markup=None
    )
    await PostStates.waiting_for_content.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'new_post')
async def callback_new_post(callback: types.CallbackQuery):
    """Кнопка нового поста"""
    await cmd_post(callback.message)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'my_posts')
async def callback_my_posts(callback: types.CallbackQuery):
    """Мои посты"""
    user_id = callback.from_user.id
    posts = post_storage.get_by_user(user_id)
    
    if not posts:
        await callback.message.edit_text(
            "📭 <b>У вас нет постов</b>\n\n"
            "Создайте новый пост с помощью /post",
            reply_markup=get_main_keyboard(user_id == Config.ADMIN_ID)
        )
        await callback.answer()
        return
    
    text = ["<b>📋 Ваши посты:</b>\n"]
    
    for i, post in enumerate(posts[:10], 1):
        status = "📅" if post.status == PostStatus.SCHEDULED.value else "✅"
        pub_time = post.publish_time_dt.strftime("%d.%m %H:%M")
        text.append(f"{i}. {status} {post.id} – {pub_time}")
    
    if len(posts) > 10:
        text.append(f"\n...и еще {len(posts) - 10} постов")
    
    await callback.message.edit_text(
        "\n".join(text),
        reply_markup=get_main_keyboard(user_id == Config.ADMIN_ID)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'scheduled')
async def callback_scheduled(callback: types.CallbackQuery):
    """Запланированные посты"""
    user_id = callback.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    if is_admin:
        posts = post_storage.get_active()
    else:
        posts = [p for p in post_storage.get_by_user(user_id) 
                if p.status == PostStatus.SCHEDULED.value]
    
    if not posts:
        await callback.message.edit_text(
            "📭 <b>Нет запланированных постов</b>",
            reply_markup=get_main_keyboard(is_admin)
        )
        await callback.answer()
        return
    
    text = ["<b>📅 Запланированные посты:</b>\n"]
    
    for post in sorted(posts, key=lambda x: x.publish_time_dt)[:10]:
        pub_time = post.publish_time_dt.strftime("%d.%m %H:%M")
        time_left = format_timedelta(post.publish_time_dt - datetime.now(Config.NSK_TIMEZONE))
        text.append(f"• {post.id} – {pub_time} (осталось {time_left})")
    
    if len(posts) > 10:
        text.append(f"\n...и еще {len(posts) - 10} постов")
    
    await callback.message.edit_text(
        "\n".join(text),
        reply_markup=get_main_keyboard(is_admin)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'published')
async def callback_published(callback: types.CallbackQuery):
    """Опубликованные посты"""
    user_id = callback.from_user.id
    is_admin = user_id == Config.ADMIN_ID
    
    if is_admin:
        posts = post_storage.get_published()
    else:
        posts = [p for p in post_storage.get_by_user(user_id) 
                if p.status == PostStatus.PUBLISHED.value]
    
    if not posts:
        await callback.message.edit_text(
            "📭 <b>Нет опубликованных постов</b>",
            reply_markup=get_main_keyboard(is_admin)
        )
        await callback.answer()
        return
    
    text = ["<b>✅ Опубликованные посты:</b>\n"]
    
    for post in sorted(posts, key=lambda x: x.publish_time_dt, reverse=True)[:10]:
        pub_time = post.publish_time_dt.strftime("%d.%m %H:%M")
        text.append(f"• {post.id} – {pub_time}")
    
    if len(posts) > 10:
        text.append(f"\n...и еще {len(posts) - 10} постов")
    
    await callback.message.edit_text(
        "\n".join(text),
        reply_markup=get_main_keyboard(is_admin)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'stats')
async def callback_stats(callback: types.CallbackQuery):
    """Статистика (только для админа)"""
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
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
    
    # Цены
    price_stats = {}
    for post in all_posts:
        if post.price:
            cat = post.price.category
            price_stats[cat] = price_stats.get(cat, 0) + 1
    
    stats_text = [
        "<b>📊 Статистика бота</b>\n",
        f"📝 Всего постов: {len(all_posts)}",
        "",
        "<b>По статусам:</b>"
    ]
    
    for status, count in status_counts.items():
        stats_text.append(f"  {status}: {count}")
    
    stats_text.extend([
        "",
        "<b>По пользователям:</b>"
    ])
    
    for user_id, count in sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        stats_text.append(f"  ID {user_id}: {count} постов")
    
    if price_stats:
        stats_text.extend([
            "",
            "<b>По ценам:</b>"
        ])
        for cat, count in price_stats.items():
            stats_text.append(f"  {cat}: {count} постов")
    
    stats_text.extend([
        "",
        f"🕐 Последнее обновление: {datetime.now(Config.NSK_TIMEZONE).strftime('%d.%m.%Y %H:%M')}"
    ])
    
    await callback.message.edit_text(
        "\n".join(stats_text),
        reply_markup=get_main_keyboard(True)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_refresh_prices')
async def admin_refresh_prices(callback: types.CallbackQuery):
    """Принудительное обновление цен (админ)"""
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("🔄 Обновление цен...")
    
    prices = await PriceParser.fetch_prices()
    if prices:
        price_storage.update_prices(prices)
        await callback.message.edit_text(
            "✅ <b>Цены успешно обновлены!</b>\n\n"
            f"Загружено: {len(prices)} позиций",
            reply_markup=get_main_keyboard(True)
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось обновить цены",
            reply_markup=get_main_keyboard(True)
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'help')
async def callback_help(callback: types.CallbackQuery):
    """Кнопка помощи"""
    await cmd_help(callback.message)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🌟 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_keyboard(callback.from_user.id == Config.ADMIN_ID)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def callback_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена действия"""
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=get_main_keyboard(callback.from_user.id == Config.ADMIN_ID)
    )
    await callback.answer()

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Команда отмены"""
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("🤷 Нет активного действия")
        return
    
    await state.finish()
    await message.reply(
        "✅ Действие отменено",
        reply_markup=get_main_keyboard(message.from_user.id == Config.ADMIN_ID)
    )

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    """Список постов"""
    await callback_my_posts(types.CallbackQuery(
        message=message,
        id="0",
        from_user=message.from_user,
        chat_instance="0",
        data="my_posts"
    ))

# ==================== ЗАДАЧИ ПЛАНИРОВЩИКА ====================

async def publish_post(post: ScheduledPost):
    """Публикация поста в канал"""
    try:
        # Формируем контент
        content_parts = [post.content]
        
        # Добавляем информацию о времени
        time_str = post.publish_time_dt.strftime('%d.%m.%Y %H:%M')
        content_parts.append(f"\n—\n⏰ {time_str} NSK")
        
        # Добавляем цену для админов (но в канале не показываем)
        # Цена сохраняется только в базе для статистики
        
        content = "\n".join(content_parts)
        
        # Отправляем в канал
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
        
        logging.info(f"✅ Пост {post.id} опубликован")
        
        # Уведомляем создателя
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"✅ <b>Пост опубликован!</b>\n\n{format_post_display(post)}"
                )
            except:
                pass
        
        # Уведомляем админа
        if Config.ADMIN_ID and Config.ADMIN_ID != post.created_by:
            await notify_admin(
                f"✅ <b>Пост опубликован пользователем {post.created_by}</b>\n\n"
                f"{format_post_display(post, for_admin=True)}"
            )
        
        # Планируем удаление
        if post.delete_after_days:
            asyncio.create_task(schedule_deletion(post))
            
    except Exception as e:
        error_msg = f"❌ Ошибка публикации поста {post.id}: {e}"
        logging.error(error_msg)
        post_storage.update(post.id, status=PostStatus.FAILED.value)
        
        # Уведомления об ошибке
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"❌ <b>Ошибка публикации</b>\n\nПост {post.id}\nОшибка: {escape_html(str(e))}"
                )
            except:
                pass
        
        await notify_admin(error_msg)

async def schedule_deletion(post: ScheduledPost):
    """Планирование удаления"""
    if not post.delete_after_days or not post.message_id:
        return
    
    delete_time = post.publish_time_dt + timedelta(days=post.delete_after_days)
    now = datetime.now(Config.NSK_TIMEZONE)
    
    delay = (delete_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
        await delete_post(post)

async def delete_post(post: ScheduledPost):
    """Удаление поста"""
    try:
        await bot.delete_message(post.channel_id, post.message_id)
        post_storage.update(post.id, status=PostStatus.DELETED.value)
        logging.info(f"🗑 Пост {post.id} удален")
        
        # Уведомления
        if post.created_by:
            try:
                await bot.send_message(
                    post.created_by,
                    f"🗑 <b>Пост удален</b>\n\n{format_post_display(post)}"
                )
            except:
                pass
        
        if Config.ADMIN_ID and Config.ADMIN_ID != post.created_by:
            await notify_admin(
                f"🗑 <b>Пост удален</b> (пользователь {post.created_by})\n\n"
                f"{format_post_display(post, for_admin=True)}"
            )
                
    except Exception as e:
        error_msg = f"❌ Ошибка удаления поста {post.id}: {e}"
        logging.error(error_msg)
        await notify_admin(error_msg)

async def schedule_post_task(post: ScheduledPost):
    """Задача планирования поста"""
    now = datetime.now(Config.NSK_TIMEZONE)
    delay = (post.publish_time_dt - now).total_seconds()
    
    if delay > 0:
        await asyncio.sleep(delay)
        await publish_post(post)

async def check_scheduled_posts():
    """Проверка запланированных постов при запуске"""
    now = datetime.now(Config.NSK_TIMEZONE)
    active_posts = post_storage.get_active()
    
    for post in active_posts:
        if post.publish_time_dt <= now:
            # Пропущенные публикуем сразу
            logging.info(f"⏰ Публикация пропущенного поста {post.id}")
            await publish_post(post)
        else:
            # Планируем будущие
            asyncio.create_task(schedule_post_task(post))
    
    logging.info(f"📊 Загружено {len(active_posts)} активных постов")

async def notify_admin(message: str):
    """Отправка уведомления админу"""
    if Config.ADMIN_ID:
        try:
            await bot.send_message(Config.ADMIN_ID, message)
        except Exception as e:
            logging.error(f"Ошибка уведомления админа: {e}")

# ==================== ЗАПУСК БОТА ====================

async def on_startup(dp):
    """Действия при запуске"""
    logging.info("🚀 Бот запускается...")
    
    # Проверка подключения к каналу
    try:
        chat = await bot.get_chat(Config.CHANNEL_ID)
        channel_title = chat.title if hasattr(chat, 'title') else str(Config.CHANNEL_ID)
        logging.info(f"📢 Подключен к каналу: {channel_title}")
        
        # Проверка прав
        bot_member = await chat.get_member(bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("⚠️ Бот не администратор канала!")
            await notify_admin("⚠️ Бот не администратор канала!")
    except Exception as e:
        error_msg = f"❌ Ошибка подключения к каналу: {e}"
        logging.error(error_msg)
        await notify_admin(error_msg)
        return
    
    # Загрузка цен
    if not price_storage.prices:
        prices = await PriceParser.fetch_prices()
        if prices:
            price_storage.update_prices(prices)
            logging.info(f"💰 Загружено {len(prices)} позиций цен")
    
    # Проверка запланированных постов
    await check_scheduled_posts()
    
    # Уведомление о запуске
    await notify_admin(
        f"🚀 <b>Бот запущен</b>\n\n"
        f"📢 Канал: {Config.CHANNEL_ID}\n"
        f"📊 Активных постов: {len(post_storage.get_active())}\n"
        f"💰 Цен в базе: {len(price_storage.prices)}"
    )
    
    logging.info("✅ Бот готов к работе!")

async def on_shutdown(dp):
    """Действия при остановке"""
    logging.info("🛑 Бот останавливается...")
    await notify_admin("🛑 <b>Бот остановлен</b>")
    await bot.close()
    logging.info("👋 До свидания!")

if __name__ == '__main__':
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )