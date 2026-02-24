"""
Конфигурация бота
Только токен берется из .env, остальное задается в коде
"""

import os
from dotenv import load_dotenv
from loguru import logger

# Загружаем .env файл
load_dotenv()

class Config:
    """Конфигурация бота"""
    
    # Telegram Bot Token (из .env)
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        raise ValueError(
            "\n❌ BOT_TOKEN не найден в .env файле!\n"
            "Создайте файл .env и добавьте:\n"
            "BOT_TOKEN=ваш_токен_от_@BotFather\n"
        )
    
    # ⚠️ ИЗМЕНИТЕ НА СВОИ ЗНАЧЕНИЯ ⚠️
    MAIN_ADMIN_ID = 1174432700  # Ваш Telegram ID (узнать у @userinfobot)
    TARGET_GROUP_ID = -1003595378977 # ID вашей группы (узнать у @getidsbot)
    
    # Настройки парсеров (можно менять)
    VK_CHECK_INTERVAL = 60  # Проверка VK раз в 60 секунд
    TG_CHECK_INTERVAL = 30  # Проверка Telegram раз в 30 секунд
    
    # База данных
    DATABASE_PATH = 'bot_database.db'
    
    # Бренд (добавляется в каждый пост)
    BRAND_TAG = "@maslyanino"
    
    # Настройки логирования
    LOG_LEVEL = "INFO"
    LOG_FILE = "bot.log"
    
    @classmethod
    def setup_logging(cls):
        """Настройка логирования"""
        logger.remove()
        
        # Лог в файл
        logger.add(
            cls.LOG_FILE,
            rotation="10 MB",
            retention="30 days",
            level=cls.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        # Лог в консоль (цветной)
        logger.add(
            lambda msg: print(msg),
            level=cls.LOG_LEVEL,
            format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | <cyan>{message}</cyan>"
        )
        
        return logger

# Создаем логгер
logger = Config.setup_logging()
logger.info("✅ Конфигурация загружена")