from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards.builder import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, employee):
    role = "admin" if employee.is_admin else "employee"
    await message.answer(
        f"👋 Добро пожаловать, {employee.full_name}!\n"
        f"Роль: {'Администратор' if employee.is_admin else 'Сотрудник филиала'}",
        reply_markup=get_main_menu(role)
    )