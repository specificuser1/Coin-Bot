import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '!'
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
PORTAL_URL = os.getenv('PORTAL_URL', 'http://localhost:8000')

# Coin Settings
COIN_PER_MINUTE = 1.0
SCREEN_SHARE_BONUS = 0.5
MIN_ACCOUNT_AGE_DAYS = 28
DAILY_KEY_LIMIT = 2
KEY_COST = 90

# Database
COINS_FILE = 'data/coins.json'
KEYS_DIR = 'keys'
