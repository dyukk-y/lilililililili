# AutoPost Bot 🤖

An advanced Python bot for automatic content publishing with time zone conversion, scheduling, and auto-deletion features. **All operations work in Novosibirsk timezone (NSK).**

[Russian Documentation / Русская документация](README_RU.md)

## ✨ Key Features

- 📝 **Publish posts** - Create posts instantly
- ⏰ **Schedule posts** - Publish at specific times
- 🗑️ **Auto-delete** - Posts delete automatically after set time
- 🌍 **Smart timezone conversion** - Convert any timezone to NSK automatically
- 💾 **Persistent storage** - Posts saved in JSON (easy to migrate to DB)
- 🔄 **Background scheduler** - Reliable task execution using APScheduler
- 🔌 **Platform integrations** - Ready for Telegram, VK, Instagram, Twitter, etc.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili

# Install dependencies
pip install -r requirements.txt
```

**👉 New to the project?** See [INSTALL_QUICK.md](INSTALL_QUICK.md) for 2-minute setup

### Basic Usage

```python
from bot import AutoPostBot

# Initialize bot
bot = AutoPostBot()

# Publish now with auto-delete in 2 hours
post_id = bot.publish_post(
    content="Hello World!",
    delete_after_hours=2
)

# Schedule for specific time
from datetime import datetime, timedelta
import pytz

future = datetime.now(pytz.UTC) + timedelta(hours=1)
bot.publish_post_at_time(
    content="This will publish in 1 hour",
    publish_time=future,
    from_tz="UTC"
)

# Convert any timezone to NSK
moscow_time = datetime(2026, 2, 23, 15, 30)
nsk_time = bot.convert_to_nsk_time(moscow_time, "Europe/Moscow")

# Get current NSK time
now = bot.get_current_nsk_time()
```

## 📚 Documentation

### Main Bot Class

```python
bot = AutoPostBot(storage_file="posts.json")
```

**Key Methods:**

- `publish_post(content, delete_after_hours=None)` - Publish now
- `publish_post_at_time(content, publish_time, from_tz=None, delete_after_hours=None)` - Schedule
- `delete_post(post_id)` - Delete post
- `convert_to_nsk_time(dt, from_tz=None)` - Convert timezone to NSK
- `get_current_nsk_time()` - Get current NSK time
- `get_post(post_id)` - Get post info
- `list_posts(status=None)` - List posts
- `get_jobs_info()` - Get scheduled jobs
- `shutdown()` - Stop scheduler

### Timezone Support

Common timezones you can use:

```
Europe/Moscow      # Moscow (UTC+3)
Asia/Novosibirsk   # Novosibirsk (UTC+7) - Default
Asia/Yekaterinburg # Yekaterinburg (UTC+5)
Europe/London      # London (UTC+0/+1)
Asia/Tokyo         # Tokyo (UTC+9)
America/New_York   # New York (UTC-5/-4)
America/Los_Angeles # Los Angeles (UTC-8/-7)
```

Full timezone list: [IANA TZ Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## 📁 Project Structure

```
.
├── bot.py                      # Main AutoPostBot class
├── examples.py                 # Usage examples
├── quickstart.py               # Interactive quick start
├── telegram_bot.py             # Telegram integration
├── platform_integrations.py    # Multi-platform support
├── requirements.txt            # Dependencies
├── README.md                   # This file
├── README_RU.md               # Russian documentation
├── .gitignore                 # Git ignore rules
└── posts.json                 # Auto-generated storage
```

## 🔌 Integrations

Bot includes ready-to-use integrations for:

- **Telegram** - Send to Telegram channels/groups
- **VK (ВКонтакте)** - Post to VK groups
- **Instagram** - Publish photos with captions
- **Twitter/X** - Post tweets
- **Reddit** - Submit to subreddits
- **WordPress** - Publish blog posts

See `platform_integrations.py` for examples.

## 📖 Documentation

- **[INSTALLING.md](INSTALLING.md)** - Complete installation guide for all platforms
- **[README_RU.md](README_RU.md)** - Russian documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions for common issues
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

## 📖 Quick Examples

### Interactive Quick Start
```bash
python quickstart.py
```

### View All Examples
```bash
python examples.py
```

### Run Basic Bot
```bash
python bot.py
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Format code
black bot.py

# Check code style
flake8 bot.py
```

### Using Makefile (Linux/macOS)

```bash
make help              # Show all commands
make install-dev      # Install dev tools
make test             # Run tests
make lint             # Check code style
make format           # Format code
make docker-build     # Build Docker image
```

## 🛠️ Configuration

### Change Default Timezone

Edit `bot.py` line 35:
```python
self.nsk_tz = pytz.timezone('Asia/Novosibirsk')  # Change to any timezone
```

### Use Custom Storage File

```python
bot = AutoPostBot(storage_file="my_posts.json")
```

## 📊 Data Format

Posts are stored in JSON:

```json
{
  "1": {
    "id": "1",
    "content": "Post content",
    "published_at": "2026-02-23T15:30:00+07:00",
    "status": "published"
  },
  "2": {
    "id": "2",
    "content": "Scheduled post",
    "scheduled_for": "2026-02-23T16:00:00+07:00",
    "status": "scheduled",
    "delete_after_hours": 3
  }
}
```

## 🔒 Security & Production

For production use:

- ✅ Use database instead of JSON (PostgreSQL, MongoDB)
- ✅ Add authentication/authorization
- ✅ Validate all input data
- ✅ Use HTTPS for APIs
- ✅ Store sensitive data in environment variables
- ✅ Implement rate limiting
- ✅ Add error handling and monitoring

## 🤝 Extending

### Custom Platform Integration

```python
from bot import AutoPostBot

class MyBot(AutoPostBot):
    def publish_post(self, content, **kwargs):
        post_id = super().publish_post(content, **kwargs)
        # Custom logic here
        self.my_api_call(content)
        return post_id
```

### Database Integration

```python
class DatabaseBot(AutoPostBot):
    def _load_posts(self):
        self.posts = self.db.load_posts()
    
    def _save_posts(self):
        self.db.save_posts(self.posts)
```

## 📝 Logging

All operations are logged:

```
INFO   - Normal operations (publish, delete)
WARNING - Warnings (post not found)
ERROR   - Errors and exceptions
```

## 🐛 Troubleshooting

**Bot doesn't start?**
1. Install dependencies: `pip install -r requirements.txt`
2. Check Python version (3.7+)
3. Enable file permissions for posts.json

**Posts not being created?**
- Check logs for errors
- Verify file permissions
- Ensure timezone is valid

**Scheduling not working?**
- Verify time is in future
- Check system timezone settings
- See `get_jobs_info()` for scheduled tasks

## 📞 Support

For issues:
1. Check logs in console
2. Verify dependencies: `pip install -r requirements.txt`
3. Review examples in `examples.py`
4. Read full documentation in `README_RU.md`

## 📄 License

Free to use and modify.

## 🎉 Version

**v1.0.0** - Release 2026-02-23

---

**Default Timezone:** Asia/Novosibirsk (UTC+7)  
**Main Language:** Python 3.7+
