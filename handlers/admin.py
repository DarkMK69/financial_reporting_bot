from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.session import async_session_maker
from database.dao import EmployeeDAO, BranchDAO
from services.google_sheets import GoogleSheetsService
from keyboards.builder import get_main_menu, get_admin_employees_keyboard

router = Router()

class AddEmployeeStates(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_full_name = State()
    waiting_for_branch = State()

class AddBranchStates(StatesGroup):
    waiting_for_branch_name = State()

@router.message(F.text == "👥 Управление сотрудниками")
async def admin_employees_menu(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    await message.answer(
        "👥 Управление сотрудниками:",
        reply_markup=get_admin_employees_keyboard()
    )

@router.message(Command("add_employee"))
async def cmd_add_employee(message: Message, employee, state: FSMContext):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    await state.set_state(AddEmployeeStates.waiting_for_telegram_id)
    await message.answer("Введите Telegram ID нового сотрудника:")

@router.message(AddEmployeeStates.waiting_for_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
        await state.update_data(telegram_id=telegram_id)
        await state.set_state(AddEmployeeStates.waiting_for_full_name)
        await message.answer("Введите ФИО сотрудника:")
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число:")

@router.message(AddEmployeeStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❌ ФИО должно содержать минимум 2 символа:")
        return
    
    await state.update_data(full_name=message.text.strip())
    
    # Показываем список филиалов
    async with async_session_maker() as session:
        branch_dao = BranchDAO(session)
        branches = await branch_dao.get_all()
        
        if not branches:
            await message.answer("❌ Нет доступных филиалов. Сначала добавьте филиал.")
            await state.clear()
            return
        
        response = "Выберите филиал (введите номер):\n\n"
        for i, branch in enumerate(branches, 1):
            response += f"{i}. {branch.name}\n"
        
        await state.update_data(branches=branches)
        await state.set_state(AddEmployeeStates.waiting_for_branch)
        await message.answer(response)

@router.message(AddEmployeeStates.waiting_for_branch)
async def process_branch(message: Message, state: FSMContext):
    try:
        choice = int(message.text)
        data = await state.get_data()
        branches = data['branches']
        
        if 1 <= choice <= len(branches):
            selected_branch = branches[choice - 1]
            
            # Создаем сотрудника
            async with async_session_maker() as session:
                employee_dao = EmployeeDAO(session)
                
                # Проверяем, существует ли уже сотрудник с таким Telegram ID
                existing = await employee_dao.get_by_telegram_id(data['telegram_id'])
                if existing:
                    await message.answer("❌ Сотрудник с таким Telegram ID уже существует.")
                    await state.clear()
                    return
                
                # Создаем нового сотрудника
                new_employee = await employee_dao.create(
                    telegram_id=data['telegram_id'],
                    full_name=data['full_name'],
                    branch_id=selected_branch.id
                )
                
                # Синхронизируем с Google Sheets
                sheets_service = GoogleSheetsService()
                employees_list = await employee_dao.get_all()
                employees_data = []
                for emp in employees_list:
                    employees_data.append({
                        'id': emp.id,
                        'telegram_id': emp.telegram_id,
                        'full_name': emp.full_name,
                        'branch_name': emp.branch.name,
                        'is_active': emp.is_active,
                        'is_admin': emp.is_admin,
                        'created_at': emp.created_at
                    })
                await sheets_service.sync_employees(employees_data)
            
            await state.clear()
            await message.answer(
                f"✅ Сотрудник добавлен:\n"
                f"👤 {new_employee.full_name}\n"
                f"🆔 Telegram ID: {new_employee.telegram_id}\n"
                f"🏢 Филиал: {selected_branch.name}"
            )
        else:
            await message.answer("❌ Неверный номер филиала. Попробуйте снова:")
    except ValueError:
        await message.answer("❌ Введите номер филиала (число):")

@router.message(Command("remove_employee"))
async def cmd_remove_employee(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    async with async_session_maker() as session:
        employee_dao = EmployeeDAO(session)
        employees = await employee_dao.get_all()
        
        if not employees:
            await message.answer("❌ Нет сотрудников.")
            return
        
        response = "Список сотрудников (введите номер для деактивации):\n\n"
        for i, emp in enumerate(employees, 1):
            status = "✅" if emp.is_active else "❌"
            response += f"{i}. {status} {emp.full_name} (@{emp.telegram_id}) - {emp.branch.name}\n"
        
        await message.answer(response)

@router.message(Command("list_employees"))
async def cmd_list_employees(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    async with async_session_maker() as session:
        employee_dao = EmployeeDAO(session)
        employees = await employee_dao.get_all()
        
        if not employees:
            await message.answer("❌ Нет сотрудников.")
            return
        
        response = "👥 Список сотрудников:\n\n"
        for emp in employees:
            status = "✅ Активен" if emp.is_active else "❌ Неактивен"
            role = "👑 Админ" if emp.is_admin else "👤 Сотрудник"
            response += (
                f"👤 {emp.full_name}\n"
                f"   🆔 ID: {emp.telegram_id}\n"
                f"   🏢 Филиал: {emp.branch.name}\n"
                f"   {status} | {role}\n"
                f"   📅 Создан: {emp.created_at.strftime('%d.%m.%Y')}\n\n"
            )
        
        await message.answer(response)

@router.message(Command("add_branch"))
async def cmd_add_branch(message: Message, employee, state: FSMContext):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    await state.set_state(AddBranchStates.waiting_for_branch_name)
    await message.answer("Введите название нового филиала:")

@router.message(AddBranchStates.waiting_for_branch_name)
async def process_branch_name(message: Message, state: FSMContext):
    branch_name = message.text.strip()
    
    if len(branch_name) < 2:
        await message.answer("❌ Название должно содержать минимум 2 символа:")
        return
    
    async with async_session_maker() as session:
        branch_dao = BranchDAO(session)
        
        # Проверяем, существует ли уже филиал с таким названием
        existing = await branch_dao.get_by_name(branch_name)
        if existing:
            await message.answer("❌ Филиал с таким названием уже существует.")
            await state.clear()
            return
        
        # Создаем филиал
        new_branch = await branch_dao.create(branch_name)
        
        # Синхронизируем с Google Sheets
        #sheets_service = GoogleSheetsService()
        branches_list = await branch_dao.get_all()
        branches_data = []
        for branch in branches_list:
            branches_data.append({
                'id': branch.id,
                'name': branch.name,
                'created_at': branch.created_at
            })
        #await sheets_service.sync_branches(branches_data)
    
    await state.clear()
    await message.answer(f"✅ Филиал '{new_branch.name}' успешно добавлен!")

@router.message(Command("list_branches"))
async def cmd_list_branches(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    async with async_session_maker() as session:
        branch_dao = BranchDAO(session)
        branches = await branch_dao.get_all()
        
        if not branches:
            await message.answer("🏢 Филиалы не добавлены.")
            return
        
        response = "🏢 Список филиалов:\n\n"
        for branch in branches:
            active_employees = sum(1 for e in branch.employees if e.is_active)
            response += (
                f"📍 {branch.name}\n"
                f"   🆔 ID: {branch.id}\n"
                f"   👥 Сотрудников: {active_employees}/{len(branch.employees)}\n"
                f"   📅 Создан: {branch.created_at.strftime('%d.%m.%Y')}\n"
                f"   📊 Отчетов: {len(branch.reports)}\n\n"
            )
        
        await message.answer(response)