from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Branch(Base):
    __tablename__ = "branch"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), 
        default=func.now()  # Время будет устанавливаться базой данных
    )
    
    employees: Mapped[list["Employee"]] = relationship(back_populates="branch")
    reports: Mapped[list["Report"]] = relationship(back_populates="branch")


class Employee(Base):
    __tablename__ = "employee"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), 
        default=func.now()
    )
    branch_id: Mapped[int] = mapped_column(ForeignKey("branch.id"))
    
    branch: Mapped["Branch"] = relationship(back_populates="employees")
    reports: Mapped[list["Report"]] = relationship(back_populates="employee")


class Report(Base):
    __tablename__ = "report"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    total_income: Mapped[float] = mapped_column(Numeric(10, 2))
    cash: Mapped[float] = mapped_column(Numeric(10, 2))
    cashless: Mapped[float] = mapped_column(Numeric(10, 2))
    cash_balance: Mapped[float] = mapped_column(Numeric(10, 2))
    clients_count: Mapped[int] = mapped_column(Integer)
    cash_to_suppliers: Mapped[float] = mapped_column(Numeric(10, 2))
    cashless_to_suppliers: Mapped[float] = mapped_column(Numeric(10, 2))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), 
        default=func.now()
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branch.id"))
    
    employee: Mapped["Employee"] = relationship(back_populates="reports")
    branch: Mapped["Branch"] = relationship(back_populates="reports")