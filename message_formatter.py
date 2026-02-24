"""
Форматирование сообщений для отправки в Telegram
"""

from typing import Dict, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class MessageFormatter:
    """Форматирование сообщений с кнопками"""
    
    def __init__(self, brand_tag: str = "@maslyanino"):
        self.brand_tag = brand_tag
    
    def format_vk_post(self, text: str, topic: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Форматирование поста из VK
        
        Args:
            text: Текст поста
            topic: Тема назначения (словарь с emoji, name)
            
        Returns:
            formatted_text: Отформатированный текст
            keyboard: Клавиатура с кнопками
        """
        # Заголовок
        header = f"[{topic['emoji']}] {topic['name'].upper()}\n"
        header += "─" * 30 + "\n\n"
        
        # Текст (обрезаем если слишком длинный)
        if len(text) > 3500:
            text = text[:3500] + "...\n\n(текст обрезан)"
        
        # Добавляем бренд
        footer = f"\n\n{self.brand_tag}"
        
        # Собираем всё вместе
        formatted_text = header + text + footer
        
        return formatted_text
    
    def format_telegram_message(self, text: str, topic: Dict, 
                                author_username: Optional[str] = None,
                                author_id: Optional[int] = None) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Форматирование сообщения из Telegram
        
        Args:
            text: Текст сообщения
            topic: Тема назначения
            author_username: Username автора (если есть)
            author_id: ID автора (если нет username)
            
        Returns:
            formatted_text: Отформатированный текст
            keyboard: Клавиатура с кнопками
        """
        # Заголовок
        header = f"[{topic['emoji']}] {topic['name'].upper()}\n"
        header += "─" * 30 + "\n\n"
        
        # Текст
        if len(text) > 3500:
            text = text[:3500] + "...\n\n(текст обрезан)"
        
        # Добавляем бренд
        footer = f"\n\n{self.brand_tag}"
        
        # Собираем всё вместе
        formatted_text = header + text + footer
        
        return formatted_text
    
    def create_source_button(self, url: str) -> InlineKeyboardMarkup:
        """Создание кнопки 'Источник'"""
        keyboard = [[InlineKeyboardButton("🔗 Источник", url=url)]]
        return InlineKeyboardMarkup(keyboard)
    
    def create_author_button(self, url: str) -> InlineKeyboardMarkup:
        """Создание кнопки 'Автор'"""
        keyboard = [[InlineKeyboardButton("👤 Автор", url=url)]]
        return InlineKeyboardMarkup(keyboard)
    
    def create_two_buttons(self, source_url: str, author_url: str) -> InlineKeyboardMarkup:
        """Создание двух кнопок в ряд"""
        keyboard = [[
            InlineKeyboardButton("🔗 Источник", url=source_url),
            InlineKeyboardButton("👤 Автор", url=author_url)
        ]]
        return InlineKeyboardMarkup(keyboard)
    
    def extract_vk_post_id(self, post_url: str) -> Optional[str]:
        """Извлечение ID поста из ссылки VK"""
        if 'wall-' in post_url:
            return post_url.split('wall-')[-1]
        elif '?w=wall-' in post_url:
            return post_url.split('wall-')[-1]
        return None