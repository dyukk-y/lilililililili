"""
Все клавиатуры бота (инлайн кнопки)
"""

from typing import Dict, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboards:
    """Класс со всеми клавиатурами"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = [
            [
                InlineKeyboardButton("📱 VK Группы", callback_data="menu_vk"),
                InlineKeyboardButton("💬 Telegram", callback_data="menu_tg")
            ],
            [
                InlineKeyboardButton("📂 Темы", callback_data="menu_topics"),
                InlineKeyboardButton("🚫 Стоп-слова", callback_data="menu_adwords")
            ],
            [
                InlineKeyboardButton("🔐 Аккаунты", callback_data="menu_accounts"),
                InlineKeyboardButton("📊 Статистика", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings"),
                InlineKeyboardButton("❓ Помощь", callback_data="menu_help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def accounts_menu(vk_status: bool, tg_status: bool) -> InlineKeyboardMarkup:
        """Меню управления аккаунтами"""
        vk_emoji = "✅" if vk_status else "❌"
        tg_emoji = "✅" if tg_status else "❌"
        
        keyboard = [
            [InlineKeyboardButton(f"{vk_emoji} VK Аккаунт", callback_data="account_vk")],
            [InlineKeyboardButton(f"{tg_emoji} Telegram Аккаунт", callback_data="account_tg")],
            [InlineKeyboardButton("📊 Статус", callback_data="account_status")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def vk_account_menu(has_token: bool) -> InlineKeyboardMarkup:
        """Меню VK аккаунта"""
        keyboard = []
        
        if has_token:
            keyboard.append([InlineKeyboardButton("🔄 Сменить токен", callback_data="vk_token_change")])
            keyboard.append([InlineKeyboardButton("🚪 Выйти", callback_data="vk_logout")])
        else:
            keyboard.append([InlineKeyboardButton("🔑 Ввести токен", callback_data="vk_token_enter")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_accounts")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def tg_account_menu(has_session: bool) -> InlineKeyboardMarkup:
        """Меню Telegram аккаунта"""
        keyboard = []
        
        if has_session:
            keyboard.append([InlineKeyboardButton("🚪 Выйти", callback_data="tg_logout")])
        else:
            keyboard.append([InlineKeyboardButton("📱 Войти", callback_data="tg_login")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_accounts")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def vk_menu() -> InlineKeyboardMarkup:
        """Меню VK групп"""
        keyboard = [
            [InlineKeyboardButton("➕ Добавить группу", callback_data="vk_add")],
            [InlineKeyboardButton("📋 Список групп", callback_data="vk_list")],
            [InlineKeyboardButton("🔄 Обновить статус", callback_data="vk_refresh")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def tg_menu() -> InlineKeyboardMarkup:
        """Меню Telegram источников"""
        keyboard = [
            [InlineKeyboardButton("➕ Добавить источник", callback_data="tg_add")],
            [InlineKeyboardButton("📋 Список источников", callback_data="tg_list")],
            [InlineKeyboardButton("🔄 Проверить доступ", callback_data="tg_check")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def topics_menu() -> InlineKeyboardMarkup:
        """Меню тем"""
        keyboard = [
            [InlineKeyboardButton("📋 Список тем", callback_data="topic_list")],
            [InlineKeyboardButton("➕ Добавить тему", callback_data="topic_add")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data="topic_edit")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def adwords_menu() -> InlineKeyboardMarkup:
        """Меню стоп-слов"""
        keyboard = [
            [InlineKeyboardButton("📋 Список слов", callback_data="adword_list")],
            [InlineKeyboardButton("➕ Добавить слово", callback_data="adword_add")],
            [InlineKeyboardButton("🗑 Удалить слово", callback_data="adword_remove")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def stats_menu() -> InlineKeyboardMarkup:
        """Меню статистики"""
        keyboard = [
            [InlineKeyboardButton("📊 За сегодня", callback_data="stats_today")],
            [InlineKeyboardButton("📈 За неделю", callback_data="stats_week")],
            [InlineKeyboardButton("📉 За месяц", callback_data="stats_month")],
            [InlineKeyboardButton("📋 За всё время", callback_data="stats_all")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def classifier_type_menu() -> InlineKeyboardMarkup:
        """Выбор типа классификатора"""
        keyboard = [
            [InlineKeyboardButton("🚫 Без классификации", callback_data="classifier_none")],
            [InlineKeyboardButton("💰 Купля/Продажа/Отдам", callback_data="classifier_buy_sell")],
            [InlineKeyboardButton("🔑 По ключевым словам", callback_data="classifier_keywords")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def yes_no_menu(callback_prefix: str) -> InlineKeyboardMarkup:
        """Меню Да/Нет"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data=f"{callback_prefix}_yes"),
                InlineKeyboardButton("❌ Нет", callback_data=f"{callback_prefix}_no")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def topics_selection_menu(topics: dict) -> InlineKeyboardMarkup:
        """Меню выбора темы"""
        keyboard = []
        for topic_id, topic in topics.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{topic['emoji']} {topic['name']}", 
                    callback_data=f"topic_select_{topic_id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def group_actions_menu(group_id: int, enabled: bool) -> InlineKeyboardMarkup:
        """Меню действий с группой"""
        status_text = "✅ Вкл" if enabled else "❌ Выкл"
        status_action = "off" if enabled else "on"
        
        keyboard = [
            [InlineKeyboardButton(f"📊 Статус: {status_text}", callback_data=f"group_toggle_{group_id}_{status_action}")],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"group_delete_{group_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="vk_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "back_main") -> InlineKeyboardMarkup:
        """Кнопка назад"""
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        """Кнопка отмены"""
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)