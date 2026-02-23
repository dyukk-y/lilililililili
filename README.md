# AutoPost Bot 🤖

Мощный бот для автоматической публикации постов с поддержкой планирования, удаления и интеграций с различными платформами. Локальная работа с часовыми поясами (базируется на NSK - Новосибирск).

**Основные возможности:**
- 📝 Опубликовать пост
- ⏰ Запланировать пост на конкретное время
- 🗑️ Автоудаление постов через N часов
- 🌍 Конвертация времени между часовыми поясами  
- 💾 Локальное хранилище (JSON)
- 🔌 Интеграции с Telegram, VK, Instagram, Twitter, Discord, Slack
- 🔄 Фоновый планировщик (APScheduler)

## ⚡ Быстрый старт

### 1. Клонирование
```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Использование в коде
```python
from bot import AutoPostBot
from config import STORAGE_FILE

# Инициализация
bot = AutoPostBot(storage_file=STORAGE_FILE)

# Опубликовать пост сейчас
bot.publish_post("Привет мир!")

# Остановить
bot.shutdown()
```

## 📖 Основные методы

```python
# Опубликовать пост сейчас
bot.publish_post(content, delete_after_hours=None)

# Запланировать на конкретное время
bot.publish_post_at_time(
    content="Текст поста",
    publish_time=datetime_object,
    from_tz="UTC",  # Часовой пояс времени
    delete_after_hours=24
)

# Удалить пост
bot.delete_post(post_id)

# Конвертировать время в НСК
bot.convert_to_nsk_time(dt, from_tz="Europe/Moscow")

# Получить текущее время НСК
bot.get_current_nsk_time()

# Получить посты
bot.list_posts()  # Все
bot.list_posts(status='published')  # Опубликованные
bot.list_posts(status='scheduled')  # Запланированные

# Информация о заданиях
bot.get_jobs_info()

# Остановить бота
bot.shutdown()
```

## 🔧 Примеры кода

### Пример 1: Опубликовать с автоудалением
```python
from bot import AutoPostBot

bot = AutoPostBot()

# Опубликовать и удалить через 2 часа
post_id = bot.publish_post(
    content="Это временный пост",
    delete_after_hours=2
)

print(f"Пост #{post_id} опубликован и удалится через 2 часа")
bot.shutdown()
```

### Пример 2: Запланировать пост
```python
from bot import AutoPostBot
from datetime import datetime, timedelta
import pytz

bot = AutoPostBot()

# Запланировать на 1 час вперед
future = datetime.now(pytz.UTC) + timedelta(hours=1)
post_id = bot.publish_post_at_time(
    content="Это запланированный пост",
    publish_time=future,
    from_tz="UTC"
)

print(f"Пост #{post_id} запланирован")
# Бот работает в фоне пока работает приложение
```

### Пример 3: Конвертация времени
```python
from bot import AutoPostBot
from datetime import datetime

bot = AutoPostBot()

# Конвертировать время из Москвы в НСК
moscow_time = datetime(2026, 2, 23, 15, 30)  # 15:30 Москва
nsk_time = bot.convert_to_nsk_time(moscow_time, "Europe/Moscow")

print(f"Москва 15:30 = НСК {nsk_time.strftime('%H:%M')}")
```

### Пример 4: Интеграция с Telegram
```python
from telegram_bot import TelegramAutoPostBot
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS, STORAGE_FILE

# Требует: pip install python-telegram-bot
bot = TelegramAutoPostBot(
    telegram_token=TELEGRAM_TOKEN,
    chat_ids=TELEGRAM_CHAT_IDS,
    storage_file=STORAGE_FILE
)

# Опубликовать пост с уведомлением в Telegram
bot.publish_post(
    content="Пост с уведомлением",
    notify_telegram=True
)
```

## ⚙️ Конфигурация

Все параметры находятся в `config.py`:

```python
# Основные параметры
STORAGE_FILE = "posts.json"          # Файл для хранения
TIMEZONE = "Asia/Novosibirsk"        # Часовой пояс
LOG_LEVEL = "INFO"                   # Уровень логирования

# Telegram
TELEGRAM_ENABLED = False
TELEGRAM_TOKEN = ""                  # Получить у @BotFather
TELEGRAM_CHAT_IDS = []               # Получить у @userinfobot

