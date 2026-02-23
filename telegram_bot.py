"""
ИНТЕГРАЦИЯ С TELEGRAM
Пример использования AutoPostBot с Telegram Bot API
"""

from datetime import datetime, timedelta
import pytz
from bot import AutoPostBot


class TelegramAutoPostBot(AutoPostBot):
    """
    Расширенная версия AutoPostBot с интеграцией Telegram
    
    Использует: python-telegram-bot
    Установка: pip install python-telegram-bot
    """
    
    def __init__(self, telegram_token: str, chat_ids: list, storage_file: str = "posts.json"):
        """
        Инициализация Telegram бота
        
        Args:
            telegram_token: токен Telegram бота от BotFather
            chat_ids: список ID чатов для отправки уведомлений
            storage_file: файл для хранения постов
        """
        super().__init__(storage_file)
        
        self.telegram_token = telegram_token
        self.chat_ids = chat_ids
        
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            self.bot = Bot(token=telegram_token)
            self.TelegramError = TelegramError
            self.telegram_available = True
        except ImportError:
            print("⚠️  Telegram не установлен. Установите: pip install python-telegram-bot")
            self.telegram_available = False
    
    def _send_telegram_notification(self, message: str, chat_id: int = None) -> bool:
        """
        Отправить уведомление в Telegram
        
        Args:
            message: текст сообщения
            chat_id: ID чата (если не указан, отправляется во все chat_ids)
        
        Returns:
            True если успешно, False если ошибка
        """
        if not self.telegram_available:
            return False
        
        chat_ids = [chat_id] if chat_id else self.chat_ids
        
        for cid in chat_ids:
            try:
                self.bot.send_message(chat_id=cid, text=message)
            except self.TelegramError as e:
                print(f"❌ Ошибка Telegram: {e}")
                return False
        
        return True
    
    def publish_post(self, content: str, notify_telegram: bool = True, **kwargs) -> str:
        """
        Опубликовать пост с уведомлением в Telegram
        
        Args:
            content: содержание поста
            notify_telegram: отправить уведомление в Telegram
            **kwargs: дополнительные параметры для publish_post родителя
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if notify_telegram and post_id:
            delete_hours = kwargs.get('delete_after_hours')
            delete_text = f" (удалится через {delete_hours}ч)" if delete_hours else ""
            
            message = f"📝 Новый пост #{post_id}{delete_text}\n\n{content}"
            self._send_telegram_notification(message)
        
        return post_id
    
    def publish_post_at_time(self, content: str, notify_telegram: bool = True, **kwargs) -> str:
        """
        Опубликовать пост в определенное время с уведомлением в Telegram
        
        Args:
            content: содержание поста
            notify_telegram: отправить уведомление в Telegram
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post_at_time(content, **kwargs)
        
        if notify_telegram and post_id:
            scheduled_time = self.posts[post_id].get('scheduled_for', 'Unknown')
            message = f"📅 Пост запланирован #{post_id}\n" \
                     f"Время: {scheduled_time}\n\n{content}"
            self._send_telegram_notification(message)
        
        return post_id
    
    def delete_post(self, post_id: str, notify_telegram: bool = True) -> bool:
        """
        Удалить пост с уведомлением в Telegram
        
        Args:
            post_id: ID поста
            notify_telegram: отправить уведомление в Telegram
        
        Returns:
            True если успешно
        """
        post = self.get_post(post_id)
        content_preview = post['content'][:50] if post else "Unknown"
        
        result = super().delete_post(post_id)
        
        if result and notify_telegram:
            message = f"🗑️  Пост #{post_id} удален\n{content_preview}..."
            self._send_telegram_notification(message)
        
        return result
    
    def get_status_message(self) -> str:
        """Получить статус работы бота для Telegram"""
        nsk_time = self.get_current_nsk_time()
        total_posts = len(self.posts)
        published = len(self.list_posts(status='published'))
        scheduled = len(self.list_posts(status='scheduled'))
        
        message = f"""
📊 Статус бота:
━━━━━━━━━━━━━━━━━━━
🕐 Время NSK: {nsk_time.strftime('%Y-%m-%d %H:%M:%S')}
📝 Всего постов: {total_posts}
✅ Опубликовано: {published}
⏳ Запланировано: {scheduled}
🔧 Заданий: {len(self.get_jobs_info())}
"""
        return message


