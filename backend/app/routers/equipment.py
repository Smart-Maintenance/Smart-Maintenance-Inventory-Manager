from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/equipment", tags=["Equipment"])

@router.post("/", response_model=schemas.EquipmentResponse)
def create_equipment(item: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Equipment).filter(models.Equipment.serial_number == item.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Exista deja un echipament cu acest numar de serie.")
    
    new_eq = models.Equipment(**item.model_dump())
    db.add(new_eq)
    db.commit()
    db.refresh(new_eq)
    return new_eq

@router.get("/", response_model=List[schemas.EquipmentResponse])
def get_all_equipment(db: Session = Depends(get_db)):
    return db.query(models.Equipment).all()

@router.patch("/{equipment_id}/status", response_model=schemas.EquipmentResponse)
def update_equipment_status(equipment_id: int, status: models.EquipmentStatus, db: Session = Depends(get_db)):
    eq = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Echipamentul nu a fost gasit.")
    
    eq.status = status
    db.commit()
    db.refresh(eq)
    return eq