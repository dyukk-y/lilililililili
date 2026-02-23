#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram бот для автопостинга с поддержкой новосибирского времени (UTC+7)
Возможности:
- Публикация постов в указанное время
- Автоматическое удаление постов через заданный интервал
- Конвертация времени в новосибирское
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# ==================== КОНФИГУРАЦИЯ ====================

class Config:
    """Класс для хранения конфигурации"""
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # Токен бота
    NSK_TIMEZONE = pytz.timezone('Asia/Novosibirsk')  # Новосибирск (UTC+7)
    DATA_FILE = "scheduled_posts.json"  # Файл для хранения постов
    LOG_LEVEL = logging.INFO  # Уровень логирования

# ==================== МОДЕЛИ ДАННЫХ ====================

class PostStatus(Enum):
    """Статусы поста"""
    SCHEDULED = "scheduled"  # Запланирован
    PUBLISHED = "published"  # Опубликован
    DELETED = "deleted"      # Удален
    FAILED = "failed"        # Ошибка

@dataclass
class ScheduledPost:
    """Класс для хранения информации о запланированном посте"""
    id: str
    chat_id: int
    content: str
    publish_time: str  # ISO формат строки
    delete_after_minutes: Optional[int] = None
    message_id: Optional[int] = None
    status: str = PostStatus.SCHEDULED.value
    created_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(Config.NSK_TIMEZONE).isoformat()
    
    @property
    def publish_time_dt(self) -> datetime:
        """Получить время публикации как datetime"""
        return datetime.fromisoformat(self.publish_time)
    
    @property
    def delete_time(self) -> Optional[datetime]:
        """Получить время удаления как datetime"""
        if self.delete_after_minutes:
            return self.publish_time_dt + timedelta(minutes=self.delete_after_minutes)
        return None

# ==================== ХРАНИЛИЩЕ ДАННЫХ ====================

class PostStorage:
    """Класс для работы с хранилищем постов"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.posts: Dict[str, ScheduledPost] = {}
        self.load()
    
    def load(self):
        """Загрузка постов из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for post_id, post_data in data.items():
                        self.posts[post_id] = ScheduledPost(**post_data)
                logging.info(f"Загружено {len(self.posts)} постов из файла")
        except Exception as e:
            logging.error(f"Ошибка загрузки данных: {e}")
    
    def save(self):
        """Сохранение постов в файл"""
        try:
            data = {post_id: asdict(post) for post_id, post in self.posts.items()}
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения данных: {e}")
    
    def add(self, post: ScheduledPost):
        """Добавление поста"""
        self.posts[post.id] = post
        self.save()
    
    def update(self, post_id: str, **kwargs):
        """Обновление данных поста"""
        if post_id in self.posts:
            for key, value in kwargs.items():
                if hasattr(self.posts[post_id], key):
                    setattr(self.posts[post_id], key, value)
            self.save()
    
    def get(self, post_id: str) -> Optional[ScheduledPost]:
        """Получение поста по ID"""
        return self.posts.get(post_id)
    
    def get_all(self) -> Dict[str, ScheduledPost]:
        """Получение всех постов"""
        return self.posts
    
    def remove(self, post_id: str):
        """Удаление поста"""
        if post_id in self.posts:
            del self.posts[post_id]
            self.save()

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

# Инициализация бота и компонентов
bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=Config.LOG_LEVEL)

# Инициализация хранилища постов
post_storage = PostStorage(Config.DATA_FILE)

# ==================== СОСТОЯНИЯ FSM ====================

class PostStates(StatesGroup):
    """Состояния для создания поста"""
    waiting_for_content = State()
    waiting_for_time = State()
    waiting_for_delete = State()

# ==================== УТИЛИТЫ ====================

