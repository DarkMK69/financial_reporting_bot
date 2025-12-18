import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from middlewares.auth import AuthMiddleware
from handlers import common, employee, owner, admin
from services.reminders import ReminderService
from utils.logger import logger
from database.base import Base
from database.session import engine

async def on_startup(bot: Bot):
    logger.info("Bot starting up...")
    
    # Создаем таблицы в БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Запускаем сервис напоминаний
    reminder_service = ReminderService(bot)
    asyncio.create_task(reminder_service.start_scheduler())
    
    logger.info("Bot started successfully")

async def on_shutdown(bot: Bot):
    logger.info("Bot shutting down...")

async def main():
    # Настройка бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Добавляем конфиг в данные
    dp["config"] = config
    
    # Подключаем middleware
    dp.update.outer_middleware(AuthMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(common.router)
    dp.include_router(employee.router)
    dp.include_router(owner.router)
    dp.include_router(admin.router)
    
    # Регистрируем обработчики startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")