import asyncio
from datetime import datetime, time
import pytz
from aiogram import Bot
from database.session import async_session_maker
from database.dao import ReportDAO, EmployeeDAO
from config import config

class ReminderService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.timezone = pytz.timezone(config.TIMEZONE)
    
    async def send_daily_reminders(self):
        """Отправка напоминаний сотрудникам в 19:00"""
        async with async_session_maker() as session:
            employee_dao = EmployeeDAO(session)
            report_dao = ReportDAO(session)
            
            # Получаем активных сотрудников
            employees = await employee_dao.get_active_employees()
            
            for employee in employees:
                # Проверяем, сдал ли сотрудник отчет сегодня
                today_report = await report_dao.get_employee_today_report(employee.id)
                
                if not today_report:
                    # Отправляем напоминание
                    try:
                        await self.bot.send_message(
                            chat_id=employee.telegram_id,
                            text="⏰ Напоминание: не забудьте сдать ежедневный финансовый отчет!"
                        )
                    except Exception as e:
                        print(f"Error sending reminder to {employee.telegram_id}: {e}")
    
    async def send_owner_notification(self):
        """Отправка уведомления владельцу в 20:00"""
        # Здесь можно добавить логику отправки сводки владельцу
        pass
    
    async def start_scheduler(self):
        """Запуск планировщика напоминаний"""
        while True:
            now = datetime.now(self.timezone)
            
            # Проверяем, 19:00 ли сейчас
            if now.hour == 19 and now.minute == 0:
                await self.send_daily_reminders()
                await asyncio.sleep(60)  # Ждем минуту, чтобы не запускать несколько раз
            
            # Проверяем, 20:00 ли сейчас
            elif now.hour == 20 and now.minute == 0:
                await self.send_owner_notification()
                await asyncio.sleep(60)
            
            await asyncio.sleep(30)  # Проверяем каждые 30 секунд