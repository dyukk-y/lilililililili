"""
Парсер Telegram чатов
Использует пользовательский аккаунт (Telethon)
"""

import asyncio
import hashlib
from typing import Optional, List, Dict
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.types import Message, User

from database import Database
from message_formatter import MessageFormatter

class TelegramParser:
    """Парсер Telegram чатов"""
    
    def __init__(self, client: TelegramClient, db: Database, formatter: MessageFormatter,
                 target_group_id: int, check_interval: int = 30):
        self.client = client
        self.db = db
        self.formatter = formatter
        self.target_group_id = target_group_id
        self.check_interval = check_interval
        self.is_running = False
        self.sources: List[Dict] = []
    
    async def start(self):
        """Запуск парсера"""
        self.is_running = True
        
        # Загружаем источники
        await self.load_sources()
        
        # Регистрируем обработчик новых сообщений
        @self.client.on(events.NewMessage)
        async def handler(event):
            await self.handle_new_message(event.message)
        
        logger.info("✅ Telegram парсер запущен")
        
        # Держим соединение
        while self.is_running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Остановка парсера"""
        self.is_running = False
        logger.info("Telegram парсер остановлен")
    
    async def load_sources(self):
        """Загрузка источников из БД"""
        self.sources = await self.db.get_telegram_sources(enabled_only=True)
        logger.info(f"Загружено {len(self.sources)} Telegram источников")
    
    async def handle_new_message(self, message: Message):
        """Обработка нового сообщения"""
        try:
            # Определяем источник
            chat_id = message.chat_id
            topic_id = message.reply_to.reply_to_msg_id if message.reply_to else None
            
            source = self.find_source(chat_id, topic_id)
            if not source:
                return
            
            # Проверяем дубликат
            message_id = str(message.id)
            if await self.db.is_processed('telegram', message_id, str(chat_id)):
                return
            
            # Текст сообщения
            text = message.text or message.caption or ""
            if not text and not source['all_posts']:
                return
            
            # Автор
            sender = await message.get_sender()
            author_username = sender.username if isinstance(sender, User) else None
            author_id = sender.id if sender else None
            
            # Темы
            topics = await self.db.get_topics()
            
            # Определяем тему
            target_topic = await self.determine_target_topic(text, source, topics)
            if not target_topic:
                return
            
            # Форматируем
            formatted_text = self.formatter.format_telegram_message(
                text, target_topic, author_username, author_id
            )
            
            # Ссылки
            source_link = await self.get_message_link(message)
            
            author_link = None
            if source['show_author']:
                if author_username:
                    author_link = f"https://t.me/{author_username}"
                elif author_id:
                    author_link = f"tg://user?id={author_id}"
            
            # TODO: Отправка в Telegram группу
            logger.info(f"✅ Новое сообщение из TG: {source['name']} -> {target_topic['name']}")
            
            # Отмечаем обработанным
            await self.db.mark_processed(
                'telegram', message_id, str(chat_id),
                target_topic['topic_id'],
                hashlib.md5(text.encode()).hexdigest()
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    def find_source(self, chat_id: int, topic_id: Optional[int]) -> Optional[Dict]:
        """Поиск источника по ID чата и темы"""
        for source in self.sources:
            if source['chat_id'] == chat_id:
                if source['topic_id']:
                    if source['topic_id'] == topic_id:
                        return source
                else:
                    return source
        return None
    
    async def determine_target_topic(self, text: str, source: Dict, topics: Dict) -> Optional[Dict]:
        """Определение целевой темы"""
        text_lower = text.lower()
        
        if source['all_posts']:
            return topics.get(source['target_topic'])
        
        if source['classifier_type'] == 'buy_sell':
            if any(word in text_lower for word in ['отдам', 'даром', 'бесплатно']):
                return topics.get('otdam')
            elif any(word in text_lower for word in ['куплю', 'ищу', 'нужен', 'приобрету']):
                return topics.get('kuplyu')
            elif any(word in text_lower for word in ['продам', 'продаю', 'реализую', 'цена']):
                return topics.get('prodam')
            else:
                return None
        
        elif source['classifier_type'] == 'keywords' and source['keywords']:
            if any(keyword.lower() in text_lower for keyword in source['keywords']):
                return topics.get(source['target_topic'])
        
        return None
    
    async def get_message_link(self, message: Message) -> str:
        """Получение ссылки на сообщение"""
        try:
            chat = await message.get_chat()
            chat_username = chat.username if hasattr(chat, 'username') else None
            
            if chat_username:
                base = f"https://t.me/{chat_username}"
            else:
                chat_id = str(chat.id).replace('-100', '')
                base = f"https://t.me/c/{chat_id}"
            
            link = f"{base}/{message.id}"
            
            if message.reply_to and hasattr(message.reply_to, 'reply_to_msg_id'):
                thread = message.reply_to.reply_to_msg_id
                if thread:
                    link += f"?thread={thread}"
            
            return link
            
        except Exception as e:
            logger.error(f"Ошибка создания ссылки: {e}")
            return ""