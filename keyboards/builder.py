from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup

def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    if role == "employee":
        builder.add(KeyboardButton(text="📊 Заполнить отчет за сегодня"))
        builder.add(KeyboardButton(text="✏️ Исправить отчет за сегодня"))
        builder.add(KeyboardButton(text="📋 Мои последние отчеты"))
    elif role in ["admin", "owner"]:
        builder.add(KeyboardButton(text="📊 Отчет за сегодня"))
        builder.add(KeyboardButton(text="📅 Отчет за дату"))
        builder.add(KeyboardButton(text="🏢 Филиалы"))
        builder.add(KeyboardButton(text="📋 Последние отчеты"))
        
        if role == "admin":
            builder.add(KeyboardButton(text="👥 Управление сотрудниками"))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="confirm_send")
    builder.button(text="✏️ Изменить", callback_data="confirm_edit")
    builder.button(text="🔄 Заполнить заново", callback_data="confirm_restart")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_admin_employees_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить сотрудника", callback_data="admin_add_employee")
    builder.button(text="➖ Удалить сотрудника", callback_data="admin_remove_employee")
    builder.button(text="📋 Список сотрудников", callback_data="admin_list_employees")
    builder.button(text="➕ Добавить филиал", callback_data="admin_add_branch")
    builder.button(text="🏢 Список филиалов", callback_data="admin_list_branches")
    builder.adjust(2)
    return builder.as_markup()