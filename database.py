"""
Работа с базой данных SQLite
"""

import aiosqlite
import json
import pickle
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager
from loguru import logger

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @asynccontextmanager
    async def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
    
    async def init_db(self):
        """Инициализация всех таблиц"""
        async with self.get_connection() as conn:
            # Администраторы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_main BOOLEAN DEFAULT 0
                )
            ''')
            
            # Сессии аккаунтов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS account_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_type TEXT NOT NULL,
                    session_data BLOB,
                    phone TEXT,
                    token TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # VK группы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS vk_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    group_id TEXT NOT NULL UNIQUE,
                    target_topic TEXT NOT NULL,
                    all_posts BOOLEAN DEFAULT 0,
                    classifier_type TEXT DEFAULT 'none',
                    keywords TEXT,
                    exclude_keywords TEXT,
                    require_date_or_price BOOLEAN DEFAULT 0,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Telegram источники
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS telegram_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    chat_id INTEGER NOT NULL,
                    chat_username TEXT,
                    topic_id INTEGER,
                    target_topic TEXT NOT NULL,
                    all_posts BOOLEAN DEFAULT 0,
                    classifier_type TEXT DEFAULT 'buy_sell',
                    keywords TEXT,
                    show_author BOOLEAN DEFAULT 1,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, topic_id)
                )
            ''')
            
            # Темы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY,
                    topic_id INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    emoji TEXT DEFAULT '📌',
                    description TEXT
                )
            ''')
            
            # Стоп-слова
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS ad_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Обработанные посты
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_group TEXT NOT NULL,
                    content_hash TEXT,
                    target_topic_id INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_type, source_id, source_group)
                )
            ''')
            
            # Настройки
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.commit()
            logger.info("✅ База данных инициализирована")
    
    # === Администраторы ===
    
    async def add_admin(self, user_id: int, username: str = None, added_by: int = None, is_main: bool = False) -> bool:
        """Добавить администратора"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO admins (user_id, username, added_by, is_main) VALUES (?, ?, ?, ?)",
                    (user_id, username, added_by, 1 if is_main else 0)
                )
                await conn.commit()
                logger.info(f"✅ Администратор {user_id} добавлен")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления администратора: {e}")
            return False
    
    async def remove_admin(self, user_id: int) -> bool:
        """Удалить администратора"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("DELETE FROM admins WHERE user_id = ? AND is_main = 0", (user_id,))
                await conn.commit()
                logger.info(f"✅ Администратор {user_id} удален")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления администратора: {e}")
            return False
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone() is not None
    
    async def is_main_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь главным администратором"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT is_main FROM admins WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row is not None and row['is_main'] == 1
    
    async def get_all_admins(self) -> List[Dict]:
        """Получить список всех администраторов"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM admins ORDER BY added_at") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # === Сессии аккаунтов ===
    
    async def save_vk_token(self, token: str) -> bool:
        """Сохранить VK токен"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE account_sessions SET is_active = 0 WHERE account_type = 'vk'"
                )
                await conn.execute(
                    "INSERT INTO account_sessions (account_type, token, is_active) VALUES (?, ?, 1)",
                    ('vk', token)
                )
                await conn.commit()
                logger.info("✅ VK токен сохранен")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения VK токена: {e}")
            return False
    
    async def get_vk_token(self) -> Optional[str]:
        """Получить активный VK токен"""
        async with self.get_connection() as conn:
            async with conn.execute(
                "SELECT token FROM account_sessions WHERE account_type = 'vk' AND is_active = 1 ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                return row['token'] if row else None
    
    async def save_telegram_session(self, session_data: bytes, phone: str) -> bool:
        """Сохранить Telegram сессию"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE account_sessions SET is_active = 0 WHERE account_type = 'telegram'"
                )
                await conn.execute(
                    "INSERT INTO account_sessions (account_type, session_data, phone, is_active) VALUES (?, ?, ?, 1)",
                    ('telegram', session_data, phone)
                )
                await conn.commit()
                logger.info(f"✅ Telegram сессия сохранена для {phone}")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения Telegram сессии: {e}")
            return False
    
    async def get_telegram_session(self) -> Tuple[Optional[bytes], Optional[str]]:
        """Получить активную Telegram сессию"""
        async with self.get_connection() as conn:
            async with conn.execute(
                "SELECT session_data, phone FROM account_sessions WHERE account_type = 'telegram' AND is_active = 1 ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row['session_data'], row['phone']
                return None, None
    
    async def deactivate_session(self, account_type: str) -> bool:
        """Деактивировать сессию"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE account_sessions SET is_active = 0 WHERE account_type = ?",
                    (account_type,)
                )
                await conn.commit()
                logger.info(f"✅ Сессия {account_type} деактивирована")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка деактивации сессии: {e}")
            return False
    
    async def get_session_status(self) -> Dict[str, bool]:
        """Получить статус сессий"""
        async with self.get_connection() as conn:
            vk = await conn.execute(
                "SELECT 1 FROM account_sessions WHERE account_type = 'vk' AND is_active = 1"
            )
            tg = await conn.execute(
                "SELECT 1 FROM account_sessions WHERE account_type = 'telegram' AND is_active = 1"
            )
            return {
                'vk': await vk.fetchone() is not None,
                'telegram': await tg.fetchone() is not None
            }
    
    # === VK группы ===
    
    async def add_vk_group(self, group_data: Dict) -> int:
        """Добавить VK группу"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    '''INSERT INTO vk_groups 
                       (name, group_id, target_topic, all_posts, classifier_type, 
                        keywords, exclude_keywords, require_date_or_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        group_data['name'],
                        group_data['group_id'],
                        group_data['target_topic'],
                        group_data['all_posts'],
                        group_data['classifier_type'],
                        json.dumps(group_data.get('keywords', [])),
                        json.dumps(group_data.get('exclude_keywords', [])),
                        group_data.get('require_date_or_price', False)
                    )
                )
                await conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка добавления VK группы: {e}")
            return 0
    
    async def get_vk_groups(self, enabled_only: bool = True) -> List[Dict]:
        """Получить список VK групп"""
        query = "SELECT * FROM vk_groups"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        
        async with self.get_connection() as conn:
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                groups = []
                for row in rows:
                    group = dict(row)
                    group['keywords'] = json.loads(group['keywords']) if group['keywords'] else []
                    group['exclude_keywords'] = json.loads(group['exclude_keywords']) if group['exclude_keywords'] else []
                    groups.append(group)
                return groups
    
    async def toggle_vk_group(self, group_id: int, enabled: bool) -> bool:
        """Включить/выключить VK группу"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE vk_groups SET enabled = ? WHERE id = ?",
                    (enabled, group_id)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка переключения VK группы: {e}")
            return False
    
    async def delete_vk_group(self, group_id: int) -> bool:
        """Удалить VK группу"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("DELETE FROM vk_groups WHERE id = ?", (group_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления VK группы: {e}")
            return False
    
    async def update_vk_group(self, group_id: int, data: dict) -> bool:
        """Обновить VK группу"""
        try:
            async with self.get_connection() as conn:
                fields = ", ".join([f"{k} = ?" for k in data.keys()])
                values = list(data.values()) + [group_id]
                await conn.execute(f"UPDATE vk_groups SET {fields} WHERE id = ?", values)
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления VK группы: {e}")
            return False
    
    # === Telegram источники ===
    
    async def add_telegram_source(self, source_data: Dict) -> int:
        """Добавить Telegram источник"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    '''INSERT INTO telegram_sources 
                       (name, chat_id, chat_username, topic_id, target_topic, all_posts,
                        classifier_type, keywords, show_author)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        source_data['name'],
                        source_data['chat_id'],
                        source_data.get('chat_username'),
                        source_data.get('topic_id'),
                        source_data['target_topic'],
                        source_data['all_posts'],
                        source_data['classifier_type'],
                        json.dumps(source_data.get('keywords', [])),
                        source_data.get('show_author', True)
                    )
                )
                await conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка добавления Telegram источника: {e}")
            return 0
    
    async def get_telegram_sources(self, enabled_only: bool = True) -> List[Dict]:
        """Получить список Telegram источников"""
        query = "SELECT * FROM telegram_sources"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        
        async with self.get_connection() as conn:
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                sources = []
                for row in rows:
                    source = dict(row)
                    source['keywords'] = json.loads(source['keywords']) if source['keywords'] else []
                    sources.append(source)
                return sources
    
    async def toggle_telegram_source(self, source_id: int, enabled: bool) -> bool:
        """Включить/выключить Telegram источник"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE telegram_sources SET enabled = ? WHERE id = ?",
                    (enabled, source_id)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка переключения Telegram источника: {e}")
            return False
    
    async def delete_telegram_source(self, source_id: int) -> bool:
        """Удалить Telegram источник"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("DELETE FROM telegram_sources WHERE id = ?", (source_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления Telegram источника: {e}")
            return False
    
    # === Темы ===
    
    async def add_topic(self, topic_data: Dict) -> bool:
        """Добавить тему"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO topics (id, topic_id, name, emoji, description) VALUES (?, ?, ?, ?, ?)",
                    (
                        topic_data['id'],
                        topic_data['topic_id'],
                        topic_data['name'],
                        topic_data.get('emoji', '📌'),
                        topic_data.get('description')
                    )
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления темы: {e}")
            return False
    
    async def get_topics(self) -> Dict[str, Dict]:
        """Получить все темы"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM topics ORDER BY topic_id") as cursor:
                rows = await cursor.fetchall()
                return {row['id']: dict(row) for row in rows}
    
    async def get_topic_by_id(self, topic_id: str) -> Optional[Dict]:
        """Получить тему по ID"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # === Стоп-слова ===
    
    async def add_ad_keyword(self, keyword: str) -> bool:
        """Добавить стоп-слово"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "INSERT OR IGNORE INTO ad_keywords (keyword) VALUES (?)",
                    (keyword.lower(),)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления стоп-слова: {e}")
            return False
    
    async def remove_ad_keyword(self, keyword: str) -> bool:
        """Удалить стоп-слово"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "DELETE FROM ad_keywords WHERE keyword = ?",
                    (keyword.lower(),)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления стоп-слова: {e}")
            return False
    
    async def get_ad_keywords(self) -> List[str]:
        """Получить список стоп-слов"""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT keyword FROM ad_keywords ORDER BY keyword") as cursor:
                rows = await cursor.fetchall()
                return [row['keyword'] for row in rows]
    
    # === Обработанные посты ===
    
    async def is_processed(self, source_type: str, source_id: str, source_group: str) -> bool:
        """Проверить, обработан ли пост"""
        async with self.get_connection() as conn:
            async with conn.execute(
                "SELECT 1 FROM processed_posts WHERE source_type = ? AND source_id = ? AND source_group = ?",
                (source_type, source_id, source_group)
            ) as cursor:
                return await cursor.fetchone() is not None
    
    async def mark_processed(self, source_type: str, source_id: str, source_group: str, 
                             target_topic_id: int, content_hash: str = None) -> bool:
        """Отметить пост как обработанный"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    '''INSERT OR IGNORE INTO processed_posts 
                       (source_type, source_id, source_group, content_hash, target_topic_id)
                       VALUES (?, ?, ?, ?, ?)''',
                    (source_type, source_id, source_group, content_hash, target_topic_id)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка отметки поста: {e}")
            return False
    
    # === Статистика ===
    
    async def get_stats(self, days: int = 1) -> Dict[str, int]:
        """Получить статистику за N дней"""
        async with self.get_connection() as conn:
            # VK
            async with conn.execute(
                '''SELECT COUNT(*) as count FROM processed_posts 
                   WHERE source_type = 'vk' AND processed_at >= datetime('now', ?)''',
                (f'-{days} days',)
            ) as cursor:
                vk = (await cursor.fetchone())['count']
            
            # Telegram
            async with conn.execute(
                '''SELECT COUNT(*) as count FROM processed_posts 
                   WHERE source_type = 'telegram' AND processed_at >= datetime('now', ?)''',
                (f'-{days} days',)
            ) as cursor:
                tg = (await cursor.fetchone())['count']
            
            return {'vk': vk, 'telegram': tg, 'total': vk + tg}