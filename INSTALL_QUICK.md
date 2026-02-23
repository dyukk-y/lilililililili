# Quick Installation Guide

## ⚡ TL;DR - 2 Minutes Setup

### Linux/macOS
```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Windows
```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

### Docker
```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
docker-compose up -d
```

## ✅ Installation Checklist

- [ ] Python 3.7+ installed
- [ ] Git installed
- [ ] Cloned repository
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Bot runs without errors

## 🧪 Verify Installation

```bash
# Test that everything works
python -c "from bot import AutoPostBot; bot = AutoPostBot(); print('✓ OK')"

# Run examples
python examples.py

# Run interactive quickstart
python quickstart.py
```

## 📖 Next Steps

1. **Read documentation**: See [README.md](README.md)
2. **View examples**: Run `python examples.py`
3. **Try it out**: Run `python quickstart.py`
4. **Integrate**: See `telegram_bot.py` or `platform_integrations.py`
5. **Deploy**: Use Docker or systemd service

## 🚀 Quick Usage

```python
from bot import AutoPostBot

# Create bot
bot = AutoPostBot()

# Publish post
bot.publish_post("Hello World!", delete_after_hours=2)

# Check current time
print(bot.get_current_nsk_time())

# List posts
for post in bot.list_posts():
    print(f"Post #{post['id']}: {post['content']}")
```

## ❓ Problems?

1. **"ModuleNotFoundError"** → Install dependencies: `pip install -r requirements.txt`
2. **"Command not found"** → Use full path or check if Python is in PATH
3. **"Permission denied"** → Activate venv or use `python bot.py`
4. **Docker issues** → Install Docker Desktop

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 📚 Full Documentation

- **[INSTALLING.md](INSTALLING.md)** - Complete installation for all platforms
- **[README.md](README.md)** - Full documentation and API
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 30+ common issues and solutions

---

**Ready to go!** 🎉 Run `python quickstart.py` to start.
