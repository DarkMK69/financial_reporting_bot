from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Dict, Any, Callable, Awaitable
from database.session import async_session_maker
from database.dao import EmployeeDAO

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user = data.get("event_from_user")
        
        if event_user:
            async with async_session_maker() as session:
                employee_dao = EmployeeDAO(session)
                employee = await employee_dao.get_by_telegram_id(event_user.id)
                
                if employee and employee.is_active:
                    data["employee"] = employee
                    return await handler(event, data)
                else:
                    # Проверяем, является ли пользователь админом из конфига
                    if event_user.id in data.get("config").ADMIN_IDS:
                        # Создаем временного админа
                        from database.models import Employee
                        admin_employee = Employee(
                            telegram_id=event_user.id,
                            full_name=f"Admin_{event_user.id}",
                            is_admin=True,
                            branch_id=1  # Временный филиал для админов
                        )
                        data["employee"] = admin_employee
                        return await handler(event, data)
        
        # Если нет доступа
        if hasattr(event, "message") and event.message:
            await event.message.answer("❌ У вас нет доступа к этому боту.")
        return None