def parse_time(input_time_str: str) -> Optional[datetime]:
    """
    Преобразует введенное время в новосибирское время (NSK, UTC+7)
    
    Поддерживаемые форматы:
    - "2024-01-15 14:30" - дата и время
    - "14:30" - сегодня в это время (или завтра, если время прошло)
    - "tomorrow 14:30" - завтра в это время
    - "1h" - через 1 час
    - "30m" - через 30 минут
    - "1d" - через 1 день
    """
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    input_time_str = input_time_str.lower().strip()
    
    try:
        # Обработка относительного времени
        if input_time_str.endswith('h'):
            hours = int(input_time_str[:-1])
            return now_nsk + timedelta(hours=hours)
            
        elif input_time_str.endswith('m'):
            minutes = int(input_time_str[:-1])
            return now_nsk + timedelta(minutes=minutes)
            
        elif input_time_str.endswith('d'):
            days = int(input_time_str[:-1])
            return now_nsk + timedelta(days=days)
            
        elif input_time_str.startswith('tomorrow'):
            time_part = input_time_str.replace('tomorrow', '').strip()
            if not time_part:
                return None
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            target_date = now_nsk.date() + timedelta(days=1)
            return Config.NSK_TIMEZONE.localize(
                datetime.combine(target_date, time_obj)
            )
            
        else:
            # Попытка распарсить как полную дату
            try:
                target_time = datetime.strptime(input_time_str, '%Y-%m-%d %H:%M')
                return Config.NSK_TIMEZONE.localize(target_time)
            except ValueError:
                # Попытка распарсить как время сегодня
                time_obj = datetime.strptime(input_time_str, '%H:%M').time()
                target_time = Config.NSK_TIMEZONE.localize(
                    datetime.combine(now_nsk.date(), time_obj)
                )
                # Если время уже прошло сегодня, переносим на завтра
                if target_time < now_nsk:
                    target_time += timedelta(days=1)
                return target_time
                
    except (ValueError, TypeError) as e:
        logging.error(f"Ошибка парсинга времени '{input_time_str}': {e}")
        return None

def format_time_remaining(target_time: datetime) -> str:
    """Форматирует оставшееся время до публикации"""
    now = datetime.now(Config.NSK_TIMEZONE)
    diff = target_time - now
    
    if diff.total_seconds() < 0:
        return "время прошло"
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} дн.")
    if hours > 0:
        parts.append(f"{hours} ч.")
    if minutes > 0:
        parts.append(f"{minutes} мин.")
    
    return " ".join(parts) if parts else "менее минуты"

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """
🤖 <b>Бот для автопостинга</b>

Я помогу вам планировать посты с учетом новосибирского времени (UTC+7).

<b>Доступные команды:</b>
/post - создать новый пост
/list - показать запланированные посты
/cancel - отменить текущее действие
/help - показать эту справку

<b>Форматы времени:</b>
• 14:30 - сегодня в 14:30 (или завтра)
• 2024-01-15 14:30 - конкретная дата
• tomorrow 14:30 - завтра в 14:30
• 1h - через 1 час
• 30m - через 30 минут
• 1d - через 1 день

После публикации можно настроить автоматическое удаление поста.
    """
    await message.reply(welcome_text, parse_mode=ParseMode.HTML)

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await cmd_start(message)

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    """Обработчик команды /post - начало создания поста"""
    await message.reply(
        "📝 Отправьте текст поста для публикации.\n"
        "Можно использовать HTML-разметку: <b>жирный</b>, <i>курсив</i>, <code>код</code>"
    )
    await PostStates.waiting_for_content.set()

