"""
Парсер групп ВКонтакте
Использует Community Token (безопасно)
"""

import asyncio
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
import aiohttp

from database import Database
from message_formatter import MessageFormatter

class VKParser:
    """Парсер VK групп"""
    
    def __init__(self, vk_token: str, db: Database, formatter: MessageFormatter, 
                 check_interval: int = 60):
        self.vk_token = vk_token
        self.db = db
        self.formatter = formatter
        self.check_interval = check_interval
        self.is_running = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API VK
        self.api_url = "https://api.vk.com/method/"
        self.api_version = "5.131"
        
        # Лимиты
        self.request_count = 0
        self.last_request_reset = datetime.now()
    
    async def start(self):
        """Запуск парсера"""
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        logger.info("✅ VK парсер запущен")
        
        while self.is_running:
            try:
                await self.check_all_groups()
            except Exception as e:
                logger.error(f"Ошибка в VK парсере: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Остановка парсера"""
        self.is_running = False
        if self.session:
            asyncio.create_task(self.session.close())
        logger.info("VK парсер остановлен")
    
    async def check_all_groups(self):
        """Проверка всех групп"""
        groups = await self.db.get_vk_groups(enabled_only=True)
        topics = await self.db.get_topics()
        ad_keywords = await self.db.get_ad_keywords()
        
        if not groups:
            logger.debug("Нет активных VK групп")
            return
        
        logger.info(f"Проверка {len(groups)} VK групп")
        
        for group in groups:
            try:
                await self.check_rate_limits()
                await self.check_group(group, topics, ad_keywords)
                await asyncio.sleep(1)  # Пауза между группами
            except Exception as e:
                logger.error(f"Ошибка при проверке группы {group['name']}: {e}")
    
    async def check_rate_limits(self):
        """Соблюдение лимитов VK API"""
        now = datetime.now()
        
        if (now - self.last_request_reset).seconds >= 1:
            self.request_count = 0
            self.last_request_reset = now
        
        if self.request_count >= 3:
            wait_time = 1 - (now - self.last_request_reset).seconds
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_request_reset = datetime.now()
    
    async def check_group(self, group: Dict, topics: Dict, ad_keywords: List[str]):
        """Проверка одной группы"""
        
        # Определяем owner_id
        group_id = group['group_id']
        
        if group_id.isdigit() or (group_id.startswith('-') and group_id[1:].isdigit()):
            owner_id = -int(group_id.lstrip('-'))
        else:
            # По короткому имени получаем ID
            owner_id = await self.get_group_owner_id(group_id)
            if not owner_id:
                return
        
        # Получаем посты
        posts = await self.get_group_posts(owner_id, count=5)
        
        for post in posts:
            await self.process_post(post, group, topics, ad_keywords, owner_id)
    
    async def get_group_owner_id(self, screen_name: str) -> Optional[int]:
        """Получение ID группы по короткому имени"""
        params = {
            'group_id': screen_name,
            'access_token': self.vk_token,
            'v': self.api_version
        }
        
        try:
            self.request_count += 1
            async with self.session.get(self.api_url + 'groups.getById', params=params) as response:
                data = await response.json()
                
                if 'error' in data:
                    logger.error(f"VK API ошибка: {data['error']['error_msg']}")
                    return None
                
                if data.get('response') and len(data['response']['groups']) > 0:
                    return -data['response']['groups'][0]['id']
                
        except Exception as e:
            logger.error(f"Ошибка получения ID группы {screen_name}: {e}")
        
        return None
    
    async def get_group_posts(self, owner_id: int, count: int = 5) -> List[Dict]:
        """Получение постов из группы"""
        params = {
            'owner_id': owner_id,
            'count': count,
            'extended': 1,
            'access_token': self.vk_token,
            'v': self.api_version
        }
        
        try:
            self.request_count += 1
            async with self.session.get(self.api_url + 'wall.get', params=params) as response:
                data = await response.json()
                
                if 'error' in data:
                    logger.error(f"VK API ошибка: {data['error']['error_msg']}")
                    return []
                
                if data.get('response') and 'items' in data['response']:
                    return data['response']['items']
                
        except Exception as e:
            logger.error(f"Ошибка получения постов: {e}")
        
        return []
    
    async def process_post(self, post: Dict, group: Dict, topics: Dict, 
                           ad_keywords: List[str], owner_id: int):
        """Обработка одного поста"""
        post_id = str(post['id'])
        source_group = group['group_id']
        
        # Проверяем дубликат
        if await self.db.is_processed('vk', post_id, source_group):
            return
        
        # Текст поста
        text = post.get('text', '')
        if not text and not group['all_posts']:
            return
        
        # Проверка на стоп-слова
        if await self.contains_ad_keywords(text, ad_keywords):
            logger.debug(f"Пост {post_id} содержит рекламу, пропущен")
            return
        
        if group['exclude_keywords'] and await self.contains_ad_keywords(text, group['exclude_keywords']):
            logger.debug(f"Пост {post_id} содержит исключающие слова, пропущен")
            return
        
        # Проверка даты/цены
        if group['require_date_or_price']:
            has_date = self.contains_date(text)
            has_price = self.contains_price(text)
            if not (has_date or has_price):
                logger.debug(f"Пост {post_id} не содержит дату или цену, пропущен")
                return
        
        # Определяем тему
        target_topic = await self.determine_target_topic(post, group, topics)
        if not target_topic:
            logger.debug(f"Для поста {post_id} не определена тема")
            return
        
        # Форматируем
        formatted_text = self.formatter.format_vk_post(text, target_topic)
        
        # Ссылки
        source_link = f"https://vk.com/wall{owner_id}_{post_id}"
        
        author_link = None
        if post.get('signer_id'):
            author_link = f"https://vk.com/id{post['signer_id']}"
        elif post.get('from_id') and post['from_id'] > 0:
            author_link = f"https://vk.com/id{post['from_id']}"
        
        # TODO: Отправка в Telegram группу
        logger.info(f"✅ Новый пост из VK: {group['name']} -> {target_topic['name']}")
        
        # Отмечаем обработанным
        await self.db.mark_processed(
            'vk', post_id, source_group, 
            target_topic['topic_id'],
            hashlib.md5(text.encode()).hexdigest()
        )
    
    async def determine_target_topic(self, post: Dict, group: Dict, topics: Dict) -> Optional[Dict]:
        """Определение целевой темы"""
        text = post.get('text', '').lower()
        
        if group['all_posts']:
            return topics.get(group['target_topic'])
        
        if group['classifier_type'] == 'buy_sell':
            if any(word in text for word in ['отдам', 'даром', 'бесплатно']):
                return topics.get('otdam')
            elif any(word in text for word in ['куплю', 'ищу', 'нужен', 'приобрету']):
                return topics.get('kuplyu')
            elif any(word in text for word in ['продам', 'продаю', 'реализую', 'цена']):
                return topics.get('prodam')
            else:
                return None
        
        elif group['classifier_type'] == 'keywords' and group['keywords']:
            if any(keyword.lower() in text for keyword in group['keywords']):
                return topics.get(group['target_topic'])
        
        return None
    
    async def contains_ad_keywords(self, text: str, keywords: List[str]) -> bool:
        """Проверка наличия стоп-слов"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def contains_date(self, text: str) -> bool:
        """Проверка наличия даты"""
        text_lower = text.lower()
        date_indicators = [
            'сегодня', 'завтра', 'вчера',
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ]
        return any(indicator in text_lower for indicator in date_indicators)
    
    def contains_price(self, text: str) -> bool:
        """Проверка наличия цены"""
        text_lower = text.lower()
        price_indicators = ['руб', '₽', 'р.', 'цена', 'стоимость']
        return any(indicator in text_lower for indicator in price_indicators)