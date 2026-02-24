"""
Управление аккаунтами VK и Telegram
Авторизация и выход через бота
"""

import pickle
from typing import Optional, Tuple
from loguru import logger
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from vk_api import VkApi
from vk_api.exceptions import ApiError

from database import Database

class AccountManager:
    """Менеджер аккаунтов"""
    
    def __init__(self, db: Database):
        self.db = db
        self.tg_client: Optional[TelegramClient] = None
        self.auth_in_progress = {}  # user_id -> состояние
    
    # === VK ===
    
    async def login_vk(self, token: str) -> Tuple[bool, str]:
        """
        Авторизация в VK через токен
        
        Returns:
            (успех, сообщение)
        """
        try:
            # Проверяем токен
            vk_session = VkApi(token=token)
            vk = vk_session.get_api()
            
            # Пробуем получить информацию о пользователе
            user = vk.users.get()
            
            if user and len(user) > 0:
                # Сохраняем токен
                await self.db.save_vk_token(token)
                
                name = f"{user[0]['first_name']} {user[0]['last_name']}"
                logger.info(f"✅ VK авторизация успешна: {name}")
                return True, f"✅ Успешный вход!\nАккаунт: {name}"
            else:
                return False, "❌ Неверный токен"
                
        except ApiError as e:
            logger.error(f"VK API ошибка: {e}")
            return False, f"❌ Ошибка VK API: {e}"
        except Exception as e:
            logger.error(f"Ошибка VK авторизации: {e}")
            return False, f"❌ Ошибка: {e}"
    
    async def logout_vk(self) -> bool:
        """Выход из VK аккаунта"""
        return await self.db.deactivate_session('vk')
    
    async def get_vk_token(self) -> Optional[str]:
        """Получение активного VK токена"""
        return await self.db.get_vk_token()
    
    # === Telegram ===
    
    async def start_tg_login(self, user_id: int, phone: str) -> Tuple[bool, str, Optional[TelegramClient]]:
        """
        Начало авторизации Telegram
        
        Returns:
            (успех, сообщение, клиент)
        """
        try:
            # Создаем клиента с уникальной сессией
            client = TelegramClient(f'sessions/user_{user_id}', None, None)
            await client.connect()
            
            if not await client.is_user_authorized():
                # Отправляем код
                await client.send_code_request(phone)
                
                # Сохраняем состояние
                self.auth_in_progress[user_id] = {
                    'client': client,
                    'phone': phone,
                    'stage': 'code'
                }
                
                return True, "📱 Код подтверждения отправлен в Telegram. Введите его:", client
            else:
                # Уже авторизован
                return False, "❌ Аккаунт уже авторизован", client
                
        except Exception as e:
            logger.error(f"Ошибка Telegram авторизации: {e}")
            return False, f"❌ Ошибка: {e}", None
    
    async def complete_tg_login(self, user_id: int, code: str, password: str = None) -> Tuple[bool, str]:
        """
        Завершение авторизации Telegram
        
        Returns:
            (успех, сообщение)
        """
        try:
            if user_id not in self.auth_in_progress:
                return False, "❌ Сессия не найдена. Начните заново."
            
            state = self.auth_in_progress[user_id]
            client = state['client']
            
            try:
                # Пробуем войти с кодом
                await client.sign_in(phone=state['phone'], code=code)
                
            except SessionPasswordNeededError:
                # Требуется двухфакторка
                if password:
                    await client.sign_in(password=password)
                else:
                    # Запрашиваем пароль
                    state['stage'] = 'password'
                    return False, "🔐 Требуется пароль двухфакторной аутентификации. Введите пароль:"
            
            # Успешная авторизация
            me = await client.get_me()
            
            # Сохраняем сессию
            session_data = pickle.dumps(client.session.save())
            await self.db.save_telegram_session(session_data, state['phone'])
            
            # Очищаем состояние
            del self.auth_in_progress[user_id]
            
            username = f"@{me.username}" if me.username else "без username"
            logger.info(f"✅ Telegram авторизация успешна: {me.first_name} ({username})")
            return True, f"✅ Успешный вход!\nАккаунт: {me.first_name} {username}"
            
        except Exception as e:
            logger.error(f"Ошибка завершения Telegram авторизации: {e}")
            return False, f"❌ Ошибка: {e}"
    
    async def logout_tg(self) -> bool:
        """Выход из Telegram аккаунта"""
        # Закрываем клиент если есть
        if self.tg_client:
            await self.tg_client.disconnect()
            self.tg_client = None
        
        # Деактивируем сессию в БД
        return await self.db.deactivate_session('telegram')
    
    async def get_tg_client(self) -> Optional[TelegramClient]:
        """Получение активного Telegram клиента"""
        # Проверяем, есть ли уже клиент
        if self.tg_client and self.tg_client.is_connected():
            return self.tg_client
        
        # Загружаем сессию из БД
        session_data, phone = await self.db.get_telegram_session()
        if not session_data:
            return None
        
        try:
            # Восстанавливаем клиент
            client = TelegramClient('sessions/current', None, None)
            client.session.load(pickle.loads(session_data))
            await client.connect()
            
            if await client.is_user_authorized():
                self.tg_client = client
                logger.info(f"✅ Telegram клиент восстановлен для {phone}")
                return client
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка восстановления Telegram клиента: {e}")
            return None
    
    async def get_session_status(self) -> Tuple[bool, bool]:
        """Получение статуса сессий"""
        status = await self.db.get_session_status()
        return status['vk'], status['telegram']