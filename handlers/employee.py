from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import pytz
from database.session import async_session_maker
from database.dao import ReportDAO, EmployeeDAO
from states.report import ReportStates
from services.validators import ReportValidator
from services.google_sheets import GoogleSheetsService
from keyboards.builder import get_main_menu, get_cancel_keyboard, get_confirmation_keyboard

router = Router()

@router.message(F.text == "📊 Заполнить отчет за сегодня")
async def start_report(message: Message, employee, state: FSMContext):
    async with async_session_maker() as session:
        report_dao = ReportDAO(session)
        existing_report = await report_dao.get_employee_today_report(employee.id)
        
        if existing_report:
            await message.answer(
                f"📝 У вас уже есть отчет за сегодня (версия {existing_report.version}).\n"
                "Хотите создать новую версию?",
                reply_markup=get_main_menu("employee")
            )
            return
    
    await state.set_state(ReportStates.waiting_for_total_income)
    await message.answer(
        "Введите общий приход за день (сумма):",
        reply_markup=get_cancel_keyboard()
    )

@router.message(ReportStates.waiting_for_total_income)
async def process_total_income(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Заполнение отчета отменено.", reply_markup=get_main_menu("employee"))
        return
    
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(total_income=amount)
    await state.set_state(ReportStates.waiting_for_cash)
    await message.answer("Введите сумму наличными:")

@router.message(ReportStates.waiting_for_cash)
async def process_cash(message: Message, state: FSMContext):
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(cash=amount)
    await state.set_state(ReportStates.waiting_for_cashless)
    await message.answer("Введите сумму безналичными:")

@router.message(ReportStates.waiting_for_cashless)
async def process_cashless(message: Message, state: FSMContext):
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(cashless=amount)
    await state.set_state(ReportStates.waiting_for_cash_balance)
    await message.answer("Введите остаток в кассе:")

@router.message(ReportStates.waiting_for_cash_balance)
async def process_cash_balance(message: Message, state: FSMContext):
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(cash_balance=amount)
    await state.set_state(ReportStates.waiting_for_clients_count)
    await message.answer("Введите количество клиентов:")

@router.message(ReportStates.waiting_for_clients_count)
async def process_clients_count(message: Message, state: FSMContext):
    is_valid, count = ReportValidator.validate_clients_count(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат. Введите целое неотрицательное число:")
        return
    
    await state.update_data(clients_count=count)
    await state.set_state(ReportStates.waiting_for_cash_to_suppliers)
    await message.answer("Введите наличные поставщикам:")

@router.message(ReportStates.waiting_for_cash_to_suppliers)
async def process_cash_to_suppliers(message: Message, state: FSMContext):
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(cash_to_suppliers=amount)
    await state.set_state(ReportStates.waiting_for_cashless_to_suppliers)
    await message.answer("Введите безнал поставщикам:")

@router.message(ReportStates.waiting_for_cashless_to_suppliers)
async def process_cashless_to_suppliers(message: Message, state: FSMContext):
    is_valid, amount = ReportValidator.validate_amount(message.text)
    if not is_valid:
        await message.answer("❌ Неверный формат суммы. Введите положительное число:")
        return
    
    await state.update_data(cashless_to_suppliers=amount)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Проверяем валидацию
    is_valid, error_message = ReportValidator.validate_all_fields(data)
    if not is_valid:
        await message.answer(f"❌ Ошибка валидации: {error_message}\nНачните заново.")
        await state.clear()
        return
    
    # Показываем сводку
    summary = (
        f"📊 Сводка отчета:\n\n"
        f"💰 Общий приход: {data['total_income']}\n"
        f"💵 Наличные: {data['cash']}\n"
        f"💳 Безналичные: {data['cashless']}\n"
        f"🏦 Остаток в кассе: {data['cash_balance']}\n"
        f"👥 Клиентов: {data['clients_count']}\n"
        f"📤 Наличные поставщикам: {data['cash_to_suppliers']}\n"
        f"📥 Безнал поставщикам: {data['cashless_to_suppliers']}\n\n"
        f"Проверьте данные и подтвердите отправку."
    )
    
    await state.set_state(ReportStates.summary)
    await message.answer(summary, reply_markup=get_confirmation_keyboard())

@router.callback_query(ReportStates.summary, F.data == "confirm_send")
async def confirm_send(callback: CallbackQuery, employee, state: FSMContext):
    data = await state.get_data()
    
    async with async_session_maker() as session:
        report_dao = ReportDAO(session)
        employee_dao = EmployeeDAO(session)
        
        # Получаем текущего сотрудника с branch
        current_employee = await employee_dao.get_by_telegram_id(employee.telegram_id)
        
        # Определяем версию
        existing_report = await report_dao.get_employee_today_report(current_employee.id)
        version = existing_report.version + 1 if existing_report else 1
        
        # Создаем отчет
        report = await report_dao.create(
            report_date=datetime.now(pytz.timezone('Europe/Moscow')),
            total_income=data['total_income'],
            cash=data['cash'],
            cashless=data['cashless'],
            cash_balance=data['cash_balance'],
            clients_count=data['clients_count'],
            cash_to_suppliers=data['cash_to_suppliers'],
            cashless_to_suppliers=data['cashless_to_suppliers'],
            version=version,
            employee_id=current_employee.id,
            branch_id=current_employee.branch_id
        )
        
        # Синхронизируем с Google Sheets
        sheets_service = GoogleSheetsService()
        await sheets_service.append_report({
            'report_date': report.report_date,
            'branch_name': current_employee.branch.name,
            'employee_name': current_employee.full_name,
            'total_income': report.total_income,
            'cash': report.cash,
            'cashless': report.cashless,
            'cash_balance': report.cash_balance,
            'clients_count': report.clients_count,
            'cash_to_suppliers': report.cash_to_suppliers,
            'cashless_to_suppliers': report.cashless_to_suppliers,
            'version': report.version,
            'created_at': report.created_at
        })
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Отчет успешно сохранен!\n"
        f"Версия: {version}\n"
        f"Дата: {datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d')}"
    )
    await callback.message.answer(
        "Главное меню:", 
        reply_markup=get_main_menu("employee")
    )

@router.callback_query(ReportStates.summary, F.data == "confirm_edit")
async def confirm_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReportStates.waiting_for_total_income)
    await callback.message.edit_text(
        "Редактирование отчета. Введите общий приход за день (сумма):"
    )

@router.callback_query(ReportStates.summary, F.data == "confirm_restart")
async def confirm_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ReportStates.waiting_for_total_income)
    await callback.message.edit_text(
        "Начинаем заполнение заново. Введите общий приход за день (сумма):"
    )

@router.message(F.text == "✏️ Исправить отчет за сегодня")
async def edit_today_report(message: Message, employee):
    await start_report(message, employee)

@router.message(F.text == "📋 Мои последние отчеты")
async def show_my_reports(message: Message, employee):
    async with async_session_maker() as session:
        report_dao = ReportDAO(session)
        reports = await report_dao.get_employee_reports(employee.id, limit=5)
        
        if not reports:
            await message.answer("📭 У вас еще нет отчетов.")
            return
        
        response = "📋 Ваши последние отчеты:\n\n"
        for report in reports:
            response += (
                f"📅 {report.report_date.strftime('%d.%m.%Y')} "
                f"(v{report.version})\n"
                f"💰 Приход: {report.total_income}\n"
                f"👥 Клиентов: {report.clients_count}\n"
                f"---\n"
            )
        
        await message.answer(response)