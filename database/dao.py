from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Branch, Employee, Report


class BranchDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[Branch]:
        result = await self.session.execute(
            select(Branch).order_by(Branch.name)
        )
        return result.scalars().all()
    
    async def get_by_id(self, branch_id: int) -> Optional[Branch]:
        result = await self.session.execute(
            select(Branch).where(Branch.id == branch_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Branch]:
        result = await self.session.execute(
            select(Branch).where(Branch.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, name: str) -> Branch:
        branch = Branch(name=name)
        self.session.add(branch)
        await self.session.commit()
        await self.session.refresh(branch)
        return branch
    
    async def update(self, branch_id: int, name: str) -> Optional[Branch]:
        branch = await self.get_by_id(branch_id)
        if branch:
            branch.name = name
            await self.session.commit()
            await self.session.refresh(branch)
        return branch
    
    async def delete(self, branch_id: int) -> bool:
        branch = await self.get_by_id(branch_id)
        if branch:
            await self.session.delete(branch)
            await self.session.commit()
            return True
        return False


class EmployeeDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[Employee]:
        result = await self.session.execute(
            select(Employee)
            .join(Branch)
            .order_by(Branch.name, Employee.full_name)
        )
        return result.scalars().all()
    
    async def get_by_id(self, employee_id: int) -> Optional[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()
    
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
    
    async def get_branch_employees(self, branch_id: int) -> List[Employee]:
        result = await self.session.execute(
            select(Employee)
            .where(and_(Employee.branch_id == branch_id, Employee.is_active == True))
            .order_by(Employee.full_name)
        )
        return result.scalars().all()
    
    async def create(
        self,
        telegram_id: int,
        full_name: str,
        branch_id: int,
        is_admin: bool = False
    ) -> Employee:
        employee = Employee(
            telegram_id=telegram_id,
            full_name=full_name,
            branch_id=branch_id,
            is_admin=is_admin
        )
        self.session.add(employee)
        await self.session.commit()
        await self.session.refresh(employee)
        return employee
    
    async def update(
        self,
        telegram_id: int,
        full_name: Optional[str] = None,
        branch_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> Optional[Employee]:
        employee = await self.get_by_telegram_id(telegram_id)
        if not employee:
            return None
        
        if full_name is not None:
            employee.full_name = full_name
        if branch_id is not None:
            employee.branch_id = branch_id
        if is_active is not None:
            employee.is_active = is_active
        if is_admin is not None:
            employee.is_admin = is_admin
        
        await self.session.commit()
        await self.session.refresh(employee)
        return employee
    
    async def deactivate(self, telegram_id: int) -> Optional[Employee]:
        return await self.update(telegram_id, is_active=False)
    
    async def delete(self, telegram_id: int) -> bool:
        employee = await self.get_by_telegram_id(telegram_id)
        if employee:
            await self.session.delete(employee)
            await self.session.commit()
            return True
        return False


class ReportDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        report_date: datetime,
        total_income: float,
        cash: float,
        cashless: float,
        cash_balance: float,
        clients_count: int,
        cash_to_suppliers: float,
        cashless_to_suppliers: float,
        employee_id: int,
        branch_id: int,
        version: int = 1
    ) -> Report:
        # Убираем часовой пояс если он есть
        if report_date.tzinfo is not None:
            report_date = report_date.replace(tzinfo=None)
        
        report = Report(
            report_date=report_date,
            total_income=total_income,
            cash=cash,
            cashless=cashless,
            cash_balance=cash_balance,
            clients_count=clients_count,
            cash_to_suppliers=cash_to_suppliers,
            cashless_to_suppliers=cashless_to_suppliers,
            version=version,
            employee_id=employee_id,
            branch_id=branch_id
        )
        
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def get_by_id(self, report_id: int) -> Optional[Report]:
        result = await self.session.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_today_reports(self) -> List[Report]:
        today = datetime.utcnow().date()
        result = await self.session.execute(
            select(Report)
            .where(func.date(Report.report_date) == today)
            .join(Employee)
            .join(Branch)
            .order_by(Branch.name)
        )
        return result.scalars().all()
    
    async def get_daily_reports(self, report_date: date) -> List[Report]:
        result = await self.session.execute(
            select(Report)
            .where(func.date(Report.report_date) == report_date)
            .join(Employee)
            .join(Branch)
            .order_by(Branch.name)
        )
        return result.scalars().all()
    
    async def get_employee_today_report(self, employee_id: int) -> Optional[Report]:
        today = datetime.utcnow().date()
        result = await self.session.execute(
            select(Report).where(
                and_(
                    Report.employee_id == employee_id,
                    func.date(Report.report_date) == today
                )
            ).order_by(Report.version.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_employee_reports(
        self,
        employee_id: int,
        limit: int = 10
    ) -> List[Report]:
        result = await self.session.execute(
            select(Report)
            .where(Report.employee_id == employee_id)
            .order_by(Report.report_date.desc(), Report.version.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_branch_reports(
        self,
        branch_id: int,
        days: int = 7
    ) -> List[Report]:
        from_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Report).where(
                and_(
                    Report.branch_id == branch_id,
                    Report.report_date >= from_date
                )
            ).order_by(Report.report_date.desc())
        )
        return result.scalars().all()
    
    async def get_reports_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Report]:
        result = await self.session.execute(
            select(Report)
            .where(
                and_(
                    func.date(Report.report_date) >= start_date,
                    func.date(Report.report_date) <= end_date
                )
            )
            .join(Employee)
            .join(Branch)
            .order_by(Report.report_date.desc(), Branch.name)
        )
        return result.scalars().all()
    
    async def update(
        self,
        report_id: int,
        total_income: Optional[float] = None,
        cash: Optional[float] = None,
        cashless: Optional[float] = None,
        cash_balance: Optional[float] = None,
        clients_count: Optional[int] = None,
        cash_to_suppliers: Optional[float] = None,
        cashless_to_suppliers: Optional[float] = None,
        version: Optional[int] = None
    ) -> Optional[Report]:
        report = await self.get_by_id(report_id)
        if not report:
            return None
        
        if total_income is not None:
            report.total_income = total_income
        if cash is not None:
            report.cash = cash
        if cashless is not None:
            report.cashless = cashless
        if cash_balance is not None:
            report.cash_balance = cash_balance
        if clients_count is not None:
            report.clients_count = clients_count
        if cash_to_suppliers is not None:
            report.cash_to_suppliers = cash_to_suppliers
        if cashless_to_suppliers is not None:
            report.cashless_to_suppliers = cashless_to_suppliers
        if version is not None:
            report.version = version
        
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def delete(self, report_id: int) -> bool:
        report = await self.get_by_id(report_id)
        if report:
            await self.session.delete(report)
            await self.session.commit()
            return True
        return False