# VK
VK_ENABLED = False
VK_ACCESS_TOKEN = ""                 # Из VK Admin panel
VK_GROUP_ID = 0

# Instagram
INSTAGRAM_ENABLED = False
INSTAGRAM_USERNAME = ""
INSTAGRAM_PASSWORD = ""

# Twitter / X
TWITTER_ENABLED = False
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""

# Discord
DISCORD_ENABLED = False
DISCORD_WEBHOOK_URL = ""

# Slack
SLACK_ENABLED = False
SLACK_WEBHOOK_URL = ""
```

## 💾 Что скачать для работы

### Основные зависимости (ОБЯЗАТЕЛЬНО)

```bash
pip install -r requirements.txt
```

Установит:
- **pytz** - работа с часовыми поясами
- **APScheduler** - фоновой планировщик

### Опциональные (для интеграций)

**Telegram:**
```bash
pip install python-telegram-bot>=20.0
```

**VK:**
```bash
pip install vk-api>=11.9.9
```

**Instagram:**
```bash
pip install instagrapi>=2.0.0
```

**Twitter/X:**
```bash
pip install tweepy>=4.14.0
```

**Discord:**
```bash
pip install discord.py>=2.3.0
```

**База данных (SQLAlchemy):**
```bash
pip install sqlalchemy>=2.0.0 psycopg2-binary>=2.9.0
```

## 📁 Структура проекта

```
lilililililili/
├── bot.py                 # Основной класс AutoPostBot (406 строк)
├── config.py              # Конфигурация всех параметров
├── telegram_bot.py        # Интеграция Telegram (опционально)
├── platform_integrations.py # Интеграции с другими платформами
├── requirements.txt       # Список зависимостей для скачивания
├── setup.py              # Конфиг установки пакета
├── pyproject.toml        # Конфиг проекта
├── README.md             # Этот файл (документация)
└── LICENSE               # MIT лицензия
```

## 🔐 Здравый смысл о безопасности

⚠️ **НИКОГДА** не коммитьте токены и пароли в Git!

Используйте переменные окружения:
```python
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
```

Или создайте `.env` файл и используйте `python-dotenv`:
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
```

## 📊 Производительность

- **Память:** ~15-30 MB при работе
- **CPU:** Минимальное использование (планировщик работает в фоне)
- **Постов в памяти:** Зависит от хранилища (JSON файл)
- **Скорость:** < 1ms для операций с постами

## 🐛 Решение проблем

**Ошибка: ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**Ошибка часового пояса:**
```python
# Используйте стандартные IANA часовые пояса
bot.convert_to_nsk_time(dt, "Europe/Moscow")  # ✓ Правильно
bot.convert_to_nsk_time(dt, "MSK")            # ✗ Неправильно
```

**Telegram не работает:**
1. Проверьте `TELEGRAM_TOKEN` в `config.py`
2. Убедитесь что `TELEGRAM_ENABLED = True`
3. Правильный ли `TELEGRAM_CHAT_IDS`? (узнайте у @userinfobot)

**Посты не удаляются:**
- Бот должен быть запущен (scheduler работает)
- Проверьте что `TIMEZONE` правильный

## 📚 Дополнительная информация

### IANA Часовые пояса

```
Asia/Novosibirsk    - Новосибирск (UTC+7)
Europe/Moscow       - Москва (UTC+3)
Asia/Yekaterinburg  - Екатеринбург (UTC+5)
Europe/London       - Лондон (UTC+0/+1)
Asia/Tokyo          - Токио (UTC+9)
America/New_York    - Нью-Йорк (UTC-5/-4)
America/Los_Angeles - Лос-Анджелес (UTC-8/-7)
UTC                 - Скоординированное всемирное время
```

Полный список: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### Полезные ссылки
- APScheduler документация: https://apscheduler.readthedocs.io/
- Python-telegram-bot: https://python-telegram-bot.readthedocs.io/
- pytz: https://pypi.org/project/pytz/

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 👨‍💻 Автор

[dyukk-y](https://github.com/dyukk-y)

## ⭐ Поддержка

Если проект вам помог, поставьте ⭐ на GitHub!

---

**Последнее обновление:** Февраль 2026