@dp.message_handler(state=PostStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    """Обработка ввода текста поста"""
    await state.update_data(content=message.html_text)
    await message.reply(
        "⏰ Укажите время публикации.\n"
        "Например: 14:30, tomorrow 10:00, 2024-01-15 15:30, 2h, 45m"
    )
    await PostStates.waiting_for_time.set()

@dp.message_handler(state=PostStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени публикации"""
    publish_time = parse_time(message.text)
    
    if not publish_time:
        await message.reply(
            "❌ Неверный формат времени.\n"
            "Используйте: 14:30, tomorrow 10:00, 2024-01-15 15:30, 2h, 45m"
        )
        return
    
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    if publish_time <= now_nsk:
        await message.reply("❌ Время публикации должно быть в будущем!")
        return
    
    await state.update_data(publish_time=publish_time.isoformat())
    
    # Запрашиваем время до удаления
    await message.reply(
        "🗑 Через сколько минут удалить пост?\n"
        "Отправьте:\n"
        "• число минут (например: 60)\n"
        "• 0 - если не нужно удалять\n"
        "• пропустите этот шаг (отправьте '-')"
    )
    await PostStates.waiting_for_delete.set()

@dp.message_handler(state=PostStates.waiting_for_delete)
async def process_delete(message: types.Message, state: FSMContext):
    """Обработка ввода времени до удаления"""
    delete_minutes = None
    
    if message.text and message.text != '-':
        try:
            delete_minutes = int(message.text)
            if delete_minutes < 0:
                raise ValueError
        except ValueError:
            await message.reply("❌ Введите корректное число минут или '-'")
            return
    
    data = await state.get_data()
    
    # Создаем пост
    post_id = f"post_{datetime.now().timestamp()}"
    new_post = ScheduledPost(
        id=post_id,
        chat_id=message.chat.id,
        content=data['content'],
        publish_time=data['publish_time'],
        delete_after_minutes=delete_minutes
    )
    
    # Сохраняем в хранилище
    post_storage.add(new_post)
    
    # Планируем публикацию
    asyncio.create_task(schedule_post_task(new_post))
    
    # Формируем ответ
    publish_time = new_post.publish_time_dt
    time_remaining = format_time_remaining(publish_time)
    
    response = (
        f"✅ <b>Пост запланирован!</b>\n\n"
        f"🆔 ID: <code>{post_id}</code>\n"
        f"📅 Публикация: {publish_time.strftime('%d.%m.%Y %H:%M')} NSK\n"
        f"⏳ Осталось: {time_remaining}\n"
    )
    
    if delete_minutes:
        delete_time = publish_time + timedelta(minutes=delete_minutes)
        response += f"🗑 Удаление: через {delete_minutes} мин. ({delete_time.strftime('%H:%M')} NSK)"
    else:
        response += "🗑 Удаление: не требуется"
    
    await message.reply(response, parse_mode=ParseMode.HTML)
    await state.finish()

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    """Обработчик команды /list - список запланированных постов"""
    posts = post_storage.get_all()
    
    if not posts:
        await message.reply("📭 Нет запланированных постов")
        return
    
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    response = "<b>📋 Запланированные посты:</b>\n\n"
    
    for post_id, post in posts.items():
        if post.status != PostStatus.SCHEDULED.value:
            continue
            
        publish_time = post.publish_time_dt
        if publish_time < now_nsk:
            continue
            
        time_remaining = format_time_remaining(publish_time)
        
        response += (
            f"🆔 <code>{post_id}</code>\n"
            f"📅 {publish_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏳ {time_remaining}\n"
            f"📝 {post.content[:50]}{'...' if len(post.content) > 50 else ''}\n\n"
        )
    
    await message.reply(response, parse_mode=ParseMode.HTML)

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Обработчик команды /cancel - отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("🤷 Нет активного действия")
        return
    
    await state.finish()
    await message.reply("✅ Действие отменено")

# ==================== ЗАДАЧИ ПЛАНИРОВЩИКА ====================

async def publish_post(post: ScheduledPost):
    """Публикация поста"""
    try:
        message = await bot.send_message(
            post.chat_id,
            post.content,
            parse_mode=ParseMode.HTML
        )
        
        # Обновляем статус поста
        post_storage.update(
            post.id,
            message_id=message.message_id,
            status=PostStatus.PUBLISHED.value
        )
        
        logging.info(f"✅ Пост {post.id} опубликован")
        
        # Если нужно удаление через время
        if post.delete_after_minutes:
            delete_time = post.publish_time_dt + timedelta(minutes=post.delete_after_minutes)
            delay = (delete_time - datetime.now(Config.NSK_TIMEZONE)).total_seconds()
            
            if delay > 0:
                await asyncio.sleep(delay)
                await delete_post(post.id)
                
    except Exception as e:
        logging.error(f"❌ Ошибка публикации поста {post.id}: {e}")
        post_storage.update(post.id, status=PostStatus.FAILED.value)

async def delete_post(post_id: str):
    """Удаление поста"""
    try:
        post = post_storage.get(post_id)
        if not post or not post.message_id:
            return
            
        await bot.delete_message(post.chat_id, post.message_id)
        post_storage.update(post_id, status=PostStatus.DELETED.value)
        logging.info(f"🗑 Пост {post_id} удален")
        
    except Exception as e:
        logging.error(f"❌ Ошибка удаления поста {post_id}: {e}")

async def schedule_post_task(post: ScheduledPost):
    """Планирование поста"""
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    publish_time = post.publish_time_dt
    
    # Вычисляем задержку до публикации
    delay = (publish_time - now_nsk).total_seconds()
    
    if delay > 0:
        await asyncio.sleep(delay)
        await publish_post(post)

async def check_scheduled_posts():
    """Проверка и запуск запланированных постов при старте"""
    now_nsk = datetime.now(Config.NSK_TIMEZONE)
    
    for post in post_storage.get_all().values():
        if post.status != PostStatus.SCHEDULED.value:
            continue
            
        publish_time = post.publish_time_dt
        
        # Если время публикации прошло
        if publish_time < now_nsk:
            # Проверяем, нужно ли удалить пост
            if post.delete_time and post.delete_time > now_nsk:
                # Время удаления еще не наступило, публикуем сейчас
                await publish_post(post)
            else:
                # Время удаления тоже прошло, помечаем как failed
                post_storage.update(post.id, status=PostStatus.FAILED.value)
        else:
            # Время еще не наступило, планируем
            asyncio.create_task(schedule_post_task(post))

# ==================== ЗАПУСК БОТА ====================

async def on_startup(dp):
    """Действия при запуске бота"""
    logging.info("🚀 Бот запускается...")
    await check_scheduled_posts()
    logging.info("✅ Бот готов к работе!")

async def on_shutdown(dp):
    """Действия при остановке бота"""
    logging.info("🛑 Бот останавливается...")
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