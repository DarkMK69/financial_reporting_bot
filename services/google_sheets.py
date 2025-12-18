import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict
import pytz
from config import config

class GoogleSheetsService:
    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.credentials = Credentials.from_service_account_file(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH, 
            scopes=self.scope
        )
        self.client = gspread.authorize(self.credentials)
        self.sheet = self.client.open_by_key(config.REPORT_SHEET_ID)
    
    async def append_report(self, report_data: Dict) -> bool:
        try:
            worksheet = self.sheet.worksheet("Reports")
            
            row = [
                report_data['report_date'].strftime('%Y-%m-%d'),
                report_data['branch_name'],
                report_data['employee_name'],
                float(report_data['total_income']),
                float(report_data['cash']),
                float(report_data['cashless']),
                float(report_data['cash_balance']),
                int(report_data['clients_count']),
                float(report_data['cash_to_suppliers']),
                float(report_data['cashless_to_suppliers']),
                int(report_data['version']),
                report_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"Error appending to Google Sheets: {e}")
            return False
    
    async def sync_branches(self, branches: List[Dict]):
        try:
            worksheet = self.sheet.worksheet("Филиалы")
            worksheet.clear()
            
            headers = ["ID", "Название", "Дата создания"]
            worksheet.append_row(headers)
            
            for branch in branches:
                row = [
                    branch['id'],
                    branch['name'],
                    branch['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                ]
                worksheet.append_row(row)
        except Exception as e:
            print(f"Error syncing branches: {e}")
    
    async def sync_employees(self, employees: List[Dict]):
        try:
            worksheet = self.sheet.worksheet("Сотрудники")
            worksheet.clear()
            
            headers = ["ID", "Telegram ID", "ФИО", "Филиал", "Активен", "Админ", "Дата создания"]
            worksheet.append_row(headers)
            
            for employee in employees:
                row = [
                    employee['id'],
                    employee['telegram_id'],
                    employee['full_name'],
                    employee['branch_name'],
                    "Да" if employee['is_active'] else "Нет",
                    "Да" if employee['is_admin'] else "Нет",
                    employee['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                ]
                worksheet.append_row(row)
        except Exception as e:
            print(f"Error syncing employees: {e}")  