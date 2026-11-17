from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from .models import EquipmentStatus, TicketStatus

# --- ECHIPAMENTE ---
class EquipmentCreate(BaseModel):
    name: str
    serial_number: str
    location: str
    status: EquipmentStatus = EquipmentStatus.FUNCTIONAL
    next_maintenance: Optional[datetime] = None

class EquipmentResponse(EquipmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- STOCURI PIESE ---
class SparePartCreate(BaseModel):
    name: str
    sku: str
    quantity: int = Field(..., ge=0)
    min_stock: int = Field(default=5, ge=0)
    unit_price: float = Field(default=0.0, ge=0.0)

class SparePartUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0.0)

class SparePartResponse(SparePartCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- TICHETE DE MENTENANTA ---
class TicketPartItem(BaseModel):
    part_id: int
    quantity_used: int = Field(..., gt=0)

class TicketCreate(BaseModel):
    equipment_id: int
    technician_id: int
    description: str

class TicketComplete(BaseModel):
    parts_used: List[TicketPartItem] = []

class TicketResponse(BaseModel):
    id: int
    equipment_id: int
    technician_id: int
    description: str
    status: TicketStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- NOTIFICARI ---
class NotificationResponse(BaseModel):
    id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)