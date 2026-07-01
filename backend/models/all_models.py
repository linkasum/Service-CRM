"""
Центральный импорт всех моделей
"""
from models.role import Role
from models.user import User
from models.order import Order
from models.part import Part
from models.order_part import OrderPart
from models.salary_config import SalaryConfig
from models.salary_record import SalaryRecord
from models.notification_task import NotificationTask
from models.document_template import DocumentTemplate
from models.company_settings import CompanySettings
from models.custom_status import CustomStatus
from models.brand import Brand
from models.category import Category
from models.device_model import DeviceModel
from models.cash_shift import CashShift
from models.client_source import ClientSource
from models.age_group import AgeGroup
from models.bot_settings import BotSettings
from models.permission_group import PermissionGroup
from models.role_permission import RolePermission
from models.individual_permission import IndividualPermission
from models.document import Document
from models.order_payment import OrderPayment
from models.order_service import OrderService
from models.work_schedule import WorkSchedule

__all__ = [
    "Role", "User", "Order", "Part", "OrderPart",
    "SalaryConfig", "SalaryRecord", "NotificationTask",
    "DocumentTemplate", "CompanySettings",
    "CustomStatus", "Brand", "Category", "DeviceModel", "CashShift", "ClientSource", "AgeGroup",
    "PermissionGroup", "RolePermission", "IndividualPermission",
    "Document", "OrderPayment", "OrderService",
    "WorkSchedule",
]
