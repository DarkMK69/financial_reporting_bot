from typing import Optional, List
from datetime import datetime, date
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Branch, Employee, Report
import pytz

class BranchDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[Branch]:
        result = await self.session.execute(select(Branch).order_by(Branch.name))
        return result.scalars().all()
    
    async def get_by_id(self, branch_id: int) -> Optional[Branch]:
        result = await self.session.execute(select(Branch).where(Branch.id == branch_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Branch]:
        result = await self.session.execute(select(Branch).where(Branch.name == name))
        return result.scalar_one_or_none()
    
    async def create(self, name: str) -> Branch:
        branch = Branch(name=name)
        self.session.add(branch)
        await self.session.commit()
        return branch

class EmployeeDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[Employee]:
        result = await self.session.execute(
            select(Employee).join(Branch).order_by(Branch.name, Employee.full_name)
        )
        return result.scalars().all()
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_employees(self) -> List[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.is_active == True)
        )
        return result.scalars().all()
    
    async def create(self, telegram_id: int, full_name: str, branch_id: int) -> Employee:
        employee = Employee(
            telegram_id=telegram_id,
            full_name=full_name,
            branch_id=branch_id
        )
        self.session.add(employee)
        await self.session.commit()
        return employee
    
    async def deactivate(self, telegram_id: int) -> Optional[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.telegram_id == telegram_id)
        )
        employee = result.scalar_one_or_none()
        if employee:
            employee.is_active = False
            await self.session.commit()
        return employee

class ReportDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, **kwargs) -> Report:
        report = Report(**kwargs)
        self.session.add(report)
        await self.session.commit()
        return report
    
    async def get_today_reports(self) -> List[Report]:
        today = datetime.now(pytz.timezone('Europe/Moscow')).date()
        result = await self.session.execute(
            select(Report).where(func.date(Report.report_date) == today)
            .join(Employee).join(Branch)
            .order_by(Branch.name)
        )
        return result.scalars().all()
    
    async def get_daily_reports(self, report_date: date) -> List[Report]:
        result = await self.session.execute(
            select(Report).where(func.date(Report.report_date) == report_date)
            .join(Employee).join(Branch)
            .order_by(Branch.name)
        )
        return result.scalars().all()
    
    async def get_employee_today_report(self, employee_id: int) -> Optional[Report]:
        today = datetime.now(pytz.timezone('Europe/Moscow')).date()
        result = await self.session.execute(
            select(Report).where(
                and_(
                    Report.employee_id == employee_id,
                    func.date(Report.report_date) == today
                )
            ).order_by(Report.version.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_employee_reports(self, employee_id: int, limit: int = 10) -> List[Report]:
        result = await self.session.execute(
            select(Report).where(Report.employee_id == employee_id)
            .order_by(Report.report_date.desc(), Report.version.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_branch_reports(self, branch_id: int, days: int = 7) -> List[Report]:
        from_date = datetime.now(pytz.timezone('Europe/Moscow')) - timedelta(days=days)
        result = await self.session.execute(
            select(Report).where(
                and_(
                    Report.branch_id == branch_id,
                    Report.report_date >= from_date
                )
            ).order_by(Report.report_date.desc())
        )
        return result.scalars().all()