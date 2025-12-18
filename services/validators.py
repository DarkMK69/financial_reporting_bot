from typing import Dict, Optional, Tuple
from decimal import Decimal

class ReportValidator:
    @staticmethod
    def validate_amount(value: str) -> Tuple[bool, Optional[float]]:
        try:
            amount = float(value)
            if amount < 0:
                return False, None
            return True, amount
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_clients_count(value: str) -> Tuple[bool, Optional[int]]:
        try:
            count = int(value)
            if count < 0:
                return False, None
            return True, count
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_totals(data: Dict) -> Tuple[bool, Optional[str]]:
        try:
            total_income = float(data['total_income'])
            cash = float(data['cash'])
            cashless = float(data['cashless'])
            
            if abs((cash + cashless) - total_income) > 0.01:
                return False, f"Наличные ({cash}) + Безнал ({cashless}) должно равняться Общему приходу ({total_income})"
            
            return True, None
        except (KeyError, ValueError):
            return False, "Ошибка валидации итогов"
    
    @staticmethod
    def validate_all_fields(data: Dict) -> Tuple[bool, Optional[str]]:
        required_fields = [
            'total_income', 'cash', 'cashless', 'cash_balance',
            'clients_count', 'cash_to_suppliers', 'cashless_to_suppliers'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Поле '{field}' обязательно для заполнения"
        
        # Проверка сумм
        for field in ['total_income', 'cash', 'cashless', 'cash_balance', 
                     'cash_to_suppliers', 'cashless_to_suppliers']:
            if float(data[field]) < 0:
                return False, f"Сумма '{field}' не может быть отрицательной"
        
        # Проверка количества клиентов
        if int(data['clients_count']) < 0:
            return False, "Количество клиентов не может быть отрицательным"
        
        # Проверка равенства сумм
        return ReportValidator.validate_totals(data)