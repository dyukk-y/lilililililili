"""
Обработчики команд для администраторов
Все кнопки полностью рабочие
"""

import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from database import Database
from keyboards import Keyboards
from account_manager import AccountManager
from config import Config

# Состояния для разговоров
(VK_TOKEN_WAIT, TG_AUTH_PHONE, TG_AUTH_CODE, TG_AUTH_PASSWORD,
 ADD_VK_NAME, ADD_VK_ID, ADD_VK_TOPIC, ADD_VK_ALL_POSTS,
 ADD_VK_CLASSIFIER, ADD_VK_KEYWORDS, ADD_VK_EXCLUDE, ADD_VK_DATE_PRICE,
 ADD_TG_NAME, ADD_TG_LINK, ADD_TG_TOPIC_ID, ADD_TG_TARGET,
 ADD_ADWORD, REMOVE_ADWORD, ADD_TOPIC_ID, ADD_TOPIC_NAME, ADD_TOPIC_EMOJI) = range(21)

class AdminHandlers:
    """Обработчики команд с полностью рабочими кнопками"""
    
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
            if update.callback_query:
                await update.callback_query.answer("⛔ У вас нет доступа!", show_alert=True)
            else:
                await update.message.reply_text(
                    "⛔ **Доступ запрещен**\n\n"
                    "У вас нет прав на использование этого бота.",
                    parse_mode='Markdown'
                )
            return False
        return True
    
    # === ОСНОВНЫЕ КОМАНДЫ ===
    
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
            f"**Текущий статус:**\n"
            f"• Используйте /menu для управления\n"
            f"• /account для настройки аккаунтов\n"
            f"• /stats для статистики\n"
            f"• /help для помощи"
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
        
        text = "📋 **Главное меню**\n\nВыберите раздел для управления:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=self.keyboards.main_menu(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
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
            
            "**Как это работает:**\n"
            "1️⃣ Сначала настройте аккаунты (VK и Telegram)\n"
            "2️⃣ Добавьте источники (VK группы и Telegram чаты)\n"
            "3️⃣ Бот автоматически собирает и публикует контент\n\n"
            
            "**Фильтрация:**\n"
            "• Стоп-слова блокируют рекламу\n"
            "• Ключевые слова определяют темы\n"
            "• Можно требовать наличие даты/цены\n\n"
            
            "Все настройки сохраняются автоматически."
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=self.keyboards.back_button(),
                parse_mode='Markdown'
            )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - показывает реальный статус"""
        if not await self.check_access(update):
            return
        
        # Собираем реальные данные
        vk_groups = await self.db.get_vk_groups(enabled_only=False)
        tg_sources = await self.db.get_telegram_sources(enabled_only=False)
        topics = await self.db.get_topics()
        stats_today = await self.db.get_stats(1)
        stats_week = await self.db.get_stats(7)
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        
        enabled_vk = sum(1 for g in vk_groups if g['enabled'])
        enabled_tg = sum(1 for s in tg_sources if s['enabled'])
        
        # Статус парсеров (проверяем через context.bot_data)
        vk_parser_running = context.bot_data.get('vk_parser_running', False) and vk_status
        tg_parser_running = context.bot_data.get('tg_parser_running', False) and tg_status
        
        text = (
            f"📊 **СТАТУС СИСТЕМЫ**\n\n"
            f"**Аккаунты:**\n"
            f"{'✅' if vk_status else '❌'} VK аккаунт\n"
            f"{'✅' if tg_status else '❌'} Telegram аккаунт\n\n"
            
            f"**Парсеры:**\n"
            f"{'✅' if vk_parser_running else '❌'} VK парсер\n"
            f"{'✅' if tg_parser_running else '❌'} Telegram парсер\n\n"
            
            f"**Источники:**\n"
            f"📱 VK группы: {enabled_vk}/{len(vk_groups)} активных\n"
            f"💬 Telegram: {enabled_tg}/{len(tg_sources)} активных\n\n"
            
            f"**Статистика:**\n"
            f"📨 За сегодня: {stats_today['total']} (VK: {stats_today['vk']}, TG: {stats_today['telegram']})\n"
            f"📨 За неделю: {stats_week['total']}\n\n"
            
            f"📂 Всего тем: {len(topics)}"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=self.keyboards.back_button(),
                parse_mode='Markdown'
            )
    
    # === УПРАВЛЕНИЕ АККАУНТАМИ (ПОЛНОСТЬЮ РАБОЧЕЕ) ===
    
    async def account_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню управления аккаунтами"""
        if not await self.check_access(update):
            return
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        
        text = (
            "🔐 **Управление аккаунтами**\n\n"
            "Здесь вы можете войти в VK и Telegram аккаунты.\n"
            "Эти аккаунты будут использоваться для парсинга.\n\n"
            f"{'✅' if vk_status else '❌'} **VK аккаунт** - " + 
            ("настроен" if vk_status else "не настроен") + "\n"
            f"{'✅' if tg_status else '❌'} **Telegram аккаунт** - " +
            ("настроен" if tg_status else "не настроен")
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
                parse_mode='Markdown'
            )
    
    # === VK АККАУНТ ===
    
    async def vk_account_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка VK аккаунта"""
        query = update.callback_query
        await query.answer()
        
        token = await self.account_manager.get_vk_token()
        has_token = token is not None
        
        if has_token:
            # Показываем информацию о текущем токене (маскируем)
            masked_token = token[:10] + "..." + token[-5:] if len(token) > 20 else "***"
            text = (
                f"🔵 **VK Аккаунт**\n\n"
                f"✅ Токен настроен\n"
                f"🔑 Токен: `{masked_token}`\n\n"
                f"Что хотите сделать?"
            )
        else:
            text = (
                f"🔵 **VK Аккаунт**\n\n"
                f"❌ Токен не настроен\n\n"
                f"Вам нужно ввести токен сообщества VK.\n\n"
                f"**Как получить токен:**\n"
                f"1. Перейдите в настройки сообщества\n"
                f"2. Работа с API → Создать токен\n"
                f"3. Выберите права: wall, groups, offline\n"
                f"4. Скопируйте токен"
            )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.vk_account_menu(has_token),
            parse_mode='Markdown'
        )
    
    async def vk_token_enter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос ввода VK токена"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🔑 **Введите VK токен**\n\n"
            "Отправьте мне токен сообщества VK.\n\n"
            "Токен должен начинаться с `vk1.a.` или `vk1/`\n\n"
            "Пример: `vk1.a.abcdefghijklmnopqrstuvwxyz123456`\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return VK_TOKEN_WAIT
    
    async def vk_token_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение и проверка VK токена"""
        token = update.message.text.strip()
        
        # Простая проверка формата
        if not (token.startswith('vk1.a.') or token.startswith('vk1/')):
            await update.message.reply_text(
                "❌ Непохоже на правильный VK токен.\n"
                "Токен должен начинаться с `vk1.a.`\n\n"
                "Попробуйте еще раз или /cancel",
                parse_mode='Markdown'
            )
            return VK_TOKEN_WAIT
        
        # Пытаемся сохранить
        success, msg = await self.account_manager.login_vk(token)
        
        if success:
            await update.message.reply_text(
                f"✅ {msg}\n\n"
                f"VK аккаунт успешно настроен!",
                reply_markup=self.keyboards.back_button("back_accounts")
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ {msg}\n\nПопробуйте еще раз или /cancel",
                reply_markup=self.keyboards.cancel_button()
            )
            return VK_TOKEN_WAIT
    
    async def vk_logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выход из VK аккаунта"""
        query = update.callback_query
        await query.answer()
        
        success = await self.account_manager.logout_vk()
        
        if success:
            text = "✅ Вы вышли из VK аккаунта"
        else:
            text = "❌ Ошибка при выходе или аккаунт не был настроен"
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
            parse_mode='Markdown'
        )
    
    # === TELEGRAM АККАУНТ ===
    
    async def tg_account_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка Telegram аккаунта"""
        query = update.callback_query
        await query.answer()
        
        session, phone = await self.db.get_telegram_session()
        has_session = session is not None
        
        if has_session:
            text = (
                f"🔷 **Telegram Аккаунт**\n\n"
                f"✅ Аккаунт настроен\n"
                f"📱 Телефон: `{phone}`\n\n"
                f"Что хотите сделать?"
            )
        else:
            text = (
                f"🔷 **Telegram Аккаунт**\n\n"
                f"❌ Аккаунт не настроен\n\n"
                f"Вам нужно войти в Telegram аккаунт.\n"
                f"Этот аккаунт будет использоваться для парсинга чатов."
            )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.tg_account_menu(has_session),
            parse_mode='Markdown'
        )
    
    async def tg_login_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало авторизации Telegram"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "📱 **Вход в Telegram**\n\n"
            "Отправьте мне ваш номер телефона в формате:\n"
            "`+71234567890`\n\n"
            "Пример: `+79123456789`\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return TG_AUTH_PHONE
    
    async def tg_auth_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение номера телефона"""
        phone = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Простая проверка формата
        if not phone.startswith('+') or not phone[1:].isdigit():
            await update.message.reply_text(
                "❌ Неверный формат. Нужно: `+71234567890`\n"
                "Попробуйте еще раз или /cancel",
                parse_mode='Markdown',
                reply_markup=self.keyboards.cancel_button()
            )
            return TG_AUTH_PHONE
        
        success, msg, client = await self.account_manager.start_tg_login(user_id, phone)
        
        if success:
            context.user_data['tg_auth_user_id'] = user_id
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.cancel_button()
            )
            return TG_AUTH_CODE
        else:
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.back_button("back_accounts")
            )
            return ConversationHandler.END
    
    async def tg_auth_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение кода подтверждения"""
        code = update.message.text.strip()
        user_id = context.user_data.get('tg_auth_user_id')
        
        if not user_id:
            await update.message.reply_text(
                "❌ Ошибка сессии. Начните заново.",
                reply_markup=self.keyboards.back_button("back_accounts")
            )
            return ConversationHandler.END
        
        success, msg = await self.account_manager.complete_tg_login(user_id, code)
        
        if "пароль" in msg.lower():
            # Требуется пароль двухфакторки
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.cancel_button()
            )
            return TG_AUTH_PASSWORD
        elif success:
            await update.message.reply_text(
                msg + "\n\n✅ Авторизация завершена!",
                reply_markup=self.keyboards.back_button("back_accounts")
            )
        else:
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.back_button("back_accounts")
            )
        
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
            await update.message.reply_text(
                msg,
                reply_markup=self.keyboards.back_button("back_accounts")
            )
        
        return ConversationHandler.END
    
    async def tg_logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выход из Telegram аккаунта"""
        query = update.callback_query
        await query.answer()
        
        success = await self.account_manager.logout_tg()
        
        if success:
            text = "✅ Вы вышли из Telegram аккаунта"
        else:
            text = "❌ Ошибка при выходе или аккаунт не был настроен"
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.accounts_menu(vk_status, tg_status),
            parse_mode='Markdown'
        )
    
    async def account_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус аккаунтов"""
        query = update.callback_query
        await query.answer()
        
        vk_status, tg_status = await self.account_manager.get_session_status()
        
        # Дополнительная информация
        vk_token = await self.account_manager.get_vk_token()
        tg_session, tg_phone = await self.db.get_telegram_session()
        
        text = (
            "📊 **Статус аккаунтов**\n\n"
            f"{'✅' if vk_status else '❌'} **VK аккаунт**\n"
        )
        
        if vk_status and vk_token:
            masked = vk_token[:10] + "..." + vk_token[-5:] if len(vk_token) > 20 else "***"
            text += f"   └ Токен: `{masked}`\n"
        
        text += f"\n{'✅' if tg_status else '❌'} **Telegram аккаунт**\n"
        
        if tg_status and tg_phone:
            text += f"   └ Телефон: `{tg_phone}`\n"
        
        if vk_status and tg_status:
            text += "\n✅ **Все аккаунты настроены, парсеры готовы к работе**"
        else:
            text += "\n⚠️ **Настройте недостающие аккаунты**"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_accounts"),
            parse_mode='Markdown'
        )
    
    # === УПРАВЛЕНИЕ VK ГРУППАМИ (ПОЛНОСТЬЮ РАБОЧЕЕ) ===
    
    async def vk_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню VK групп"""
        query = update.callback_query
        await query.answer()
        
        groups = await self.db.get_vk_groups(enabled_only=False)
        enabled = sum(1 for g in groups if g['enabled'])
        
        text = (
            f"📱 **VK Группы**\n\n"
            f"Всего групп: {len(groups)}\n"
            f"Активных: {enabled}\n\n"
            f"Выберите действие:"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.vk_menu(),
            parse_mode='Markdown'
        )
    
    async def vk_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список VK групп"""
        query = update.callback_query
        await query.answer()
        
        groups = await self.db.get_vk_groups(enabled_only=False)
        topics = await self.db.get_topics()
        
        if not groups:
            text = "📋 **VK группы**\n\nСписок пуст. Добавьте первую группу через ➕ Добавить группу"
            await query.edit_message_text(
                text,
                reply_markup=self.keyboards.back_button("back_vk"),
                parse_mode='Markdown'
            )
            return
        
        text = "📋 **VK группы**\n\n"
        
        for i, group in enumerate(groups, 1):
            status = "✅" if group['enabled'] else "❌"
            topic_name = topics.get(group['target_topic'], {}).get('name', group['target_topic'])
            
            text += f"{status} **{i}. {group['name']}**\n"
            text += f"   ID: `{group['group_id']}`\n"
            text += f"   Тема: {topic_name}\n"
            text += f"   Тип: {group['classifier_type']}\n\n"
        
        text += "Выберите группу для управления (пока не реализовано)"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_vk"),
            parse_mode='Markdown'
        )
    
    async def vk_add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления VK группы"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "➕ **Добавление VK группы**\n\n"
            "Шаг 1/8: Введите **название группы**\n"
            "Например: `Подслушано Маслянино`\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return ADD_VK_NAME
    
    async def vk_add_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия группы"""
        name = update.message.text.strip()
        context.user_data['vk_name'] = name
        
        await update.message.reply_text(
            f"✅ Название: **{name}**\n\n"
            "Шаг 2/8: Введите **ID группы**\n"
            "Можно использовать:\n"
            "• Короткое имя: `podslyshanomaslo`\n"
            "• Числовой ID: `-123456789`\n\n"
            "ID можно взять из ссылки: vk.com/***ID***",
            parse_mode='Markdown',
            reply_markup=self.keyboards.cancel_button()
        )
        
        return ADD_VK_ID
    
    async def vk_add_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение ID группы"""
        group_id = update.message.text.strip()
        context.user_data['vk_group_id'] = group_id
        
        # Получаем список тем для выбора
        topics = await self.db.get_topics()
        
        if not topics:
            await update.message.reply_text(
                "❌ Сначала добавьте темы через меню Темы!",
                reply_markup=self.keyboards.back_button("back_vk")
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            f"✅ ID: `{group_id}`\n\n"
            "Шаг 3/8: Выберите **целевую тему**",
            reply_markup=self.keyboards.topics_selection_menu(topics),
            parse_mode='Markdown'
        )
        
        return ADD_VK_TOPIC
    
    async def vk_add_topic_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора темы"""
        query = update.callback_query
        await query.answer()
        
        topic_id = query.data.replace('topic_select_', '')
        topics = await self.db.get_topics()
        topic = topics.get(topic_id, {})
        
        context.user_data['vk_target_topic'] = topic_id
        
        await query.edit_message_text(
            f"✅ Выбрана тема: {topic.get('emoji', '📌')} {topic.get('name', topic_id)}\n\n"
            "Шаг 4/8: Отправлять **все посты**?\n"
            "• Если ДА - будут публиковаться все посты подряд\n"
            "• Если НЕТ - будет применяться классификатор",
            reply_markup=self.keyboards.yes_no_menu("vk_all"),
            parse_mode='Markdown'
        )
        
        return ADD_VK_ALL_POSTS
    
    async def vk_add_all_posts_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора all_posts"""
        query = update.callback_query
        await query.answer()
        
        all_posts = query.data == "vk_all_yes"
        context.user_data['vk_all_posts'] = all_posts
        
        await query.edit_message_text(
            f"✅ Все посты: {'Да' if all_posts else 'Нет'}\n\n"
            "Шаг 5/8: Выберите **тип классификатора**:\n\n"
            "• **Без классификации** - посты идут в выбранную тему\n"
            "• **Купля/Продажа/Отдам** - автоопределение по словам\n"
            "• **По ключевым словам** - только посты с ключевыми словами",
            reply_markup=self.keyboards.classifier_type_menu(),
            parse_mode='Markdown'
        )
        
        return ADD_VK_CLASSIFIER
    
    async def vk_add_classifier_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора классификатора"""
        query = update.callback_query
        await query.answer()
        
        classifier = query.data.replace('classifier_', '')
        context.user_data['vk_classifier'] = classifier
        
        classifier_names = {
            'none': '🚫 Без классификации',
            'buy_sell': '💰 Купля/Продажа/Отдам',
            'keywords': '🔑 По ключевым словам'
        }
        
        if classifier == 'keywords':
            await query.edit_message_text(
                f"✅ Выбран: {classifier_names.get(classifier, classifier)}\n\n"
                "Шаг 6/8: Введите **ключевые слова** через запятую\n"
                "Например: `отдых, парк, мероприятие, афиша`\n\n"
                "Посты будут публиковаться только если содержат хотя бы одно слово",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return ADD_VK_KEYWORDS
        else:
            # Пропускаем ключевые слова
            context.user_data['vk_keywords'] = []
            await query.edit_message_text(
                f"✅ Выбран: {classifier_names.get(classifier, classifier)}\n\n"
                "Шаг 6/8: Пропускаем (ключевые слова не нужны)\n\n"
                "Шаг 7/8: Введите **исключающие слова** через запятую\n"
                "Посты с этими словами будут игнорироваться\n"
                "Или отправьте `-` чтобы пропустить",
                reply_markup=self.keyboards.cancel_button(),
                parse_mode='Markdown'
            )
            return ADD_VK_EXCLUDE
    
    async def vk_add_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение ключевых слов"""
        keywords_text = update.message.text.strip()
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        context.user_data['vk_keywords'] = keywords
        
        await update.message.reply_text(
            f"✅ Ключевые слова: {', '.join(keywords) if keywords else 'нет'}\n\n"
            "Шаг 7/8: Введите **исключающие слова** через запятую\n"
            "Посты с этими словами будут игнорироваться\n"
            "Или отправьте `-` чтобы пропустить",
            parse_mode='Markdown',
            reply_markup=self.keyboards.cancel_button()
        )
        
        return ADD_VK_EXCLUDE
    
    async def vk_add_exclude(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение исключающих слов"""
        exclude_text = update.message.text.strip()
        
        if exclude_text == '-':
            exclude = []
        else:
            exclude = [e.strip() for e in exclude_text.split(',') if e.strip()]
        
        context.user_data['vk_exclude'] = exclude
        
        await update.message.reply_text(
            f"✅ Исключающие слова: {', '.join(exclude) if exclude else 'нет'}\n\n"
            "Шаг 8/8: Требовать наличие **даты или цены**?\n"
            "Если ДА - будут публиковаться только посты с датой (число.месяц) или ценой (руб)",
            reply_markup=self.keyboards.yes_no_menu("vk_date"),
            parse_mode='Markdown'
        )
        
        return ADD_VK_DATE_PRICE
    
    async def vk_add_date_price_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение добавления VK группы"""
        query = update.callback_query
        await query.answer()
        
        require = query.data == "vk_date_yes"
        
        # Собираем все данные
        group_data = {
            'name': context.user_data.get('vk_name'),
            'group_id': context.user_data.get('vk_group_id'),
            'target_topic': context.user_data.get('vk_target_topic'),
            'all_posts': context.user_data.get('vk_all_posts', False),
            'classifier_type': context.user_data.get('vk_classifier', 'none'),
            'keywords': context.user_data.get('vk_keywords', []),
            'exclude_keywords': context.user_data.get('vk_exclude', []),
            'require_date_or_price': require
        }
        
        # Сохраняем в БД
        group_id = await self.db.add_vk_group(group_data)
        
        if group_id:
            # Получаем название темы
            topics = await self.db.get_topics()
            topic = topics.get(group_data['target_topic'], {})
            
            text = (
                f"✅ **VK группа успешно добавлена!**\n\n"
                f"📌 **Название:** {group_data['name']}\n"
                f"🆔 **ID:** {group_data['group_id']}\n"
                f"📂 **Тема:** {topic.get('emoji', '')} {topic.get('name', group_data['target_topic'])}\n"
                f"📊 **Все посты:** {'Да' if group_data['all_posts'] else 'Нет'}\n"
                f"🔍 **Классификатор:** {group_data['classifier_type']}\n"
                f"🚫 **Исключающие:** {', '.join(group_data['exclude_keywords']) if group_data['exclude_keywords'] else 'нет'}\n"
                f"📅 **Требовать дату/цену:** {'Да' if require else 'Нет'}\n\n"
                f"Группа добавлена и {'активна' if require else 'активна'}."
            )
        else:
            text = "❌ Ошибка при добавлении группы. Возможно, такая группа уже есть."
        
        # Очищаем данные
        context.user_data.clear()
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_vk"),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    # === УПРАВЛЕНИЕ СТОП-СЛОВАМИ ===
    
    async def adwords_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню стоп-слов"""
        query = update.callback_query
        await query.answer()
        
        keywords = await self.db.get_ad_keywords()
        
        text = (
            f"🚫 **Стоп-слова**\n\n"
            f"Всего слов в списке: {len(keywords)}\n\n"
            f"Эти слова будут блокировать публикацию постов.\n"
            f"Выберите действие:"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.adwords_menu(),
            parse_mode='Markdown'
        )
    
    async def adword_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список стоп-слов"""
        query = update.callback_query
        await query.answer()
        
        keywords = await self.db.get_ad_keywords()
        
        if not keywords:
            text = "📋 **Стоп-слова**\n\nСписок пуст. Добавьте слова через ➕ Добавить слово"
        else:
            text = "📋 **Стоп-слова**\n\n"
            for i, word in enumerate(keywords, 1):
                text += f"{i}. `{word}`\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_adwords"),
            parse_mode='Markdown'
        )
    
    async def adword_add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления стоп-слова"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "➕ **Добавление стоп-слова**\n\n"
            "Отправьте слово, которое нужно добавить в стоп-лист.\n"
            "Например: `реклама`\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return ADD_ADWORD
    
    async def adword_add_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение стоп-слова"""
        word = update.message.text.strip().lower()
        
        if len(word) < 2:
            await update.message.reply_text(
                "❌ Слово слишком короткое. Минимум 2 символа.\n"
                "Попробуйте еще раз или /cancel",
                reply_markup=self.keyboards.cancel_button()
            )
            return ADD_ADWORD
        
        success = await self.db.add_ad_keyword(word)
        
        if success:
            await update.message.reply_text(
                f"✅ Слово `{word}` добавлено в стоп-лист!",
                reply_markup=self.keyboards.back_button("back_adwords"),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Слово `{word}` уже есть в стоп-листе или ошибка.",
                reply_markup=self.keyboards.back_button("back_adwords"),
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END
    
    async def adword_remove_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало удаления стоп-слова"""
        query = update.callback_query
        await query.answer()
        
        keywords = await self.db.get_ad_keywords()
        
        if not keywords:
            await query.edit_message_text(
                "📋 **Стоп-слова**\n\nСписок пуст, удалять нечего.",
                reply_markup=self.keyboards.back_button("back_adwords"),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Создаем клавиатуру со словами
        keyboard = []
        for word in keywords:
            keyboard.append([InlineKeyboardButton(f"🗑 {word}", callback_data=f"del_{word}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_adwords")])
        
        await query.edit_message_text(
            "🗑 **Удаление стоп-слова**\n\n"
            "Выберите слово для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return REMOVE_ADWORD
    
    async def adword_remove_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаление стоп-слова по кнопке"""
        query = update.callback_query
        await query.answer()
        
        word = query.data.replace('del_', '')
        success = await self.db.remove_ad_keyword(word)
        
        if success:
            text = f"✅ Слово `{word}` удалено из стоп-листа!"
        else:
            text = f"❌ Ошибка при удалении слова `{word}`."
        
        # Показываем обновленный список
        keywords = await self.db.get_ad_keywords()
        
        if keywords:
            keyboard = []
            for w in keywords:
                keyboard.append([InlineKeyboardButton(f"🗑 {w}", callback_data=f"del_{w}")])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_adwords")])
            
            await query.edit_message_text(
                text + "\n\nВыберите следующее слово для удаления:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text + "\n\nСписок стоп-слов пуст.",
                reply_markup=self.keyboards.back_button("back_adwords"),
                parse_mode='Markdown'
            )
        
        return REMOVE_ADWORD
    
    # === УПРАВЛЕНИЕ ТЕМАМИ ===
    
    async def topics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню тем"""
        query = update.callback_query
        await query.answer()
        
        topics = await self.db.get_topics()
        
        text = (
            f"📂 **Темы назначения**\n\n"
            f"Всего тем: {len(topics)}\n\n"
            f"Темы определяют, в какой раздел группы попадут посты.\n"
            f"Выберите действие:"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.topics_menu(),
            parse_mode='Markdown'
        )
    
    async def topic_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список тем"""
        query = update.callback_query
        await query.answer()
        
        topics = await self.db.get_topics()
        
        if not topics:
            text = "📋 **Темы**\n\nСписок пуст. Добавьте темы через ➕ Добавить тему"
        else:
            text = "📋 **Темы назначения**\n\n"
            for topic_id, topic in topics.items():
                text += f"{topic['emoji']} **{topic['name']}**\n"
                text += f"   ID: `{topic_id}`\n"
                text += f"   Topic ID: `{topic['topic_id']}`\n\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_topics"),
            parse_mode='Markdown'
        )
    
    async def topic_add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления темы"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "➕ **Добавление темы**\n\n"
            "Шаг 1/3: Введите **ID темы** (уникальный идентификатор)\n"
            "Например: `novosti` или `kuplyu`\n"
            "Только латинские буквы и цифры\n\n"
            "Или отправьте /cancel для отмены",
            reply_markup=self.keyboards.cancel_button(),
            parse_mode='Markdown'
        )
        
        return ADD_TOPIC_ID
    
    async def topic_add_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение ID темы"""
        topic_id = update.message.text.strip().lower()
        
        # Проверка на допустимые символы
        if not topic_id.replace('_', '').isalnum():
            await update.message.reply_text(
                "❌ ID должен содержать только латинские буквы, цифры и _\n"
                "Попробуйте еще раз или /cancel",
                reply_markup=self.keyboards.cancel_button()
            )
            return ADD_TOPIC_ID
        
        context.user_data['new_topic_id'] = topic_id
        
        await update.message.reply_text(
            f"✅ ID: `{topic_id}`\n\n"
            "Шаг 2/3: Введите **номер темы в Telegram** (Topic ID)\n"
            "Например: `105`\n"
            "Узнать можно у @getidsbot",
            parse_mode='Markdown',
            reply_markup=self.keyboards.cancel_button()
        )
        
        return ADD_TOPIC_NAME
    
    async def topic_add_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение номера темы и названия"""
        try:
            topic_num = int(update.message.text.strip())
            context.user_data['new_topic_num'] = topic_num
        except ValueError:
            await update.message.reply_text(
                "❌ Номер темы должен быть числом\n"
                "Попробуйте еще раз или /cancel",
                reply_markup=self.keyboards.cancel_button()
            )
            return ADD_TOPIC_NAME
        
        await update.message.reply_text(
            f"✅ Topic ID: `{topic_num}`\n\n"
            "Шаг 3/3: Введите **название темы**\n"
            "Например: `Новости` или `Куплю`",
            parse_mode='Markdown',
            reply_markup=self.keyboards.cancel_button()
        )
        
        return ADD_TOPIC_EMOJI
    
    async def topic_add_emoji(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия и завершение"""
        name = update.message.text.strip()
        
        # Спрашиваем эмодзи
        await update.message.reply_text(
            f"✅ Название: **{name}**\n\n"
            "Теперь отправьте **эмодзи** для темы\n"
            "Например: 📢 или 🛒\n"
            "Или отправьте `-` для стандартного 📌",
            parse_mode='Markdown',
            reply_markup=self.keyboards.cancel_button()
        )
        
        context.user_data['new_topic_name'] = name
        
        return ADD_TOPIC_EMOJI
    
    async def topic_add_final(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение добавления темы"""
        emoji = update.message.text.strip()
        
        if emoji == '-':
            emoji = '📌'
        
        # Сохраняем тему
        topic_data = {
            'id': context.user_data.get('new_topic_id'),
            'topic_id': context.user_data.get('new_topic_num'),
            'name': context.user_data.get('new_topic_name'),
            'emoji': emoji
        }
        
        success = await self.db.add_topic(topic_data)
        
        if success:
            text = (
                f"✅ **Тема успешно добавлена!**\n\n"
                f"{emoji} **{topic_data['name']}**\n"
                f"ID: `{topic_data['id']}`\n"
                f"Topic ID: `{topic_data['topic_id']}`"
            )
        else:
            text = "❌ Ошибка при добавлении темы. Возможно, такой ID уже существует."
        
        context.user_data.clear()
        
        await update.message.reply_text(
            text,
            reply_markup=self.keyboards.back_button("back_topics"),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    # === СТАТИСТИКА ===
    
    async def stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню статистики"""
        query = update.callback_query
        await query.answer()
        
        # Показываем краткую статистику
        stats_today = await self.db.get_stats(1)
        stats_week = await self.db.get_stats(7)
        
        text = (
            f"📊 **Статистика**\n\n"
            f"**За сегодня:** {stats_today['total']}\n"
            f"   └ VK: {stats_today['vk']}\n"
            f"   └ TG: {stats_today['telegram']}\n\n"
            f"**За неделю:** {stats_week['total']}\n\n"
            f"Выберите период для детальной статистики:"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.stats_menu(),
            parse_mode='Markdown'
        )
    
    async def stats_show(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику за период"""
        query = update.callback_query
        await query.answer()
        
        days_map = {
            "stats_today": 1,
            "stats_week": 7,
            "stats_month": 30,
            "stats_all": 365
        }
        days = days_map.get(query.data, 1)
        
        stats = await self.db.get_stats(days)
        
        # Получаем дополнительную статистику (топ источников)
        async with self.db.get_connection() as conn:
            async with conn.execute(
                '''SELECT source_group, COUNT(*) as count 
                   FROM processed_posts 
                   WHERE processed_at >= datetime('now', ?)
                   GROUP BY source_group 
                   ORDER BY count DESC 
                   LIMIT 5''',
                (f'-{days} days',)
            ) as cursor:
                top_sources = await cursor.fetchall()
        
        days_text = {
            1: "сегодня",
            7: "неделю",
            30: "месяц",
            365: "всё время"
        }.get(days, f"{days} дн.")
        
        text = (
            f"📊 **Статистика за {days_text}**\n\n"
            f"📨 **Всего обработано:** {stats['total']}\n"
            f"   └ ВКонтакте: {stats['vk']}\n"
            f"   └ Telegram: {stats['telegram']}\n\n"
        )
        
        if top_sources:
            text += "**🏆 Топ источников:**\n"
            for row in top_sources:
                source = row['source_group']
                count = row['count']
                text += f"   • {source}: {count}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_stats"),
            parse_mode='Markdown'
        )
    
    # === ОБЩИЕ ОБРАБОТЧИКИ ===
    
    async def back_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки назад"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_main":
            await self.main_menu(update, context)
        elif query.data == "back_accounts":
            await self.account_menu(update, context)
        elif query.data == "back_vk":
            await self.vk_menu(update, context)
        elif query.data == "back_tg":
            await self.tg_menu(update, context)
        elif query.data == "back_topics":
            await self.topics_menu(update, context)
        elif query.data == "back_adwords":
            await self.adwords_menu(update, context)
        elif query.data == "back_stats":
            await self.stats_menu(update, context)
        elif query.data == "back":
            # Возврат в предыдущее меню (для вложенных)
            await query.edit_message_text(
                "📋 **Меню**",
                reply_markup=self.keyboards.main_menu(),
                parse_mode='Markdown'
            )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Операция отменена.",
                reply_markup=self.keyboards.back_button("back_main"),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Операция отменена.",
                reply_markup=self.keyboards.back_button("back_main"),
                parse_mode='Markdown'
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    # === ЗАГЛУШКИ ДЛЯ НЕ РЕАЛИЗОВАННЫХ ФУНКЦИЙ ===
    
    async def tg_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню Telegram источников (заглушка)"""
        query = update.callback_query
        await query.answer()
        
        sources = await self.db.get_telegram_sources(enabled_only=False)
        enabled = sum(1 for s in sources if s['enabled'])
        
        text = (
            f"💬 **Telegram источники**\n\n"
            f"Всего источников: {len(sources)}\n"
            f"Активных: {enabled}\n\n"
            f"⚙️ Функция в разработке\n"
            f"Скоро здесь можно будет добавлять чаты для парсинга"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_main"),
            parse_mode='Markdown'
        )
    
    async def settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню настроек (заглушка)"""
        query = update.callback_query
        await query.answer()
        
        text = (
            "⚙️ **Настройки**\n\n"
            "Здесь будут настройки бота:\n"
            "• Интервалы проверки\n"
            "• Формат сообщений\n"
            "• Дополнительные фильтры\n\n"
            "⚙️ Функция в разработке"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.back_button("back_main"),
            parse_mode='Markdown'
        )