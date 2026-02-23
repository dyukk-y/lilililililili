# Troubleshooting Guide

Common issues and solutions for AutoPost Bot.

## Installation Issues

### Python Not Found

**Error:** `python: command not found` or `python3: command not found`

**Solutions:**
1. Install Python from [python.org](https://www.python.org)
2. Verify installation: `python3 --version`
3. Use full path: `/usr/bin/python3` or `C:\Python311\python.exe`

### Permission Denied on macOS/Linux

**Error:** `Permission denied` when running `python bot.py`

**Solutions:**
```bash
# Make file executable
chmod +x bot.py

# Or run with python explicitly
python bot.py
```

### ModuleNotFoundError: No module named 'pytz'

**Error:** `ModuleNotFoundError: No module named 'pytz'`

**Solutions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or manually install
pip install pytz==2024.1
pip install APScheduler==3.10.4

# Check installation
python -c "import pytz; print(pytz.__version__)"
```

### Virtual Environment Issues

**Error:** `No module named 'xyz'` even after installing

**Solutions:**
```bash
# Check if venv is activated
which python
# Should show: /path/to/venv/bin/python

# If not activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Recreate venv if corrupted
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Pip Command Not Found

**Error:** `pip: command not found`

**Solutions:**
```bash
# Use python module
python -m pip install -r requirements.txt

# Or ensure pip is installed
python -m ensurepip --upgrade

# Check pip version
python -m pip --version
```

## Runtime Issues

### No Module Error on Startup

**Error:** `ModuleNotFoundError` when running bot

**Checklist:**
1. ✓ Virtual environment activated?
2. ✓ Dependencies installed? `pip install -r requirements.txt`
3. ✓ Correct Python version? `python --version` (3.7+)
4. ✓ In correct directory? `pwd` or `cd` to project folder

### Bot Starts but Posts Not Creating

**Symptoms:** Bot runs but no posts appear

**Check:**
```bash
# Check if posts.json exists
ls -la posts.json
# or on Windows: dir posts.json

# Check file permissions
test -w posts.json && echo "Writable" || echo "Not writable"

# Try creating test file
touch data/test.txt && rm data/test.txt

# Check disk space
df -h          # Linux/macOS
wmic logicaldisk get size,freespace  # Windows
```

**Solutions:**
1. Check directory permissions: `chmod 755 .`
2. Check disk space: `df -h`
3. Check file permissions: `chmod 644 posts.json`
4. Run as different user or with `sudo` (not recommended)

### "Address already in use" Error

**Error:** `OSError: [Errno 48] Address already in use`

**Cause:** Port already in use (if using API server)

**Solutions:**
```bash
# Find process using port
lsof -i :8000        # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>         # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port in config
```

## Timezone Issues

### Wrong Time in Posts

**Symptoms:** Times don't match Novosibirsk

**Check:**
```bash
# Test timezone conversion
python -c "from bot import AutoPostBot; bot = AutoPostBot(); print(bot.get_current_nsk_time())"

# Check system timezone
date
# or on Windows: Get-TimeZone

# List all available timezones
python -c "import pytz; print('\n'.join(pytz.all_timezones))"
```

**Solutions:**
1. Update system timezone settings
2. Change `nsk_tz` in bot.py:
   ```python
   self.nsk_tz = pytz.timezone('Your/Timezone')
   ```
3. Specify timezone explicitly:
   ```python
   bot.convert_to_nsk_time(time, from_tz="Europe/Moscow")
   ```

### Posts Not Scheduled at Correct Time

**Symptoms:** Scheduled posts appear at wrong time

**Check:**
```bash
# Verify scheduled jobs
bot = AutoPostBot()
for job in bot.get_jobs_info():
    print(job['next_run_time'])

# Check if time is in future
from datetime import datetime, timedelta
import pytz
future = datetime.now(pytz.UTC) + timedelta(hours=1)
print(future)
```

**Solutions:**
1. Ensure time is in the future
2. Verify timezone in `publish_post_at_time()`:
   ```python
   bot.publish_post_at_time(
       content="Test",
       publish_time=future,
       from_tz="UTC"   # Specify this
   )
   ```
3. Check scheduler: `bot.scheduler.running` should be True

## Data Issues

### Posts Not Saving

**Symptoms:** Posts published but not found in list

**Check:**
```bash
# Check post storage
cat posts.json
# or on Windows: type posts.json

# Verify post exists in memory
from bot import AutoPostBot
bot = AutoPostBot()
print(len(bot.posts))
print(bot.list_posts())
```

**Solutions:**
```bash
# Check file permissions
ls -la posts.json
chmod 644 posts.json

# Check disk space
df -h

# Verify JSON validity
python -c "import json; json.load(open('posts.json'))"
```

### Corrupted posts.json

**Symptoms:** "JSON decode error" or bot won't start

**Solutions:**
```bash
# Backup corrupted file
cp posts.json posts.json.bak

# Check file validity
python -c "import json; json.load(open('posts.json'))" 

# If invalid, try to recover
python -c "
import json
try:
    with open('posts.json') as f:
        data = json.load(f)
except Exception as e:
    print('File corrupted:', e)
    print('Recovering...')
    # Create empty storage
    open('posts.json', 'w').write('{}')
"

# Restart bot
python bot.py
```

### Lost Posts After Restart

**Cause:** posts.json deleted or in wrong location

**Solutions:**
```bash
# Check file location
find . -name "posts.json"

# Check storage_file parameter
bot = AutoPostBot(storage_file="posts.json")
# Make sure path is correct

# Restore from backup if available
cp posts.json.bak posts.json
```

## Scheduler Issues

### Jobs Not Executing

**Symptoms:** Scheduled tasks don't run

**Check:**
```bash
# Verify scheduler is running
from bot import AutoPostBot
bot = AutoPostBot()
print(bot.scheduler.running)

# Check scheduled jobs
for job in bot.scheduler.get_jobs():
    print(f"Job: {job.id}, Next run: {job.next_run_time}")

# Check logs
tail -f autopost_bot.log
```

**Solutions:**
1. Ensure bot is still running:
   ```bash
   ps aux | grep bot.py
   # or on Windows: tasklist | findstr bot.py
   ```
2. Increase scheduler check interval (in bot.py)
3. Verify system time is correct: `date`
4. Check for blocking code in callbacks

### Too Many Scheduled Jobs

**Symptoms:** Memory usage increasing, bot slowing down

**Check:**
```bash
# Count jobs
from bot import AutoPostBot
bot = AutoPostBot()
print(f"Total jobs: {len(bot.scheduler.get_jobs())}")
print(f"Total posts: {len(bot.posts)}")
```

**Solutions:**
```bash
# Clean up old posts
from bot import AutoPostBot
bot = AutoPostBot()

# Delete posts older than 30 days
from datetime import datetime, timedelta, timezone
cutoff = datetime.now(timezone.utc) - timedelta(days=30)

for post_id, post in list(bot.posts.items()):
    if 'published_at' in post:
        # Delete old posts
        bot.delete_post(post_id)
```

## Docker Issues

### Docker Image Build Fails

**Error:** `ERROR: Service 'autopost-bot' failed to build`

**Solutions:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t autopost-bot .

# Check Docker log
docker build -t autopost-bot . 2>&1 | tail -20
```

### Container Exits Immediately

**Error:** Container starts then stops

**Check:**
```bash
# View logs
docker logs <container_id>

# Run interactively
docker run -it autopost-bot

# Check health
docker ps -a  # Check status
docker logs <container_id> --tail 20
```

**Solutions:**
```bash
# Run with entrypoint override
docker run -it --entrypoint bash autopost-bot

# Check dependencies in container
docker run --rm autopost-bot python -c "from bot import AutoPostBot; print('OK')"
```

### Volume Mount Issues

**Error:** `Permission denied` for /app/data

**Solutions:**
```bash
# On Linux/macOS
sudo chown -R $(id -u):$(id -g) ./data

# On Windows, disable SELinux or use different volume
docker-compose down
docker-compose up -d

# Check volume
docker volume ls
docker volume inspect <volume_name>
```

## Performance Issues

### Memory Usage Growing

**Symptoms:** Bot using more and more memory

**Check:**
```python
import sys
print(f"Posts in memory: {len(bot.posts)}")
print(f"Scheduled jobs: {len(bot.scheduler.get_jobs())}")

# Get object sizes
import sys
for post_id, post in bot.posts.items():
    size = sys.getsizeof(post)
    if size > 1000:  # > 1KB
        print(f"Post {post_id}: {size} bytes")
```

**Solutions:**
1. Archive old posts periodically
2. Implement post cleanup (older than N days)
3. Use database instead of JSON for large datasets
4. Monitor with: `top` or `htop` (Linux/macOS)

### Bot Slow/Unresponsive

**Symptoms:** Delays in executing commands

**Check:**
```bash
# Check CPU usage
top -p <PID>
# or on Windows: tasklist

# Check for blocking operations
# Review logs for slow operations
```

**Solutions:**
1. Reduce logging level: `LOG_LEVEL=WARNING`
2. Archive old posts
3. Reduce scheduler poll interval
4. Use async operations for I/O

## Integration Issues

### Telegram Integration Not Working

**Error:** `No module named 'telegram'`

**Solutions:**
```bash
pip install python-telegram-bot

# Test import
python -c "from telegram import Bot; print('OK')"

# Check token
python -c "
from telegram import Bot
bot = Bot(token='YOUR_TOKEN')
updates = bot.get_updates()
print(updates)
"
```

### Platform-Specific Credentials Issues

**Symptoms:** "Invalid credentials" or "Unauthorized"

**Solutions:**
1. Regenerate credentials/tokens
2. Check token expiration
3. Verify permissions for tokens
4. Use environment variables:
   ```python
   import os
   token = os.getenv('TELEGRAM_TOKEN')
   ```

## Logging

### Not Seeing Logs

**Check log level:**
```bash
# Change in bot.py
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
python bot.py
```

### Log File Not Created

**Solutions:**
```bash
# Create log file manually
touch autopost_bot.log

# Ensure write permissions
chmod 644 autopost_bot.log

# Add logging file handler in code
handler = logging.FileHandler('autopost_bot.log')
logger.addHandler(handler)
```

## Getting More Help

### Debug Information Collection

Collect this info when reporting issues:
```bash
# System info
python --version
uname -a  # or systeminfo on Windows
df -h     # Disk space
free -h   # Memory (Linux)

# Bot info
python -c "from bot import AutoPostBot; bot = AutoPostBot(); print(len(bot.posts))"

# Recent logs
tail -100 autopost_bot.log

# Environment
env | grep -E "(PYTHON|PATH)"
pip list | grep -E "(pytz|APScheduler)"
```

### Report Issues

When reporting issues, include:
1. Error messages (full stack trace)
2. Steps to reproduce
3. Expected vs actual behavior
4. Debug info from above
5. Python version and OS
6. Complete logs if possible

### Useful Links

- [Python Docs](https://docs.python.org/3/)
- [pytz Documentation](https://pypi.org/project/pytz/)
- [APScheduler Docs](https://apscheduler.readthedocs.io/)
- [GitHub Issues](https://github.com/dyukk-y/lilililililili/issues)

---

**Still stuck?** Open an issue on [GitHub](https://github.com/dyukk-y/lililililitili/issues) with all details!
