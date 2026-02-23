# Configuration examples for integrations
# Copy this file to config.py and fill in your credentials

# ==============================================
# TELEGRAM CONFIGURATION
# ==============================================
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_IDS = [123456789]  # Your chat IDs

# How to get:
# 1. Create bot with @BotFather in Telegram
# 2. Get token from BotFather
# 3. Get your chat_id from @userinfobot in Telegram


# ==============================================
# VK CONFIGURATION
# ==============================================
VK_ACCESS_TOKEN = "YOUR_VK_TOKEN_HERE"
VK_GROUP_ID = 12345678  # Your VK group ID

# How to get:
# 1. Create community in VK
# 2. Get access token from VK Admin panel
# 3. Get group ID from community settings


# ==============================================
# INSTAGRAM CONFIGURATION
# ==============================================
INSTAGRAM_USERNAME = "your_instagram_username"
INSTAGRAM_PASSWORD = "your_instagram_password"

# Warning: Keep credentials secure!


# ==============================================
# TWITTER CONFIGURATION
# ==============================================
TWITTER_API_KEY = "YOUR_API_KEY_HERE"
TWITTER_API_SECRET = "YOUR_API_SECRET_HERE"
TWITTER_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"
TWITTER_ACCESS_TOKEN_SECRET = "YOUR_ACCESS_TOKEN_SECRET_HERE"

# How to get:
# 1. Go to https://developer.twitter.com
# 2. Create app and get credentials
# 3. Enable OAuth 1.0a in app settings


# ==============================================
# REDDIT CONFIGURATION
# ==============================================
REDDIT_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
REDDIT_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
REDDIT_USERNAME = "your_reddit_username"
REDDIT_PASSWORD = "your_reddit_password"
REDDIT_SUBREDDIT = "test"  # Which subreddit to post to

# How to get:
# 1. Go to https://www.reddit.com/prefs/apps
# 2. Create application
# 3. Get client ID and secret


# ==============================================
# WORDPRESS CONFIGURATION
# ==============================================
WORDPRESS_URL = "https://example.com"
WORDPRESS_USERNAME = "admin"
WORDPRESS_PASSWORD = "your_password_here"

# How to get:
# 1. Install REST API on WordPress
# 2. Create user with post capability
# 3. Get API credentials


# ==============================================
# DATABASE CONFIGURATION (for production)
# ==============================================
DATABASE_URL = "postgresql://user:password@localhost/autopost_db"
# or
MONGODB_URL = "mongodb://user:password@localhost/autopost_db"

# Recommended for production instead of JSON storage


# ==============================================
# ENVIRONMENT VARIABLES
# ==============================================
# Create .env file with:
# TELEGRAM_TOKEN=your_token
# VK_TOKEN=your_token
# DATABASE_URL=your_db_url
# DEBUG=False

# Then load with:
# from dotenv import load_dotenv
# import os
# load_dotenv()
# API_KEY = os.getenv('TELEGRAM_TOKEN')
