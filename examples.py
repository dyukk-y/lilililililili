"""
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ АВТОПОСТИНГ БОТА
"""

from datetime import datetime, timedelta
import pytz
from bot import AutoPostBot


def example_basic_usage():
    """Базовое использование"""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Базовое использование")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Опубликовать простой пост
    post_id = bot.publish_post(
        content="Привет, это мой первый пост!",
        delete_after_hours=1
    )
    
    print(f"Пост опубликован с ID: {post_id}")
    print(f"Текущее время NSK: {bot.get_current_nsk_time()}")


def example_time_conversion():
    """Пример преобразования времени"""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Преобразование времени из разных часовых поясов")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Преобразование из Москвы
    moscow_tz = "Europe/Moscow"
    moscow_time = datetime(2026, 2, 23, 15, 30, 0)  # 15:30 по Москве
    nsk_time = bot.convert_to_nsk_time(moscow_time, moscow_tz)
    print(f"Москва: {moscow_time} -> NSK: {nsk_time.strftime('%H:%M')}")
    
    # Преобразование из Нью-Йорка
    ny_tz = "America/New_York"
    ny_time = datetime(2026, 2, 23, 10, 0, 0)  # 10:00 по Нью-Йорку
    nsk_time = bot.convert_to_nsk_time(ny_time, ny_tz)
    print(f"Нью-Йорк: {ny_time} -> NSK: {nsk_time.strftime('%H:%M')}")
    
    # Преобразование из UTC
    utc_time = datetime.now(pytz.UTC)
    nsk_time = bot.convert_to_nsk_time(utc_time)
    print(f"UTC (сейчас): {utc_time.strftime('%H:%M')} -> NSK: {nsk_time.strftime('%H:%M')}")


def example_scheduled_posts():
    """Пример планирования постов"""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Планирование постов на конкретное время NSK")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Запланировать пост на 1 час вперед
    future_time = datetime.now(pytz.UTC) + timedelta(hours=1)
    post_id = bot.publish_post_at_time(
        content="Это пост опубликуется автоматически через час!",
        publish_time=future_time,
        from_tz="UTC",
        delete_after_hours=2
    )
    
    print(f"Пост #{post_id} запланирован")
    
    # Запланировать пост из времени другого часового пояса
    moscow_tz = pytz.timezone("Europe/Moscow")
    moscow_time = datetime.now(moscow_tz) + timedelta(hours=2)
    post_id2 = bot.publish_post_at_time(
        content="Пост запланирован из московского времени",
        publish_time=moscow_time,
        from_tz="Europe/Moscow"
    )
    
    print(f"Пост #{post_id2} запланирован из московского времени")


def example_post_management():
    """Пример управления постами"""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Управление постами")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Опубликовать несколько постов
    ids = []
    for i in range(3):
        post_id = bot.publish_post(f"Пост номер {i+1}")
        ids.append(post_id)
    
    # Показать все посты
    print("\nВсе посты:")
    for post in bot.list_posts():
        print(f"  #{post['id']}: {post['content']} ({post['status']})")
    
    # Показать только опубликованные
    print("\nОпубликованные:")
    for post in bot.list_posts(status='published'):
        print(f"  #{post['id']}: {post['content']}")
    
    # Удалить первый пост
    if ids:
        bot.delete_post(ids[0])
        print(f"\nПост #{ids[0]} удален")


def example_advanced_scheduling():
    """Продвинутый пример с разными параметрами"""
    print("\n" + "="*60)
    print("ПРИМЕР 5: Продвинутое планирование")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Пост, который удалится через 30 минут
    post_id1 = bot.publish_post(
        content="Временный пост на 30 минут",
        delete_after_hours=0.5
    )
    print(f"Пост #{post_id1} будет удален через 30 минут")
    
    # Пост на завтра 10:00 NSK
    tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=7, minute=0, second=0)  # 10:00 NSK = 07:00 UTC+3
    
    post_id2 = bot.publish_post_at_time(
        content="Пост завтра в 10:00 (NSK) с удалением через 3 часа",
        publish_time=tomorrow,
        from_tz="UTC",
        delete_after_hours=3
    )
    print(f"Пост #{post_id2} запланирован на завтра")
    
    # Показать запланированные задания
    print("\nЗапланированные задания:")
    for job in bot.get_jobs_info():
        print(f"  {job['id']}: {job['next_run_time']}")


def example_time_zones():
    """Демонстрация работы с разными часовыми поясами"""
    print("\n" + "="*60)
    print("ПРИМЕР 6: Сравнение времени в разных зонах")
    print("="*60)
    
    bot = AutoPostBot()
    
    # Текущее время UTC
    utc_now = datetime.now(pytz.UTC)
    
    time_zones = {
        "UTC": "UTC",
        "Москва": "Europe/Moscow",
        "Новосибирск": "Asia/Novosibirsk",
        "Екатеринбург": "Asia/Yekaterinburg",
        "Токио": "Asia/Tokyo",
        "Лондон": "Europe/London",
        "Нью-Йорк": "America/New_York",
    }
    
    print(f"Сравнение текущего времени:\n")
    for city, tz_name in time_zones.items():
        tz = pytz.timezone(tz_name)
        local_time = utc_now.astimezone(tz)
        print(f"  {city:15} {local_time.strftime('%H:%M:%S')}")


def example_simulation():
    """Пример симуляции работы"""
    print("\n" + "="*60)
    print("ПРИМЕР 7: Симуляция работы бота")
    print("="*60)
    
    import time
    
    bot = AutoPostBot()
    
    print("Публикуем 3 поста с интервалом в 3 секунды...")
    for i in range(3):
        post_id = bot.publish_post(f"Пост #{i+1} опубликован в {bot.get_current_nsk_time().strftime('%H:%M:%S')}")
        print(f"  Опубликован пост #{post_id}")
        time.sleep(3)
    
    print("\nСписок всех постов:")
    for post in bot.list_posts():
        published = post.get('published_at', 'N/A')
        print(f"  #{post['id']}: {post['content']} ({published})")


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  АВТОПОСТИНГ БОТ - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    # Раскомментируйте нужный пример:
    
    print("\nВыполняем примеры...\n")
    
    example_basic_usage()
    example_time_conversion()
    # example_scheduled_posts()  # Включит фоновый планировщик
    example_post_management()
    example_advanced_scheduling()
    example_time_zones()
    # example_simulation()
    
    print("\n" + "█"*60)
    print("Примеры выполнены!")
    print("█"*60)
