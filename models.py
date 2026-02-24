"""
Модели данных для базы данных
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Admin:
    """Модель администратора"""
    user_id: int
    username: Optional[str] = None
    added_by: Optional[int] = None
    added_at: Optional[datetime] = None
    is_main: bool = False

@dataclass
class VKGroup:
    """Модель группы ВКонтакте"""
    id: Optional[int] = None
    name: str = ""
    group_id: str = ""
    target_topic: str = ""
    all_posts: bool = False
    classifier_type: str = "none"  # none, buy_sell, keywords
    keywords: List[str] = None
    exclude_keywords: List[str] = None
    require_date_or_price: bool = False
    enabled: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.exclude_keywords is None:
            self.exclude_keywords = []

@dataclass
class TelegramSource:
    """Модель источника Telegram"""
    id: Optional[int] = None
    name: str = ""
    chat_id: int = 0
    chat_username: Optional[str] = None
    topic_id: Optional[int] = None
    target_topic: str = ""
    all_posts: bool = False
    classifier_type: str = "buy_sell"  # none, buy_sell, keywords
    keywords: List[str] = None
    show_author: bool = True
    enabled: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class Topic:
    """Модель темы назначения"""
    id: str
    topic_id: int
    name: str
    emoji: str = "📌"
    description: Optional[str] = None

@dataclass
class ProcessedPost:
    """Модель обработанного поста"""
    id: Optional[int] = None
    source_type: str = ""
    source_id: str = ""
    source_group: str = ""
    content_hash: str = ""
    target_topic_id: Optional[int] = None
    processed_at: Optional[datetime] = None