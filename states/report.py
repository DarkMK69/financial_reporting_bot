from aiogram.fsm.state import StatesGroup, State

class ReportStates(StatesGroup):
    waiting_for_total_income = State()
    waiting_for_cash = State()
    waiting_for_cashless = State()
    waiting_for_cash_balance = State()
    waiting_for_clients_count = State()
    waiting_for_cash_to_suppliers = State()
    waiting_for_cashless_to_suppliers = State()
    summary = State()