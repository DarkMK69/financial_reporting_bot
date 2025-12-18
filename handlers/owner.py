from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func
from database.session import async_session_maker
from database.dao import ReportDAO, BranchDAO
from database.models import Report, Employee, Branch
from keyboards.builder import get_main_menu

router = Router()


@router.message(F.text == "📊 Отчет за сегодня")
@router.message(Command("today"))
async def cmd_today(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    async with async_session_maker() as session:
        # Получаем отчеты с явной загрузкой связей
        today = datetime.utcnow().date()
        
        # Вариант 1: Используем SQLAlchemy напрямую с явной загрузкой
        result = await session.execute(
            select(Report)
            .options(
                joinedload(Report.employee).joinedload(Employee.branch)
            )
            .join(Employee)
            .join(Branch)
            .where(func.date(Report.report_date) == today)
            .order_by(Branch.name, Employee.full_name)
        )
        reports = result.unique().scalars().all()
        
        if not reports:
            await message.answer("📭 На сегодня отчетов еще нет.")
            return
        
        total_income = sum(r.total_income for r in reports)
        total_clients = sum(r.clients_count for r in reports)
        total_cash = sum(r.cash for r in reports)
        total_cashless = sum(r.cashless for r in reports)
        
        response = (
            f"📊 Сводка за сегодня "
            f"({datetime.utcnow().strftime('%d.%m.%Y')}):\n\n"
            f"🏢 Филиалов отчиталось: {len(set(r.employee.branch_id for r in reports))}\n"
            f"💰 Общий приход: {total_income:.2f}\n"
            f"💵 Наличные: {total_cash:.2f}\n"
            f"💳 Безналичные: {total_cashless:.2f}\n"
            f"👥 Всего клиентов: {total_clients}\n\n"
            f"Детали по филиалам:\n"
        )
        
        current_branch_id = None
        for report in reports:
            # Получаем branch через уже загруженную связь
            branch = report.employee.branch
            
            if branch.id != current_branch_id:
                current_branch_id = branch.id
                response += f"\n🏢 {branch.name}:\n"
            
            response += (
                f"  👤 {report.employee.full_name} (v{report.version}):\n"
                f"    💰 {report.total_income:.2f} | 👥 {report.clients_count}\n"
            )
        
        await message.answer(response)


@router.message(F.text == "📅 Отчет за дату")
@router.message(Command("daily"))
async def cmd_daily(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    # Простая реализация - можно расширить до выбора даты
    await message.answer(
        "Введите дату в формате ГГГГ-ММ-ДД:",
    )


@router.message(F.text.regexp(r'^\d{4}-\d{2}-\d{2}$'))
async def process_date(message: Message, employee):
    if not employee.is_admin:
        return
    
    try:
        date_obj = datetime.strptime(message.text, '%Y-%m-%d').date()
        
        async with async_session_maker() as session:
            # Используем явную загрузку связей
            result = await session.execute(
                select(Report)
                .options(
                    joinedload(Report.employee).joinedload(Employee.branch)
                )
                .join(Employee)
                .join(Branch)
                .where(func.date(Report.report_date) == date_obj)
                .order_by(Branch.name, Employee.full_name)
            )
            reports = result.unique().scalars().all()
            
            if not reports:
                await message.answer(f"📭 На {message.text} отчетов нет.")
                return
            
            response = f"📊 Отчет за {message.text}:\n\n"
            
            current_branch_id = None
            for report in reports:
                branch = report.employee.branch
                
                if branch.id != current_branch_id:
                    current_branch_id = branch.id
                    response += f"\n🏢 {branch.name}:\n"
                
                response += (
                    f"  👤 {report.employee.full_name}:\n"
                    f"    💰 Приход: {report.total_income:.2f}\n"
                    f"    👥 Клиентов: {report.clients_count}\n"
                    f"    💵 Наличные: {report.cash:.2f}\n"
                    f"    💳 Безналичные: {report.cashless:.2f}\n"
                    f"    📝 Версия: {report.version}\n"
                )
            
            await message.answer(response)
    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")


@router.message(F.text == "🏢 Филиалы")
@router.message(Command("branches"))
async def cmd_branches(message: Message, employee):
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
            # Подсчитываем активных сотрудников
            active_employees = len([e for e in branch.employees if e.is_active])
            response += f"📍 {branch.name}\n"
            response += f"   📅 Создан: {branch.created_at.strftime('%d.%m.%Y')}\n"
            response += f"   👥 Сотрудников: {active_employees} активных\n\n"
        
        await message.answer(response)


@router.message(F.text == "📋 Последние отчеты")
@router.message(Command("reports_last"))
async def cmd_reports_last(message: Message, employee):
    if not employee.is_admin:
        await message.answer("❌ Только для администраторов.")
        return
    
    async with async_session_maker() as session:
        # Получаем отчеты за последние 3 дня с явной загрузкой связей
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        result = await session.execute(
            select(Report)
            .options(
                joinedload(Report.employee).joinedload(Employee.branch)
            )
            .join(Employee)
            .join(Branch)
            .where(Report.report_date >= three_days_ago)
            .order_by(Report.report_date.desc())
            .limit(10)
        )
        reports = result.unique().scalars().all()
        
        if not reports:
            await message.answer("📭 Нет отчетов за последние дни.")
            return
        
        response = "📋 Последние отчеты:\n\n"
        for report in reports:
            branch = report.employee.branch
            response += (
                f"📅 {report.report_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"🏢 {branch.name} | 👤 {report.employee.full_name}\n"
                f"💰 {report.total_income:.2f} | 👥 {report.clients_count} | v{report.version}\n"
                f"---\n"
            )
        
        await message.answer(response)