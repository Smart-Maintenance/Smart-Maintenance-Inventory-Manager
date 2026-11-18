from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, RoleChecker

require_gestionar = RoleChecker([models.UserRole.ADMIN, models.UserRole.GESTIONAR])

router = APIRouter(prefix="/inventory", tags=["Inventory & Alerts"])

def check_and_create_stock_alert(db: Session, part: models.SparePart):
    if part.quantity <= part.min_stock:
        alert = models.Notification(
            message=f"Stoc critic pentru '{part.name}' (SKU: {part.sku}): {part.quantity} buc. ramase (prag minim: {part.min_stock}).",
            type="stoc_minim"
        )
        db.add(alert)

@router.post("/parts", response_model=schemas.SparePartResponse)
def add_spare_part(
    part: schemas.SparePartCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_gestionar)
):
    existing = db.query(models.SparePart).filter(models.SparePart.sku == part.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Codul SKU exista deja in inventar.")
    
    new_part = models.SparePart(**part.model_dump())
    db.add(new_part)
    db.flush()
    check_and_create_stock_alert(db, new_part)
    db.commit()
    db.refresh(new_part)
    return new_part

@router.get("/parts", response_model=List[schemas.SparePartResponse])
def get_spare_parts(db: Session = Depends(get_db)):
    return db.query(models.SparePart).all()

@router.patch("/parts/{part_id}", response_model=schemas.SparePartResponse)
def update_spare_part(
    part_id: int,
    updates: schemas.SparePartUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_gestionar)
):
    part = db.query(models.SparePart).filter(models.SparePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Piesa nu a fost gasita.")
    
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(part, key, value)
    
    check_and_create_stock_alert(db, part)
    db.commit()
    db.refresh(part)
    return part

@router.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(models.Notification).order_by(models.Notification.created_at.desc()).all()

@router.patch("/notifications/{notif_id}/read", response_model=schemas.NotificationResponse)
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificarea nu a fost gasita.")
    
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif