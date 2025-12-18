from datetime import datetime
import pytz
from config import config

def get_moscow_time() -> datetime:
    """Получить текущее время в Москве"""
    tz = pytz.timezone(config.TIMEZONE)
    return datetime.now(tz)

def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Форматирование даты и времени"""
    return dt.strftime(format_str)

def format_currency(amount: float) -> str:
    """Форматирование денежных сумм"""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")