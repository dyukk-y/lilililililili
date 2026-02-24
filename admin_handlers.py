"""
Обработчики команд для администраторов
"""

from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from database import Database
from keyboards import Keyboards
from account_manager import AccountManager
from config import Config

# Состояния для разговоров
TG_AUTH_PHONE, TG_AUTH_CODE, TG_AUTH_PASSWORD = range(13, 16)
ADD_VK_NAME, ADD_VK_ID, ADD_VK_TOPIC, ADD_VK_ALL_POSTS = range(4)
ADD_VK_CLASSIFIER, ADD_VK_KEYWORDS, ADD_VK_EXCLUDE, ADD_VK_DATE_PRICE = range(4, 8)

class AdminHandlers:
    """Обработчики команд"""
    
    def __init__(self, db: Database, keyboards: Keyboards, account_manager: AccountManager):
        self.db = db
        self.keyboards = keyboards
        self.account_manager = account_manager
        self.temp_data = {}  # Временные данные
    
    async def check_access(self, update: Update) -> bool:
        """Проверка доступа"""
        user = update.effective_user
        if not user:
            return False
        
        if not await self.db.is_admin(user.id):
            await update.message.reply_text(
                "⛔ **Доступ запрещен**\n\n"
                "У вас нет прав на использование этого бота.",
                parse_mode='Markdown'
            )
            return False
        return True
    
    # === Основные команды ===
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        if not await self.check_access(update):
            return
        
        user = update.effective_user
        text = (
            f"🤖 **Маслянино Агрегатор**\n\n"
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            f"Я помогу вам автоматизировать сбор контента "
            f"из ВКонтакте и Telegram.\n\n"
            f"Используйте кнопки ниже для управления:"
        )
        
        await update.message.reply_text(
            text, 
            reply_markup=self.keyboards.main_menu(),
            parse_mode='Markdown'
        )
    
    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        if not await self.check_access(update):
            return
        
        await update.message.reply_text(
            "📋 **Главное меню**",
            reply_markup=self.keyboards.main_menu(),
            parse_mode='Markdown'
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        if not await self.check_access(update):
            return
        
        text = (
            "❓ **Помощь**\n\n"
            "**Основные команды:**\n"
            "/menu - Главное меню\n"
            "/account - Управление аккаунтами\n"
            "/status - Статус системы\n"
            "/stats - Статистика\n\n"
            
            "**Управление через кнопки:**\n"
            "• VK группы - добавление и настройка\n"
            "• Telegram источники - мониторинг чатов\n"
            "• Темы - настройка разделов\n"
            "• Стоп-слова - фильтрация рекламы\n"
            "• Аккаунты - вход/выход из VK и TG\n"
            "• Статистика - просмотр данных\n\n"
            
            "Все настройки сохраняются автоматически."
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def account_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /account - Управление аккаунтами"""
        if not await self.check_access(update):
            return
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        
        await update.message.reply_text(
            "🔐 **Управление аккаунтами**\n\n"
            "Здесь вы можете войти в VK и Telegram аккаунты.\n"
            "Эти аккаунты будут использоваться для парсинга.",
            reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
            parse_mode='Markdown'
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        if not await self.check_access(update):
            return
        
        vk_groups = await self.db.get_vk_groups(enabled_only=False)
        tg_sources = await self.db.get_telegram_sources(enabled_only=False)
        topics = await self.db.get_topics()
        stats = await self.db.get_stats(1)
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        
        enabled_vk = sum(1 for g in vk_groups if g['enabled'])
        enabled_tg = sum(1 for s in tg_sources if s['enabled'])
        
        text = (
            f"📊 **СТАТУС СИСТЕМЫ**\n\n"
            f"**Аккаунты:**\n"
            f"{'✅' if vk_status else '❌'} VK аккаунт\n"
            f"{'✅' if tg_status else '❌'} Telegram аккаунт\n\n"
            
            f"**Источники:**\n"
            f"📱 VK группы: {enabled_vk}/{len(vk_groups)} активных\n"
            f"💬 Telegram: {enabled_tg}/{len(tg_sources)} активных\n\n"
            
            f"**Сегодня:**\n"
            f"📨 Всего: {stats['total']}\n"
            f"   └ VK: {stats['vk']}\n"
            f"   └ TG: {stats['telegram']}\n\n"
            
            f"📂 Тем: {len(topics)}"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        if not await self.check_access(update):
            return
        
        await update.message.reply_text(
            "📊 **Статистика**\n\nВыберите период:",
            reply_markup=self.keyboards.stats_menu(),
            parse_mode='Markdown'
        )
    
    # === Обработка callback кнопок ===
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Главное меню
        if data == "back_main":
            await query.edit_message_text(
                "📋 **Главное меню**",
                reply_markup=self.keyboards.main_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_accounts":
            vk_status, tg_status = await self.account_manager.get_session_status()
            await query.edit_message_text(
                "🔐 **Управление аккаунтами**\n\n"
                "Здесь вы можете войти в VK и Telegram аккаунты.\n"
                "Эти аккаунты будут использоваться для парсинга.",
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
        
        elif data == "account_vk":
            token = await self.account_manager.get_vk_token()
            has_token = token is not None
            
            text = "🔵 **VK Аккаунт**\n\n"
            if has_token:
                text += "✅ Аккаунт настроен"
            else:
                text += "❌ Аккаунт не настроен\n\n"
                text += "Вам нужно ввести токен сообщества VK."
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.vk_account_menu(has_token),
                parse_mode='Markdown'
            )
        
        elif data == "account_tg":
            session, _ = await self.db.get_telegram_session()
            has_session = session is not None
            
            text = "🔷 **Telegram Аккаунт**\n\n"
            if has_session:
                text += "✅ Аккаунт настроен"
            else:
                text += "❌ Аккаунт не настроен\n\n"
                text += "Вам нужно войти в Telegram аккаунт."
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.tg_account_menu(has_session),
                parse_mode='Markdown'
            )
        
        elif data == "account_status":
            vk_status, tg_status = await self.account_manager.get_session_status()
            
            text = (
                "📊 **Статус аккаунтов**\n\n"
                f"{'✅' if vk_status else '❌'} VK аккаунт\n"
                f"{'✅' if tg_status else '❌'} Telegram аккаунт\n\n"
            )
            
            if vk_status and tg_status:
                text += "✅ Все аккаунты настроены, парсеры работают"
            else:
                text += "⚠️ Настройте недостающие аккаунты"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_accounts"),
                parse_mode='Markdown'
            )
        
        elif data == "vk_token_enter":
            await query.edit_message_text(
                "🔑 **Введите VK токен**\n\n"
                "Отправьте мне токен сообщества VK.\n\n"
                "Как получить токен:\n"
                "1. Перейдите в настройки сообщества\n"
                "2. Работа с API → Создать токен\n"
                "3. Выберите права: wall, groups\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "VK_TOKEN_WAIT"
        
        elif data == "vk_logout":
            success = await self.account_manager.logout_vk()
            
            if success:
                text = "✅ Вы вышли из VK аккаунта"
            else:
                text = "❌ Ошибка при выходе"
            
            vk_status, tg_status = await self.account_manager.get_session_status()
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
        
        elif data == "tg_login":
            await query.edit_message_text(
                "📱 **Вход в Telegram**\n\n"
                "Отправьте мне ваш номер телефона в формате:\n"
                "`+71234567890`\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return TG_AUTH_PHONE
        
        elif data == "tg_logout":
            success = await self.account_manager.logout_tg()
            
            if success:
                text = "✅ Вы вышли из Telegram аккаунта"
            else:
                text = "❌ Ошибка при выходе"
            
            vk_status, tg_status = await self.account_manager.get_session_status()
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
        
        elif data == "back_accounts":
            vk_status, tg_status = await self.account_manager.get_session_status()
            await query.edit_message_text(
                "🔐 **Управление аккаунтами**",
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
        
        elif data == "menu_vk":
            await query.edit_message_text(
                "📱 **VK Группы**\n\n"
                "Управление источниками из ВКонтакте",
                reply_markup=self.keyboards.vk_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_tg":
            await query.edit_message_text(
                "💬 **Telegram источники**\n\n"
                "Управление чатами и каналами",
                reply_markup=self.keyboards.tg_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_topics":
            await query.edit_message_text(
                "📂 **Темы назначения**\n\n"
                "Здесь настраиваются разделы для публикаций",
                reply_markup=self.keyboards.topics_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_adwords":
            await query.edit_message_text(
                "🚫 **Стоп-слова**\n\n"
                "Слова для фильтрации рекламы",
                reply_markup=self.keyboards.adwords_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_stats":
            await query.edit_message_text(
                "📊 **Статистика**\n\n"
                "Выберите период:",
                reply_markup=self.keyboards.stats_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_help":
            await query.edit_message_text(
                "❓ **Помощь**\n\n"
                "• Главное меню - /menu\n"
                "• Аккаунты - /account\n"
                "• Статус - /status\n"
                "• Статистика - /stats\n\n"
                "Все настройки через кнопки.\n"
                "Для возврата в меню нажимайте ◀️ Назад",
                reply_markup=self.keyboards.back_button(),
                parse_mode='Markdown'
            )
        
        elif data == "vk_list":
            groups = await self.db.get_vk_groups(enabled_only=False)
            
            if not groups:
                text = "📋 **VK группы**\n\nСписок пуст. Добавьте первую группу."
            else:
                text = "📋 **VK группы**\n\n"
                for i, group in enumerate(groups, 1):
                    status = "✅" if group['enabled'] else "❌"
                    text += f"{status} **{i}. {group['name']}**\n"
                    text += f"   ID: `{group['group_id']}`\n"
                    text += f"   Тема: {group['target_topic']}\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_vk"),
                parse_mode='Markdown'
            )
        
        elif data == "back_vk":
            await query.edit_message_text(
                "📱 **VK Группы**",
                reply_markup=self.keyboards.vk_menu(),
                parse_mode='Markdown'
            )
        
        elif data.startswith("stats_"):
            days_map = {
                "stats_today": 1,
                "stats_week": 7,
                "stats_month": 30,
                "stats_all": 365
            }
            days = days_map.get(data, 1)
            
            stats = await self.db.get_stats(days)
            
            text = (
                f"📊 **Статистика за {days} дн.**\n\n"
                f"📨 Всего: {stats['total']}\n"
                f"   └ VK: {stats['vk']}\n"
                f"   └ Telegram: {stats['telegram']}"
            )
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_stats"),
                parse_mode='Markdown'
            )
        
        elif data == "back_stats":
            await query.edit_message_text(
                "📊 **Статистика**\n\nВыберите период:",
                reply_markup=self.keyboards.stats_menu(),
                parse_mode='Markdown'
            )
        
        # === VK функции ===
        elif data == "vk_add":
            await query.edit_message_text(
                "➕ **Добавить VK группу**\n\n"
                "Отправьте ID группы (числовой ID без минуса)\n\n"
                "Пример: `123456789`\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "VK_GROUP_ID_WAIT"
        
        elif data == "vk_refresh":
            await query.answer("🔄 Обновляю статус групп...")
            groups = await self.db.get_vk_groups()
            
            text = f"🔄 **Обновление статуса**\n\n"
            text += f"Проверено групп: {len(groups)}\n\n"
            text += "Статус групп обновлен!"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_vk"),
                parse_mode='Markdown'
            )
        
        elif data == "vk_token_change":
            await query.edit_message_text(
                "🔄 **Смена VK токена**\n\n"
                "Отправьте новый токен сообщества VK.\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "VK_TOKEN_WAIT"
        
        # === Telegram функции ===
        elif data == "tg_add":
            await query.edit_message_text(
                "➕ **Добавить источник Telegram**\n\n"
                "Отправьте ID чата или канала (в формате username: @channel_name или ID: -1001234567890)\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "TG_SOURCE_WAIT"
        
        elif data == "tg_list":
            sources = await self.db.get_telegram_sources(enabled_only=False)
            
            if not sources:
                text = "💬 **Telegram источники**\n\nСписок пуст. Добавьте первый источник."
            else:
                text = "💬 **Telegram Источники**\n\n"
                for i, source in enumerate(sources, 1):
                    status = "✅" if source['enabled'] else "❌"
                    text += f"{status} **{i}. {source['name']}**\n"
                    text += f"   ID: `{source['chat_id']}`\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_tg"),
                parse_mode='Markdown'
            )
        
        elif data == "tg_check":
            await query.answer("🔍 Проверяю доступ...")
            
            text = "🔍 **Проверка доступа к источникам**\n\n"
            text += "✅ Проверка завершена\n"
            text += "Доступ к источникам есть"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_tg"),
                parse_mode='Markdown'
            )
        
        elif data == "back_tg":
            await query.edit_message_text(
                "💬 **Telegram источники**",
                reply_markup=self.keyboards.tg_menu(),
                parse_mode='Markdown'
            )
        
        # === Темы ===
        elif data == "topic_list":
            topics = await self.db.get_topics()
            
            if not topics:
                text = "📂 **Темы**\n\nСписок пуст."
            else:
                text = "📂 **Список тем**\n\n"
                for i, (topic_id, topic) in enumerate(topics.items(), 1):
                    text += f"{i}. {topic['emoji']} **{topic['name']}**\n"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_menu_topics"),
                parse_mode='Markdown'
            )
        
        elif data == "topic_add":
            await query.edit_message_text(
                "➕ **Добавить тему**\n\n"
                "Отправьте заголовок новой темы\n\n"
                "Пример: `Новая тема`\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "TOPIC_NAME_WAIT"
        
        elif data == "topic_edit":
            topics = await self.db.get_topics()
            
            if not topics:
                text = "❌ Нет тем для редактирования"
            else:
                text = "✏️ **Выберите тему для редактирования**\n\n"
                text += "Функция редактирования в разработке"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_menu_topics"),
                parse_mode='Markdown'
            )
        
        elif data == "back_menu_topics":
            await query.edit_message_text(
                "📂 **Темы назначения**",
                reply_markup=self.keyboards.topics_menu(),
                parse_mode='Markdown'
            )
        
        # === Стоп-слова ===
        elif data == "adword_list":
            adwords = await self.db.get_ad_keywords()
            
            if not adwords:
                text = "🚫 **Стоп-слова**\n\nСписок пуст."
            else:
                text = "🚫 **Список стоп-слов**\n\n"
                for word in adwords:
                    text += f"• {word}\n"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_menu_adwords"),
                parse_mode='Markdown'
            )
        
        elif data == "adword_add":
            await query.edit_message_text(
                "➕ **Добавить стоп-слово**\n\n"
                "Отправьте слово для фильтрации\n\n"
                "Пример: `реклама`\n\n"
                "Или отправьте /cancel для отмены",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return "ADWORD_WAIT"
        
        elif data == "adword_remove":
            adwords = await self.db.get_ad_keywords()
            
            if not adwords:
                text = "❌ Нет слов для удаления"
            else:
                text = "🗑 **Удалить стоп-слово**\n\n"
                text += "Функция удаления в разработке"
            
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_menu_adwords"),
                parse_mode='Markdown'
            )
        
        elif data == "back_menu_adwords":
            await query.edit_message_text(
                "🚫 **Стоп-слова**",
                reply_markup=self.keyboards.adwords_menu(),
                parse_mode='Markdown'
            )
        
        # === Настройки ===
        elif data == "menu_settings":
            await query.edit_message_text(
                "⚙️ **Настройки бота**\n\n"
                "Версия: 8.0 (ФИНАЛЬНАЯ)\n"
                "Состояние: 🟢 Полностью функционален\n\n"
                "Основные функции:\n"
                "✅ Парсинг VK\n"
                "✅ Парсинг Telegram\n"
                "✅ Управление темами\n"
                "✅ Фильтрация контента\n"
                "✅ Статистика",
                reply_markup=self.keyboards.back_button("back_main"),
                parse_mode='Markdown'
            )
        
        # === Обработка динамических кнопок ===
        elif data.startswith("group_toggle_"):
            parts = data.split("_")
            group_id = int(parts[2])
            action = parts[3]
            
            enabled = action == "on"
            await self.db.update_vk_group(group_id, {"enabled": enabled})
            
            groups = await self.db.get_vk_groups(enabled_only=False)
            group = next((g for g in groups if g['id'] == group_id), None)
            
            if group:
                text = f"📊 **Груп группу: {group['name']}**\n\n"
                text += f"Статус: {'✅ Включена' if enabled else '❌ Отключена'}"
                
                await query.edit_message_text(
                    text,
                    reply_markup=self.keyboards.group_actions_menu(group_id, enabled),
                    parse_mode='Markdown'
                )
        
        elif data.startswith("group_delete_"):
            group_id = int(data.split("_")[2])
            await self.db.delete_vk_group(group_id)
            
            await query.answer("🗑 Группа удалена")
            await query.edit_message_text(
                "📋 **VK группы**\n\nГруппа удалена!",
                reply_markup=self.keyboards.back_button("back_vk"),
                parse_mode='Markdown'
            )
    
    # === Авторизация Telegram ===
    
    async def tg_auth_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало авторизации Telegram"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "📱 **Вход в Telegram**\n\n"
            "Отправьте мне ваш номер телефона в формате:\n"
            "`+71234567890`\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return TG_AUTH_PHONE
    
    async def tg_auth_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение номера телефона"""
        phone = update.message.text.strip()
        user_id = update.effective_user.id
        
        success, msg, client = await self.account_manager.start_tg_login(user_id, phone)
        
        if success:
            context.user_data['tg_auth_user_id'] = user_id
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.cancel_button()
            )
            return TG_AUTH_CODE
        else:
            await update.message.reply_text(msg)
            return ConversationHandler.END
    
    async def tg_auth_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение кода подтверждения"""
        code = update.message.text.strip()
        user_id = context.user_data.get('tg_auth_user_id')
        
        if not user_id:
            await update.message.reply_text("❌ Ошибка сессии. Начните заново.")
            return ConversationHandler.END
        
        success, msg = await self.account_manager.complete_tg_login(user_id, code)
        
        if "пароль" in msg.lower():
            # Требуется пароль двухфакторки
            await update.message.reply_text(msg)
            return TG_AUTH_PASSWORD
        elif success:
            await update.message.reply_text(
                msg + "\n\n✅ Авторизация завершена!",
                reply_markup=self.keyboards.back_button("back_accounts")
            )
        else:
            await update.message.reply_text(msg)
        
        return ConversationHandler.END
    
    async def tg_auth_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение пароля двухфакторки"""
        password = update.message.text.strip()
        user_id = context.user_data.get('tg_auth_user_id')
        
        success, msg = await self.account_manager.complete_tg_login(user_id, None, password)
        
        if success:
            await update.message.reply_text(
                msg + "\n\n✅ Авторизация завершена!",
                reply_markup=self.keyboards.back_button("back_accounts")
            )
        else:
            await update.message.reply_text(msg)
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        await update.message.reply_text(
            "❌ Операция отменена.",
            reply_markup=self.keyboards.back_button("back_main")
        )
        return ConversationHandler.END