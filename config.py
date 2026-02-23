"""
КОНФИГУРАЦИЯ ПРОЕКТА
"""

# Файл для хранения постов
STORAGE_FILE = "posts.json"

# Часовой пояс (Asia/Novosibirsk, UTC, Europe/Moscow, и т.д.)
TIMEZONE = "Asia/Novosibirsk"

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"


# ============================================================================
# ИНТЕГРАЦИИ (заполните свои токены)
# ============================================================================

# TELEGRAM
TELEGRAM_ENABLED = False
TELEGRAM_TOKEN = ""  # Получите у @BotFather, узнайте Chat ID у @userinfobot
TELEGRAM_CHAT_IDS = []  # Пример: [123456789]

# VK (ВКОНТАКТЕ)
VK_ENABLED = False
VK_ACCESS_TOKEN = ""  # Из Управление → Настройки → API
VK_GROUP_ID = 0

# INSTAGRAM
INSTAGRAM_ENABLED = False
INSTAGRAM_USERNAME = ""
INSTAGRAM_PASSWORD = ""

# TWITTER / X
TWITTER_ENABLED = False
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""

# DISCORD
DISCORD_ENABLED = False
DISCORD_WEBHOOK_URL = ""

# SLACK
SLACK_ENABLED = False
SLACK_WEBHOOK_URL = ""
