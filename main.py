#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Bot "Маслянино Агрегатор"
Версия: 8.0 (ФИНАЛЬНАЯ)

GitHub: https://github.com/yourusername/maslyanino-bot

⚠️ ПЕРЕД ЗАПУСКОМ:
1. Создайте файл .env с BOT_TOKEN
2. Измените MAIN_ADMIN_ID в config.py на свой ID
3. Измените TARGET_GROUP_ID в config.py на ID своей группы
"""

import asyncio
import signal
import sys
from typing import Optional

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters
)
from loguru import logger

from config import Config
from database import Database
from keyboards import Keyboards
from account_manager import AccountManager
from admin_handlers import AdminHandlers
from vk_parser import VKParser
from tg_parser import TelegramParser
from message_formatter import MessageFormatter

# Состояния для ConversationHandler
TG_AUTH_PHONE, TG_AUTH_CODE, TG_AUTH_PASSWORD = range(13, 16)

class MaslyaninoBot:
    """Главный класс бота"""
    
    def __init__(self):
        self.config = Config
        self.db = Database(self.config.DATABASE_PATH)
        self.keyboards = Keyboards()
        self.formatter = MessageFormatter(self.config.BRAND_TAG)
        self.account_manager = AccountManager(self.db)
        
        self.vk_parser: Optional[VKParser] = None
        self.tg_parser: Optional[TelegramParser] = None
        self.application: Optional[Application] = None
        
        logger.info("✅ Бот инициализирован")
        logger.info(f"👑 Главный администратор: {self.config.MAIN_ADMIN_ID}")
        logger.info(f"📢 Целевая группа: {self.config.TARGET_GROUP_ID}")
    
    async def initialize(self):
        """Инициализация"""
        await self.db.init_db()
        
        # Добавляем главного администратора если его нет
        if not await self.db.is_admin(self.config.MAIN_ADMIN_ID):
            await self.db.add_admin(
                self.config.MAIN_ADMIN_ID,
                "main_admin",
                is_main=True
            )
            logger.info("👑 Главный администратор добавлен в БД")
        
        # Создаем стандартные темы если их нет
        topics = await self.db.get_topics()
        if not topics:
            default_topics = [
                ('podslushano', 101, 'Подслушано', '📌'),
                ('kuplyu', 102, 'Куплю', '🛒'),
                ('prodam', 103, 'Продам', '💰'),
                ('otdam', 104, 'Отдам', '🎁'),
                ('novosti', 105, 'Новости', '📢'),
                ('otdyh', 106, 'Место для отдыха', '🏞️')
            ]
            for topic_id, topic_num, name, emoji in default_topics:
                await self.db.add_topic({
                    'id': topic_id,
                    'topic_id': topic_num,
                    'name': name,
                    'emoji': emoji
                })
            logger.info("📂 Стандартные темы созданы")
    
    async def start_parsers(self):
        """Запуск парсеров"""
        
        # VK парсер
        vk_token = await self.account_manager.get_vk_token()
        if vk_token:
            self.vk_parser = VKParser(
                vk_token=vk_token,
                db=self.db,
                formatter=self.formatter,
                check_interval=self.config.VK_CHECK_INTERVAL
            )
            asyncio.create_task(self.vk_parser.start())
            logger.info("▶️ VK парсер запущен")
        else:
            logger.warning("⚠️ VK токен не настроен. Используйте /account для настройки")
        
        # Telegram парсер
        tg_client = await self.account_manager.get_tg_client()
        if tg_client:
            self.tg_parser = TelegramParser(
                client=tg_client,
                db=self.db,
                formatter=self.formatter,
                target_group_id=self.config.TARGET_GROUP_ID,
                check_interval=self.config.TG_CHECK_INTERVAL
            )
            asyncio.create_task(self.tg_parser.start())
            logger.info("▶️ Telegram парсер запущен")
        else:
            logger.warning("⚠️ Telegram аккаунт не настроен. Используйте /account для настройки")
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        handlers = AdminHandlers(self.db, self.keyboards, self.account_manager)
        
        # Команды
        self.application.add_handler(CommandHandler("start", handlers.start))
        self.application.add_handler(CommandHandler("menu", handlers.main_menu))
        self.application.add_handler(CommandHandler("help", handlers.help))
        self.application.add_handler(CommandHandler("account", handlers.account_menu))
        self.application.add_handler(CommandHandler("status", handlers.status))
        self.application.add_handler(CommandHandler("stats", handlers.stats))
        
        # Callback кнопки
        self.application.add_handler(CallbackQueryHandler(handlers.handle_callback))
        
        # Разговор для авторизации Telegram
        tg_auth_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                handlers.tg_auth_start, 
                pattern="^tg_login$"
            )],
            states={
                TG_AUTH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.tg_auth_phone)],
                TG_AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.tg_auth_code)],
                TG_AUTH_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.tg_auth_password)],
            },
            fallbacks=[CommandHandler("cancel", handlers.cancel)],
            per_message=True
        )
        self.application.add_handler(tg_auth_conv)
    
    async def post_init(self, application):
        """После инициализации"""
        logger.info(f"✅ Бот @{application.bot.username} запущен")
        
        # Отправляем приветствие главному админу
        try:
            await application.bot.send_message(
                chat_id=self.config.MAIN_ADMIN_ID,
                text=(
                    "🤖 **Маслянино Агрегатор запущен!**\n\n"
                    "Используйте /menu для управления ботом.\n"
                    "Или /account для настройки аккаунтов."
                ),
                parse_mode='Markdown'
            )
        except:
            pass
    
    async def shutdown(self):
        """Завершение работы"""
        logger.info("🛑 Завершение работы...")
        
        if self.vk_parser:
            self.vk_parser.stop()
        
        if self.tg_parser:
            await self.tg_parser.stop()
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("👋 Бот остановлен")
    
    def signal_handler(self, sig, frame):
        """Обработчик сигналов"""
        logger.info(f"Получен сигнал {sig}")
        asyncio.create_task(self.shutdown())
        sys.exit(0)
    
    async def run(self):
        """Запуск"""
        try:
            # Инициализация
            await self.initialize()
            
            # Создание приложения
            self.application = Application.builder() \
                .token(self.config.BOT_TOKEN) \
                .post_init(self.post_init) \
                .build()
            
            # Настройка обработчиков
            self.setup_handlers()
            
            # Запуск парсеров
            await self.start_parsers()
            
            # Запуск бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ Бот готов к работе")
            
            # Держим запущенным
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            await self.shutdown()

def main():
    """Точка входа"""
    bot = MaslyaninoBot()
    
    # Обработчики сигналов
    signal.signal(signal.SIGINT, bot.signal_handler)
    signal.signal(signal.SIGTERM, bot.signal_handler)
    
    # Запуск
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()