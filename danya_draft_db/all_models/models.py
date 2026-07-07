# models.py
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Date, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from db import Base


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    short_name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)
    opf = Column(String(100), nullable=True)
    inn = Column(BigInteger, nullable=True)
    kpp = Column(BigInteger, nullable=True)
    ogrn = Column(BigInteger, nullable=True)
    okpo = Column(BigInteger, nullable=True)
    okato = Column(BigInteger, nullable=True)
    oktmo = Column(BigInteger, nullable=True)
    okfs = Column(BigInteger, nullable=True)
    tax_system = Column(String(100), nullable=True)

    # Связи
    addresses = relationship("Address", back_populates="company", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    directors = relationship("Director", back_populates="company", cascade="all, delete-orphan")
    activity_types = relationship("ActivityType", back_populates="company", cascade="all, delete-orphan")
    details = relationship("CompanyDetails", back_populates="company", uselist=False, cascade="all, delete-orphan")
    financials = relationship("FinancialPerformance", back_populates="company", cascade="all, delete-orphan")


class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    address_type = Column(String(50), nullable=True) 
    address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    postal_index = Column(BigInteger, nullable=True)

    company = relationship("Company", back_populates="addresses")


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    contact_type = Column(String(50), nullable=True)      
    value = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="contacts")


class Director(Base):
    __tablename__ = "director"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    inn = Column(BigInteger, nullable=True)
    year = Column(Date, nullable=True)   
    is_current = Column(Boolean, default=True)

    company = relationship("Company", back_populates="directors")


class ActivityType(Base):
    __tablename__ = "activity_type"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    okved_code = Column(String(20), nullable=True)
    activity_name = Column(String(500), nullable=True)
    is_main = Column(Boolean, default=False)

    company = relationship("Company", back_populates="activity_types")


class CompanyDetails(Base):
    __tablename__ = "company_details"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    registration_date = Column(Date, nullable=True)
    authorized_capital = Column(Numeric(18, 2), nullable=True)
    employee_count = Column(Integer, nullable=True)
    msp_category = Column(Integer, nullable=True)
    source_url = Column(String(500), nullable=True)
    ifns_reg_date = Column(Date, nullable=True)
    ifns_code = Column(Integer, nullable=True)
    ifns_name = Column(String(255), nullable=True)
    fss_reg_date = Column(Date, nullable=True)
    fss_code = Column(Integer, nullable=True)
    fss_name = Column(String(255), nullable=True)
    pfr_reg_date = Column(Date, nullable=True)
    pfr_code = Column(Integer, nullable=True)
    pfr_name = Column(String(255), nullable=True)
    special_tax_regimes = Column(String(255), nullable=True)
    average_headcount = Column(Integer, nullable=True)

    company = relationship("Company", back_populates="details")


class FinancialPerformance(Base):
    __tablename__ = "financial_performance"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=True)
    revenue = Column(BigInteger, nullable=True)                 
    sales_profit = Column(BigInteger, nullable=True)            
    pretax_profit = Column(BigInteger, nullable=True)          
    net_profit = Column(BigInteger, nullable=True)              
    receivables = Column(BigInteger, nullable=True)          
    payables = Column(BigInteger, nullable=True)              
    inventory = Column(BigInteger, nullable=True)             
    fixed_assets = Column(BigInteger, nullable=True)           
    liquidity_abs = Column(Numeric(18, 4), nullable=True)       
    liquidity_curr = Column(Numeric(18, 4), nullable=True)       
    solvency_recovery = Column(Numeric(18, 4), nullable=True)   
    fin_stability = Column(Numeric(18, 4), nullable=True)       

    company = relationship("Company", back_populates="financials")



