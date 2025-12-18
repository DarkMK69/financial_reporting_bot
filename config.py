import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///finance.db")
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    REPORT_SHEET_ID = os.getenv("REPORT_SHEET_ID")
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    
config = Config()