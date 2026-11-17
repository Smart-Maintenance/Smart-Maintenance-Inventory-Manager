import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEHNICIAN = "tehnician"
    GESTIONAR = "gestionar"

class EquipmentStatus(str, enum.Enum):
    FUNCTIONAL = "functional"
    IN_MENTENANTA = "in_mentenanta"
    DEFECT = "defect"

class TicketStatus(str, enum.Enum):
    DESCHIS = "deschis"
    IN_LUCRU = "in_lucru"
    FINALIZAT = "finalizat"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TEHNICIAN, nullable=False)

    tickets = relationship("MaintenanceTicket", back_populates="technician")

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=False)
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.FUNCTIONAL)
    next_maintenance = Column(DateTime, nullable=True)

    tickets = relationship("MaintenanceTicket", back_populates="equipment")

class SparePart(Base):
    __tablename__ = "spare_parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=5, nullable=False)
    unit_price = Column(Float, default=0.0)

class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.DESCHIS)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    equipment = relationship("Equipment", back_populates="tickets")
    technician = relationship("User", back_populates="tickets")
    parts_used = relationship("TicketPart", back_populates="ticket")

class TicketPart(Base):
    __tablename__ = "ticket_parts"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("maintenance_tickets.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("spare_parts.id"), nullable=False)
    quantity_used = Column(Integer, nullable=False)

    ticket = relationship("MaintenanceTicket", back_populates="parts_used")
    part = relationship("SparePart")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)  # ex: "stoc_minim", "mentenanta_scadenta"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)