import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoPostBot:
    """Бот для автопостинга с поддержкой времени Новосибирска"""
    
    def __init__(self, storage_file: str = "posts.json"):
        """
        Инициализация бота
        
        Args:
            storage_file: путь к файлу для хранения постов
        """
        self.storage_file = storage_file
        self.scheduler = BackgroundScheduler()
        self.nsk_tz = pytz.timezone('Asia/Novosibirsk')
        self.posts: Dict[str, dict] = {}
        self.post_counter = 0
        
        self._load_posts()
        self._start_scheduler()
        
        logger.info("Бот инициализирован. Часовой пояс: Asia/Novosibirsk")
    
    def _load_posts(self) -> None:
        """Загрузка постов из файла"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.posts = json.load(f)
                    if self.posts:
                        self.post_counter = max(
                            int(post_id) for post_id in self.posts.keys()
                        )
                logger.info(f"Загружено {len(self.posts)} постов из хранилища")
            except Exception as e:
                logger.error(f"Ошибка при загрузке постов: {e}")
                self.posts = {}
        else:
            self.posts = {}
    
    def _save_posts(self) -> None:
        """Сохранение постов в файл"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении постов: {e}")
    
    def _start_scheduler(self) -> None:
        """Запуск планировщика"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик запущен")
    
    def convert_to_nsk_time(self, dt: datetime, from_tz: Optional[str] = None) -> datetime:
        """
        Преобразование времени в время Новосибирска
        
        Args:
            dt: объект datetime
            from_tz: часовой пояс исходного времени (по умолчанию UTC)
        
        Returns:
            datetime в часовом поясе Новосибирска
        """
        try:
            if from_tz is None:
                # Предполагаем UTC если не указан пояс
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                else:
                    if dt.tzinfo is not None:
                        dt = dt.astimezone(pytz.UTC)
            else:
                # Преобразование из указанного часового пояса
                tz = pytz.timezone(from_tz)
                if dt.tzinfo is None:
                    dt = tz.localize(dt)
                else:
                    dt = dt.astimezone(tz)
            
            # Преобразование в NSK
            nsk_time = dt.astimezone(self.nsk_tz)
            logger.info(f"Преобразовано время: {dt} -> {nsk_time}")
            return nsk_time
        except Exception as e:
            logger.error(f"Ошибка при преобразовании времени: {e}")
            return None
    
    def get_current_nsk_time(self) -> datetime:
        """Получение текущего времени в Новосибирске"""
        now_utc = datetime.now(pytz.UTC)
        return now_utc.astimezone(self.nsk_tz)
    
    def publish_post(self, content: str, delete_after_hours: Optional[int] = None) -> str:
        """
        Опубликовать пост
        
        Args:
            content: содержание поста
            delete_after_hours: удалить пост через N часов (опционально)
        
        Returns:
            ID опубликованного поста
        """
        try:
            self.post_counter += 1
            post_id = str(self.post_counter)
            
            current_nsk_time = self.get_current_nsk_time()
            
            post_data = {
                "id": post_id,
                "content": content,
                "published_at": current_nsk_time.isoformat(),
                "status": "published"
            }
            
            # Если указано время удаления
            if delete_after_hours:
                delete_time = current_nsk_time + timedelta(hours=delete_after_hours)
                post_data["delete_at"] = delete_time.isoformat()
                
                # Планируем удаление
                self._schedule_post_deletion(post_id, delete_time)
            
            self.posts[post_id] = post_data
            self._save_posts()
            
            logger.info(f"Пост #{post_id} опубликован. Содержание: {content[:50]}...")
            
            if delete_after_hours:
                logger.info(f"Пост #{post_id} будет удален через {delete_after_hours} часов (в {post_data['delete_at']})")
            
            return post_id
        except Exception as e:
            logger.error(f"Ошибка при публикации поста: {e}")
            return None
    
    def publish_post_at_time(self, content: str, publish_time: datetime, 
                              from_tz: Optional[str] = None, 
                              delete_after_hours: Optional[int] = None) -> str:
        """
        Опубликовать пост в указанное время
        
        Args:
            content: содержание поста
            publish_time: время публикации
            from_tz: часовой пояс времени (по умолчанию UTC)
            delete_after_hours: удалить пост через N часов после публикации
        
        Returns:
            ID запланированного поста
        """
        try:
            # Преобразуем время в NSK
            nsk_publish_time = self.convert_to_nsk_time(publish_time, from_tz)
            
            if nsk_publish_time is None:
                logger.error("Не удалось преобразовать время")
                return None
            
            self.post_counter += 1
            post_id = str(self.post_counter)
            
            post_data = {
                "id": post_id,
                "content": content,
                "scheduled_for": nsk_publish_time.isoformat(),
                "status": "scheduled",
                "delete_after_hours": delete_after_hours
            }
            
            self.posts[post_id] = post_data
            
            # Планируем публикацию
            self._schedule_post_publication(post_id, nsk_publish_time, delete_after_hours)
            
            self._save_posts()
            
            logger.info(f"Пост #{post_id} запланирован на {nsk_publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            return post_id
        except Exception as e:
            logger.error(f"Ошибка при планировании поста: {e}")
            return None
    
    def _schedule_post_publication(self, post_id: str, publish_time: datetime, 
                                    delete_after_hours: Optional[int] = None) -> None:
        """Планирование публикации поста"""
        try:
            job_id = f"publish_{post_id}"
            self.scheduler.add_job(
                self._publish_scheduled_post,
                args=[post_id, delete_after_hours],
                trigger='date',
                run_date=publish_time.replace(tzinfo=None),
                timezone=self.nsk_tz,
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Публикация поста #{post_id} запланирована на {publish_time}")
        except Exception as e:
            logger.error(f"Ошибка при планировании публикации: {e}")
    
    def _publish_scheduled_post(self, post_id: str, delete_after_hours: Optional[int] = None) -> None:
        """Публикация запланированного поста"""
        try:
            if post_id in self.posts:
                post = self.posts[post_id]
                current_nsk_time = self.get_current_nsk_time()
                
                post["status"] = "published"
                post["published_at"] = current_nsk_time.isoformat()
                
                # Если нужно удалить через время
                if delete_after_hours:
                    delete_time = current_nsk_time + timedelta(hours=delete_after_hours)
                    post["delete_at"] = delete_time.isoformat()
                    self._schedule_post_deletion(post_id, delete_time)
                
                self._save_posts()
                logger.info(f"Запланированный пост #{post_id} опубликован")
        except Exception as e:
            logger.error(f"Ошибка при публикации запланированного поста: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """
        Удалить пост
        
        Args:
            post_id: ID поста для удаления
        
        Returns:
            True если успешно, False если пост не найден
        """
        try:
            if post_id in self.posts:
                content_preview = self.posts[post_id]["content"][:50]
                del self.posts[post_id]
                self._save_posts()
                
                # Отменяем запланированное удаление если оно было
                delete_job_id = f"delete_{post_id}"
                if self.scheduler.get_job(delete_job_id):
                    self.scheduler.remove_job(delete_job_id)
                
                logger.info(f"Пост #{post_id} удален. Содержание: {content_preview}...")
                return True
            else:
                logger.warning(f"Пост #{post_id} не найден")
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении поста: {e}")
            return False
    
    def _schedule_post_deletion(self, post_id: str, delete_time: datetime) -> None:
        """Планирование удаления поста"""
        try:
            job_id = f"delete_{post_id}"
            self.scheduler.add_job(
                self.delete_post,
                args=[post_id],
                trigger='date',
                run_date=delete_time.replace(tzinfo=None),
                timezone=self.nsk_tz,
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Удаление поста #{post_id} запланировано на {delete_time}")
        except Exception as e:
            logger.error(f"Ошибка при планировании удаления: {e}")
    
    def get_post(self, post_id: str) -> Optional[dict]:
        """Получить информацию о посте"""
        return self.posts.get(post_id)
    
    def list_posts(self, status: Optional[str] = None) -> List[dict]:
        """
        Получить список постов
        
        Args:
            status: фильтр по статусу ('published', 'scheduled' или None для всех)
        
        Returns:
            Список постов
        """
        posts_list = list(self.posts.values())
        
        if status:
            posts_list = [p for p in posts_list if p.get("status") == status]
        
        return sorted(posts_list, key=lambda x: x.get("published_at") or x.get("scheduled_for", ""), reverse=True)
    
    def get_jobs_info(self) -> List[dict]:
        """Получить информацию о запланированных заданиях"""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "next_run_time": str(job.next_run_time),
                "trigger": str(job.trigger)
            })
        return jobs_info
    
    def shutdown(self) -> None:
        """Остановить бота (завершить планировщик)"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Бот остановлен")


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

