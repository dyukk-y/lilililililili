"""
ИНТЕГРАЦИЯ С ДРУГИМИ ПЛАТФОРМАМИ
Шаблоны для интеграции AutoPostBot с разными сервисами
"""

from bot import AutoPostBot
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# INSTAGRAM INTEGRATION
# ============================================================================

class InstagramAutoPostBot(AutoPostBot):
    """
    Интеграция с Instagram (потребуется instagram-api или instagrapi)
    
    Установка:
    pip install instagrapi
    """
    
    def __init__(self, username: str, password: str, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        self.username = username
        self.password = password
        
        try:
            from instagrapi import Client
            self.client = Client()
            self.client.login(username, password)
            self.instagram_available = True
            logger.info("Instagram клиент инициализирован")
        except ImportError:
            logger.warning("instagrapi не установлен: pip install instagrapi")
            self.instagram_available = False
    
    def publish_post(self, content: str, image_path: str = None, **kwargs) -> str:
        """
        Опубликовать пост в Instagram
        
        Args:
            content: подпись к посту
            image_path: путь к изображению
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.instagram_available and image_path:
            try:
                # Опубликовать в Instagram
                media = self.client.photo_upload(image_path, caption=content)
                logger.info(f"Пост опубликован в Instagram: {media.pk}")
            except Exception as e:
                logger.error(f"Ошибка при публикации в Instagram: {e}")
        
        return post_id


# ============================================================================
# VKONTAKTE (VK) INTEGRATION
# ============================================================================

class VKAutoPostBot(AutoPostBot):
    """
    Интеграция с VK (ВКонтакте)
    
    Установка:
    pip install vk-api
    """
    
    def __init__(self, access_token: str, group_id: int, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        self.access_token = access_token
        self.group_id = group_id
        
        try:
            import vk
            self.vk = vk.API(access_token=access_token, v='5.131')
            self.vk_available = True
            logger.info("VK API инициализирован")
        except ImportError:
            logger.warning("vk-api не установлен: pip install vk-api")
            self.vk_available = False
    
    def publish_post(self, content: str, notify_vk: bool = True, **kwargs) -> str:
        """
        Опубликовать пост в ВКонтакте
        
        Args:
            content: текст поста
            notify_vk: отправить в VK
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.vk_available and notify_vk:
            try:
                # Опубликовать на стену группы
                result = self.vk.wall.post(
                    owner_id=-self.group_id,
                    message=content
                )
                logger.info(f"Пост опубликован в VK: {result['post_id']}")
            except Exception as e:
                logger.error(f"Ошибка при публикации в VK: {e}")
        
        return post_id


# ============================================================================
# TWITTER / X INTEGRATION
# ============================================================================

class TwitterAutoPostBot(AutoPostBot):
    """
    Интеграция с Twitter/X
    
    Установка:
    pip install tweepy
    """
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, 
                 access_token_secret: str, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        try:
            import tweepy
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
            self.api = tweepy.API(auth)
            self.client = tweepy.Client(
                bearer_token=api_key,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            self.twitter_available = True
            logger.info("Twitter API инициализирован")
        except ImportError:
            logger.warning("tweepy не установлен: pip install tweepy")
            self.twitter_available = False
    
    def publish_post(self, content: str, notify_twitter: bool = True, **kwargs) -> str:
        """
        Опубликовать твит
        
        Args:
            content: текст твита (макс 280 символов)
            notify_twitter: отправить в Twitter
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.twitter_available and notify_twitter:
            try:
                # Отправить твит
                response = self.client.create_tweet(text=content[:280])
                logger.info(f"Твит опубликован: {response.data['id']}")
            except Exception as e:
                logger.error(f"Ошибка при публикации твита: {e}")
        
        return post_id


# ============================================================================
# REDDIT INTEGRATION
# ============================================================================

class RedditAutoPostBot(AutoPostBot):
    """
    Интеграция с Reddit
    
    Установка:
    pip install praw
    """
    
    def __init__(self, client_id: str, client_secret: str, username: str,
                 password: str, subreddit: str, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        self.subreddit_name = subreddit
        
        try:
            import praw
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=f"AutoPostBot/1.0 by {username}",
                username=username,
                password=password
            )
            self.subreddit = reddit.subreddit(subreddit)
            self.reddit_available = True
            logger.info(f"Reddit API инициализирован для r/{subreddit}")
        except ImportError:
            logger.warning("praw не установлен: pip install praw")
            self.reddit_available = False
    
    def publish_post(self, content: str, title: str = None, notify_reddit: bool = True, **kwargs) -> str:
        """
        Опубликовать пост в Reddit
        
        Args:
            content: содержание поста
            title: заголовок поста
            notify_reddit: отправить в Reddit
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.reddit_available and notify_reddit:
            try:
                post_title = title or "AutoPost"
                submission = self.subreddit.submit(
                    title=post_title,
                    selftext=content
                )
                logger.info(f"Пост опубликован в Reddit: r/{self.subreddit_name}/{submission.id}")
            except Exception as e:
                logger.error(f"Ошибка при публикации на Reddit: {e}")
        
        return post_id


# ============================================================================
# WORDPRESS INTEGRATION
# ============================================================================

class WordPressAutoPostBot(AutoPostBot):
    """
    Интеграция с WordPress
    
    Установка:
    pip install wordpress-api
    """
    
    def __init__(self, url: str, username: str, password: str, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        self.wp_url = url
        self.wp_username = username
        self.wp_password = password
        
        try:
            from wordpress_api import Client
            self.client = Client({
                'base_url': url,
                'wp_user': username,
                'wp_pass': password,
                'wp_path': 'wp-json'
            })
            self.wordpress_available = True
            logger.info(f"WordPress API инициализирован: {url}")
        except ImportError:
            logger.warning("wordpress-api не установлен: pip install wordpress-api")
            self.wordpress_available = False
    
    def publish_post(self, content: str, title: str = None, status: str = "publish",
                     notify_wp: bool = True, **kwargs) -> str:
        """
        Опубликовать пост в WordPress
        
        Args:
            content: содержание поста
            title: заголовок поста
            status: статус ('publish', 'draft', 'pending')
            notify_wp: опубликовать на WordPress
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.wordpress_available and notify_wp:
            try:
                post_data = {
                    'title': title or 'Auto Post',
                    'content': content,
                    'status': status
                }
                result = self.client.posts.create(post_data)
                logger.info(f"Пост опубликован в WordPress: ID {result['id']}")
            except Exception as e:
                logger.error(f"Ошибка при публикации на WordPress: {e}")
        
        return post_id


# ============================================================================
# TELEGRAM CHANNELS INTEGRATION
# ============================================================================

class TelegramChannelAutoPostBot(AutoPostBot):
    """
    Интеграция с Telegram каналом
    
    Установка:
    pip install python-telegram-bot
    """
    
    def __init__(self, token: str, channel_id: int, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        
        self.token = token
        self.channel_id = channel_id
        
        try:
            from telegram import Bot
            self.bot = Bot(token=token)
            self.telegram_available = True
            logger.info(f"Telegram бот инициализирован для канала {channel_id}")
        except ImportError:
            logger.warning("python-telegram-bot не установлен")
            self.telegram_available = False
    
    def publish_post(self, content: str, notify_telegram: bool = True, **kwargs) -> str:
        """
        Опубликовать пост в Telegram канал
        
        Args:
            content: текст сообщения
            notify_telegram: отправить в Telegram
            **kwargs: дополнительные параметры
        
        Returns:
            ID поста
        """
        post_id = super().publish_post(content, **kwargs)
        
        if self.telegram_available and notify_telegram:
            try:
                msg = self.bot.send_message(
                    chat_id=self.channel_id,
                    text=content
                )
                logger.info(f"Сообщение опубликовано в Telegram: {msg.message_id}")
            except Exception as e:
                logger.error(f"Ошибка при публикации в Telegram: {e}")
        
        return post_id


# ============================================================================
# MULTI-PLATFORM BOT (публикация на несколько платформ одновременно)
# ============================================================================

class MultiPlatformAutoPostBot(AutoPostBot):
    """
    Публикация на несколько платформ одновременно
    """
    
    def __init__(self, storage_file: str = "posts.json"):
        super().__init__(storage_file)
        self.platforms = {}
    
    def add_platform(self, name: str, bot_instance):
        """Добавить платформу"""
        self.platforms[name] = bot_instance
        logger.info(f"Платформа добавлена: {name}")
    
    def publish_to_all(self, content: str, **kwargs) -> dict:
        """
        Опубликовать на все платформы
        
        Returns:
            Словарь с результатами публикации на каждую платформу
        """
        local_post_id = super().publish_post(content, **kwargs)
        
        results = {
            'local': local_post_id
        }
        
        for platform_name, platform_bot in self.platforms.items():
            try:
                post_id = platform_bot.publish_post(content, **kwargs)
                results[platform_name] = post_id
                logger.info(f"Пост опубликован на {platform_name}: {post_id}")
            except Exception as e:
                logger.error(f"Ошибка при публикации на {platform_name}: {e}")
                results[platform_name] = None
        
        return results


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

def example_multi_platform():
    """Пример использования многоплатформенного бота"""
    
    print("="*60)
    print("МУЛЬТИПЛАТФОРМЕННЫЙ АВТОПОСТИНГ БОТ")
    print("="*60)
    
    # Создание многоплатформенного бота
    multi_bot = MultiPlatformAutoPostBot()
    
    # Добавление платформ (с реальными учетными данными)
    # Это просто примеры - замените на реальные параметры
    
    # VK
    # vk_bot = VKAutoPostBot(access_token="YOUR_TOKEN", group_id=12345)
    # multi_bot.add_platform("VK", vk_bot)
    
    # Twitter
    # twitter_bot = TwitterAutoPostBot(
    #     api_key="YOUR_KEY",
    #     api_secret="YOUR_SECRET",
    #     access_token="YOUR_TOKEN",
    #     access_token_secret="YOUR_TOKEN_SECRET"
    # )
    # multi_bot.add_platform("Twitter", twitter_bot)
    
    # Telegram Channel
    # telegram_bot = TelegramChannelAutoPostBot(token="BOT_TOKEN", channel_id=-123456)
    # multi_bot.add_platform("Telegram", telegram_bot)
    
    print("\n✅ Мультиплатформенный бот создан")
    
    # Опубликовать на все платформы
    content = "Это пост, опубликованный одновременно на несколько платформ! 🚀"
    
    print(f"\n📝 Публикуем: {content}\n")
    # results = multi_bot.publish_to_all(content)
    
    # print("Результаты публикации:")
    # for platform, post_id in results.items():
    #     status = "✅" if post_id else "❌"
    #     print(f"  {status} {platform}: {post_id}")


if __name__ == "__main__":
    example_multi_platform()