# ============================================================================
# TELEGRAM COMMANDS для использования с python-telegram-bot
# ============================================================================

class TelegramBotCommands:
    """Команды для Telegram интеграции"""
    
    @staticmethod
    async def start(update, context):
        """Команда /start"""
        await update.message.reply_text(
            "👋 Добро пожаловать в автопостинг бот!\n"
            "Используйте команды:\n"
            "/post - опубликовать пост\n"
            "/list - показать все посты\n"
            "/status - статус бота\n"
            "/help - справка"
        )
    
    @staticmethod
    async def help_command(update, context):
        """Команда /help"""
        help_text = """
🤖 Автопостинг Бот - Справка

📝 КОМАНДЫ:
/start - начало
/help - справка
/status - статус бота

📤 ПУБЛИКАЦИЯ:
/post <текст> - опубликовать пост сейчас
/post_schedule <текст> - запланировать пост
/scheduled - показать запланированные посты

📋 УПРАВЛЕНИЕ:
/list - все посты
/posts_published - только опубликованные
/delete <ID> - удалить пост

🕐 ВРЕМЯ:
/time - текущее время NSK
/convert <час:минута> <зона> - конвертировать время

⏰ УДАЛЕНИЕ:
/auto_delete <ID> <часов> - удалить пост через N часов

Пример: /post Привет, это мой первый пост!
"""
        await update.message.reply_text(help_text)
    
    @staticmethod
    async def status(update, context, bot_instance):
        """Команда /status"""
        await update.message.reply_text(
            bot_instance.get_status_message(),
            parse_mode='markdown'
        )


# ============================================================================
# ПРИМЕР ПОЛНОЙ ИНТЕГРАЦИИ С TELEGRAM
# ============================================================================

def setup_telegram_bot():
    """
    Пример полной настройки Telegram бота
    
    Требуется установка:
    pip install python-telegram-bot
    
    Использование:
    1. Создать бота в BotFather (@BotFather)
    2. Получить токен
    3. Узнать свой chat_id (отправить сообщение боту и получить ID)
    4. Заменить значения ниже
    """
    
    # ⚠️ ЗАМЕНИТЕ НА СВОИ ЗНАЧЕНИЯ!
    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_IDS = [123456789]  # Ваш chat_id (можно получить через @userinfobot)
    
    # Создание бота
    bot = TelegramAutoPostBot(
        telegram_token=TELEGRAM_TOKEN,
        chat_ids=CHAT_IDS
    )
    
    return bot


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

def example_telegram_usage():
    """Пример использования Telegram бота"""
    
    print("="*60)
    print("ПРИМЕР TELEGRAM ИНТЕГРАЦИИ")
    print("="*60)
    
    # Замените на реальные значения
    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = 123456789
    
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN":
        print("\n⚠️  Замените значения в коде:")
        print(f"  TELEGRAM_TOKEN = '{TELEGRAM_TOKEN}'")
        print(f"  CHAT_ID = {CHAT_ID}")
        print("\nДля получения токена:")
        print("  1. Напишите @BotFather в Telegram")
        print("  2. Команда /newbot")
        print("  3. Скопируйте полученный токен")
        print("\nДля получения chat_id:")
        print("  1. Напишите @userinfobot в Telegram")
        print("  2. Получите ваш ID")
        return
    
    try:
        # Создание бота (без фактической отправки в Telegram)
        bot = TelegramAutoPostBot(
            telegram_token=TELEGRAM_TOKEN,
            chat_ids=[CHAT_ID]
        )
        
        print("\n✅ Бот инициализирован")
        print(f"   Токен: {TELEGRAM_TOKEN[:20]}...")
        print(f"   Chat ID: {CHAT_ID}")
        
        # Пример публикации (в реальной работе будет отправлено в Telegram)
        print("\n📝 Пример публикации поста:")
        post_id = bot.publish_post(
            content="Это тестовый пост из Python!",
            notify_telegram=False  # Не отправляем реально
        )
        print(f"   Пост #{post_id} создан")
        
        # Пример получения статуса
        print("\n📊 Статус бота:")
        print(bot.get_status_message())
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    example_telegram_usage()