if __name__ == "__main__":
    # Инициализация бота
    bot = AutoPostBot()
    
    print("=" * 60)
    print("АВТОПОСТИНГ БОТ - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    print("=" * 60)
    
    # Пример 1: Опубликовать пост сейчас
    print("\n[1] Публикация поста сейчас:")
    post_id = bot.publish_post(
        content="Это мой первый пост! 🎉",
        delete_after_hours=2
    )
    if post_id:
        print(f"✓ Пост #{post_id} опубликован")
        print(f"  Удалится через 2 часа")
    
    # Пример 2: Получить текущее время в Новосибирске
    print("\n[2] Текущее время в Новосибирске:")
    nsk_now = bot.get_current_nsk_time()
    print(f"✓ {nsk_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Пример 3: Преобразовать время из другого часового пояса
    print("\n[3] Преобразование времени:")
    utc_time = datetime.now(pytz.UTC)
    print(f"  UTC: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    nsk_time = bot.convert_to_nsk_time(utc_time)
    print(f"  NSK: {nsk_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Пример 4: Опубликовать пост в определенное время
    print("\n[4] Планирование поста на будущее:")
    future_time = datetime.now(pytz.UTC) + timedelta(hours=1)
    post_id2 = bot.publish_post_at_time(
        content="Это запланированный пост!",
        publish_time=future_time,
        from_tz="UTC",
        delete_after_hours=3
    )
    if post_id2:
        print(f"✓ Пост #{post_id2} запланирован")
    
    # Пример 5: Список всех постов
    print("\n[5] Все опубликованные посты:")
    published = bot.list_posts(status='published')
    for post in published:
        print(f"  #{post['id']}: {post['content'][:40]}... "
              f"({post.get('published_at', 'N/A')})")
    
    print("\n[6] Запланированные посты:")
    scheduled = bot.list_posts(status='scheduled')
    for post in scheduled:
        print(f"  #{post['id']}: {post['content'][:40]}... "
              f"({post.get('scheduled_for', 'N/A')})")
    
    # Пример 6: Информация о запланированных заданиях
    print("\n[7] Запланированные задания:")
    jobs = bot.get_jobs_info()
    for job in jobs:
        print(f"  {job['id']}: {job['next_run_time']}")
    
    print("\n" + "=" * 60)
    print("Бот готов к работе!")
    print("Хранилище постов: posts.json")
    print("=" * 60)
    
    # Бот будет работать в фоне
    # Для остановки: Ctrl+C или bot.shutdown()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nОстановка бота...")
        bot.shutdown()
        print("Бот остановлен")
