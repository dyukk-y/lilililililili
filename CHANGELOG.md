# Changelog

All notable changes to AutoPost Bot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-23

### Added
- Initial release of AutoPost Bot
- Core `AutoPostBot` class with full functionality
- Post publishing with immediate publishing
- Post scheduling for specific times
- Automatic post deletion after set time interval
- Timezone conversion for any timezone to Novosibirsk (NSK)
- Background scheduler using APScheduler
- JSON-based persistent storage
- Platform integrations:
  - Telegram (telegram_bot.py)
  - VK/ВКонтакте (platform_integrations.py)
  - Instagram (platform_integrations.py)
  - Twitter/X (platform_integrations.py)
  - Reddit (platform_integrations.py)
  - WordPress (platform_integrations.py)
  - Multi-platform support
- Comprehensive documentation:
  - English README.md
  - Russian README_RU.md
  - API documentation
  - Usage examples
- Interactive quickstart guide (quickstart.py)
- 7 complete usage examples (examples.py)
- Configuration template (config_example.py)
- Docker and Docker Compose support
- Setup.py for pip installation
- MIT License
- .gitignore for safe version control
- Environment variables support (.env.example)

### Features
- ✅ Publish posts instantly or on schedule
- ✅ Auto-delete posts after specified hours
- ✅ Convert any timezone to NSK automatically
- ✅ Reliable background task scheduling
- ✅ Persistent JSON storage
- ✅ Comprehensive logging
- ✅ Multi-platform support
- ✅ Production-ready code
- ✅ Easy to extend and customize

### Documentation
- Full API documentation in README.md
- Russian documentation in README_RU.md
- Usage examples in examples.py
- Quickstart guide in quickstart.py
- Integration examples in platform_integrations.py
- Configuration template in config_example.py

### Technical Details
- Python 3.7+
- APScheduler 3.10.4
- pytz 2024.1
- Async-compatible architecture
- Extensible class-based design
- Error handling and logging throughout

## [Unreleased]

### Planned for Future Releases
- Database integration (PostgreSQL, MongoDB)
- REST API for managing posts
- Web dashboard UI
- Webhook support
- More platform integrations
- Batch operations
- Advanced scheduling (cron expressions)
- Post templates
- Media attachment support
- Analytics and statistics
- Rate limiting
- Priority queue for posts
- Post versioning
- Duplicate detection
- A/B testing support
