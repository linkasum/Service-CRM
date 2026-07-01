"""
Сервис расчёта зарплаты
Безопасное вычисление по формуле через simpleeval
"""
from typing import Dict, Any, Optional
from sqlmodel import Session, select
from simpleeval import simple_eval, SimpleEval

from models.salary_config import SalaryConfig
from models.order import Order
from models.salary_record import SalaryRecord
from models.user import User
from core.logging import logger


class SalaryService:
    """Сервис для безопасного расчёта зарплаты по формуле"""
    
    # Разрешённые функции в формулах
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "int": int,
        "float": float,
    }
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_formula(self) -> Optional[SalaryConfig]:
        """Получить активную формулу"""
        return self.session.exec(
            select(SalaryConfig).where(SalaryConfig.is_active == True)
        ).first()
    
    def calculate_for_order(
        self,
        order: Order,
        formula: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Рассчитать зарплату для заказа.
        
        Возвращает:
        {
            "total": общая сумма заказа,
            "parts": стоимость запчастей,
            "work": стоимость работ,
            "warranty": флаг гарантии (0 или 1),
            "formula": использованная формула,
            "result": рассчитанная сумма,
        }
        """
        if not formula:
            config = self.get_active_formula()
            if not config:
                raise ValueError("Нет активной формулы зарплаты")
            formula = config.formula_string
        
        total = order.total_cost or 0
        parts = order.parts_cost or 0
        work = order.work_cost or 0
        warranty = 1 if (order.warranty_days and order.warranty_days > 0) else 0
        
        try:
            result = simple_eval(
                formula,
                names={
                    "total": total,
                    "parts": parts,
                    "work": work,
                    "warranty": warranty,
                },
                functions=self.ALLOWED_FUNCTIONS,
            )
        except Exception as e:
            logger.error(f"Ошибка расчёта зарплаты: {e}")
            raise ValueError(f"Ошибка вычисления формулы: {str(e)}")
        
        return {
            "total": total,
            "parts": parts,
            "work": work,
            "warranty": warranty,
            "formula": formula,
            "result": round(result, 2),
        }
    
    def create_salary_records_for_period(
        self,
        period_start,
        period_end,
        status: str = "accrued",
    ) -> list:
        """
        Создать ведомости за период.
        Собирает все закрытые (issued) заказы мастеров за период.
        """
        config = self.get_active_formula()
        if not config:
            raise ValueError("Нет активной формулы зарплаты")
        
        orders = self.session.exec(
            select(Order).where(
                Order.status == "issued",
                Order.master_id.isnot(None),
                Order.issued_at >= period_start,
                Order.issued_at <= period_end,
            )
        ).all()
        
        created_records = []
        
        for order in orders:
            calculation = self.calculate_for_order(order, config.formula_string)
            
            record = SalaryRecord(
                user_id=order.master_id,
                order_id=order.id,
                calculated_amount=calculation["result"],
                status=status,
                period_start=period_start,
                period_end=period_end,
            )
            self.session.add(record)
            created_records.append(record)
        
        self.session.commit()
        
        for r in created_records:
            self.session.refresh(r)
        
        logger.info(
            f"Создано {len(created_records)} записей ведомости "
            f"за период {period_start.date()} - {period_end.date()}"
        )
        
        return created_records
    
    def validate_formula(self, formula: str) -> tuple[bool, str]:
        """
        Проверить формулу на безопасность и корректность.
        Возвращает (успех, сообщение об ошибке)
        """
        try:
            # Тестовое вычисление
            simple_eval(
                formula,
                names={"total": 100, "parts": 20, "work": 30, "warranty": 0},
                functions=self.ALLOWED_FUNCTIONS,
            )
            return True, ""
        except Exception as e:
            return False, str(e)
