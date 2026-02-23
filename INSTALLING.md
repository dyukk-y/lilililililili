# Installation Guide

Complete step-by-step guide to install and run AutoPost Bot.

## Table of Contents

1. [Quick Install](#quick-install)
2. [System Requirements](#system-requirements)
3. [Standard Installation](#standard-installation)
4. [Docker Installation](#docker-installation)
5. [From Source](#from-source)
6. [Platform-Specific Instructions](#platform-specific-instructions)
7. [Troubleshooting](#troubleshooting)

## Quick Install

```bash
# 1. Clone repository
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the bot
python bot.py
```

## System Requirements

- **Python:** 3.7 or higher
- **OS:** Linux, macOS, Windows
- **RAM:** 256 MB minimum, 512 MB recommended
- **Disk:** 100 MB for installation

### Check Python Version

```bash
python --version
# or
python3 --version
```

If you don't have Python 3.8+, download from [python.org](https://www.python.org/downloads/)

## Standard Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytz==2024.1` - Timezone support
- `APScheduler==3.10.4` - Background task scheduling

### 4. Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
# or
code .env
```

### 5. Run the Bot

```bash
# Basic run
python bot.py

# Or with virtual environment active
source venv/bin/activate  # Linux/macOS
python bot.py
```

## Docker Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 1.29+ (optional)

### Quick Docker Run

```bash
# Build image
docker build -t autopost-bot .

# Run container
docker run -d \
  --name autopost \
  -v $(pwd)/data:/app/data \
  autopost-bot
```

### With Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Start bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop bot
docker-compose down
```

### Docker Commands

```bash
# Build image
docker build -t autopost-bot .

# Run in foreground
docker run -it -v $(pwd)/data:/app/data autopost-bot

# Run in background
docker run -d -v $(pwd)/data:/app/data autopost-bot

# See logs
docker logs -f <container_id>

# Stop container
docker stop <container_id>

# Remove container
docker rm <container_id>
```

## From Source

### Clone and Setup

```bash
# Clone
git clone https://github.com/dyukk-y/lililililibli.git
cd lilililililili

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements.txt
```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

```bash
# Update package manager
sudo apt-get update

# Install Python and pip
sudo apt-get install python3 python3-pip python3-venv

# Clone and setup
git clone https://github.com/dyukk-y/lililililitili.git
cd lilililililili

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python bot.py
```

### macOS

```bash
# Using Homebrew (if installed)
brew install python@3.11

# Or download from python.org
# Then:

git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install and run
pip install -r requirements.txt
python bot.py
```

### Windows

```bash
# Download Python from python.org
# During installation, CHECK "Add Python to PATH"

# Then in Command Prompt:
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili

# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Install and run
pip install -r requirements.txt
python bot.py
```

### Raspberry Pi / ARM

```bash
# Install Python
sudo apt-get install python3 python3-pip python3-venv

# Clone
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install (may take longer)
pip install -r requirements.txt

# Run
python bot.py
```

## Installation Methods

### Method 1: pip (Simplest)

```bash
# Will be available after publishing to PyPI
pip install autopost-bot
```

### Method 2: From GitHub

```bash
pip install git+https://github.com/dyukk-y/lililililitili.git
```

### Method 3: From Source

```bash
git clone https://github.com/dyukk-y/lilililililili.git
cd lilililililili
pip install -e .
```

### Method 4: Docker

```bash
docker pull dyukk-y/autopost-bot
docker run -d -v $(pwd)/data:/app/data dyukk-y/autopost-bot
```

## Verify Installation

```bash
# Test import
python -c "from bot import AutoPostBot; print('OK')"

# Run examples
python examples.py

# Interactive quickstart
python quickstart.py
```

## Troubleshooting

### "python: command not found"

**Solution:** You need to install Python or use `python3`

```bash
python3 --version
python3 bot.py
```

### "ModuleNotFoundError: No module named 'pytz'"

**Solution:** Install dependencies

```bash
pip install -r requirements.txt
```

### "Permission denied" on Linux/macOS

**Solution:** Make files executable

```bash
chmod +x bot.py
./bot.py
```

### Virtual Environment Issues

```bash
# Remove and recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Docker Build Issues

```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t autopost-bot .
```

### Posts Not Saving

**Check:**
1. File permissions: `ls -la posts.json`
2. Disk space: `df -h`
3. Directory writable: `touch data/test.txt`

### Timezone Issues

```python
# Check available timezones
import pytz
print(pytz.all_timezones)

# Verify current setting in bot.py
python -c "from bot import AutoPostBot; bot = AutoPostBot(); print(bot.get_current_nsk_time())"
```

## Uninstall

```bash
# Remove virtual environment
rm -rf venv

# Remove cloned directory
rm -rf lilililililili

# Or pip uninstall (if installed via pip)
pip uninstall autopost-bot
```

## Post-Installation

### 1. Configure Bot

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (Telegram, VK, etc.)
nano .env
```

### 2. Test Bot

```bash
# Run examples
python examples.py

# Or interactive test
python quickstart.py
```

### 3. Integrate with Platforms

See platform configuration in:
- `config_example.py` - Configuration templates
- `telegram_bot.py` - Telegram integration
- `platform_integrations.py` - Other platforms

### 4. Set Up Logging

Create `logging_config.py` or modify in `bot.py` for custom logging.

### 5. Database (Optional)

For production, configure database in `.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost/autopost_db
```

## Next Steps

1. Read [README.md](README.md) for usage examples
2. Check [README_RU.md](README_RU.md) for Russian documentation
3. Review `examples.py` for practical examples
4. Read `CHANGELOG.md` for version history

## Getting Help

If you have issues:

1. Check [Troubleshooting](#troubleshooting) above
2. Review logs: `cat autopost_bot.log`
3. Check `posts.json` file exists
4. Open an issue on [GitHub](https://github.com/dyukk-y/lilililililili/issues)

## Security Notes

- Never commit `.env` or `posts.json` files
- Use environment variables for sensitive data
- For production, use database instead of JSON
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Use HTTPS for API endpoints

---

**Happy posting!** 🚀
