from typing import Optional
from datetime import date
from pydantic import BaseModel
from decimal import Decimal

# ---------- Company ----------
class CompanySchema(BaseModel):
    id: Optional[int] = None
    short_name: str
    full_name: Optional[str] = None
    status: Optional[str] = None
    opf: Optional[str] = None
    inn: Optional[int] = None
    kpp: Optional[int] = None
    ogrn: Optional[int] = None
    okpo: Optional[int] = None
    okato: Optional[int] = None
    oktmo: Optional[int] = None
    okfs: Optional[int] = None
    tax_system: Optional[str] = None

    class Config:
        orm_mode = True


# ---------- Address ----------
class AddressSchema(BaseModel):
    id: Optional[int] = None
    company_id: int  # обязательный внешний ключ
    address_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_index: Optional[int] = None

    class Config:
        orm_mode = True


# ---------- Contact ----------
class ContactSchema(BaseModel):
    id: Optional[int] = None
    company_id: int
    contact_type: Optional[str] = None
    value: Optional[str] = None

    class Config:
        orm_mode = True


# ---------- Director ----------
class DirectorSchema(BaseModel):
    id: Optional[int] = None
    company_id: int
    full_name: Optional[str] = None
    position: Optional[str] = None
    inn: Optional[int] = None
    year: Optional[date] = None
    is_current: Optional[bool] = True

    class Config:
        orm_mode = True


# ---------- ActivityType ----------
class ActivityTypeSchema(BaseModel):
    id: Optional[int] = None
    company_id: int
    okved_code: Optional[str] = None
    activity_name: Optional[str] = None
    is_main: Optional[bool] = False

    class Config:
        orm_mode = True


# ---------- CompanyDetails ----------
class CompanyDetailsSchema(BaseModel):
    id: Optional[int] = None
    company_id: int
    registration_date: Optional[date] = None
    authorized_capital: Optional[Decimal] = None
    employee_count: Optional[int] = None
    msp_category: Optional[int] = None
    source_url: Optional[str] = None
    ifns_reg_date: Optional[date] = None
    ifns_code: Optional[int] = None
    ifns_name: Optional[str] = None
    fss_reg_date: Optional[date] = None
    fss_code: Optional[int] = None
    fss_name: Optional[str] = None
    pfr_reg_date: Optional[date] = None
    pfr_code: Optional[int] = None
    pfr_name: Optional[str] = None
    special_tax_regimes: Optional[str] = None
    average_headcount: Optional[int] = None

    class Config:
        orm_mode = True


# ---------- FinancialPerformance ----------
class FinancialPerformanceSchema(BaseModel):
    id: Optional[int] = None
    company_id: int
    year: Optional[int] = None
    revenue: Optional[int] = None
    sales_profit: Optional[int] = None
    pretax_profit: Optional[int] = None
    net_profit: Optional[int] = None
    receivables: Optional[int] = None
    payables: Optional[int] = None
    inventory: Optional[int] = None
    fixed_assets: Optional[int] = None
    liquidity_abs: Optional[Decimal] = None
    liquidity_curr: Optional[Decimal] = None
    solvency_recovery: Optional[Decimal] = None
    fin_stability: Optional[Decimal] = None

    class Config:
        orm_mode = True



