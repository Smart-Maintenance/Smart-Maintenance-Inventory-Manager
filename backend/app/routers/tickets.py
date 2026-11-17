from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .inventory import check_and_create_stock_alert

router = APIRouter(prefix="/tickets", tags=["Maintenance Tickets"])

@router.post("/", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    eq = db.query(models.Equipment).filter(models.Equipment.id == ticket.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Echipamentul specificat nu exista.")
    
    eq.status = models.EquipmentStatus.IN_MENTENANTA
    new_ticket = models.MaintenanceTicket(**ticket.model_dump())
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/", response_model=List[schemas.TicketResponse])
def get_tickets(db: Session = Depends(get_db)):
    return db.query(models.MaintenanceTicket).all()

@router.post("/{ticket_id}/complete", response_model=schemas.TicketResponse)
def complete_ticket(ticket_id: int, payload: schemas.TicketComplete, db: Session = Depends(get_db)):
    ticket = db.query(models.MaintenanceTicket).filter(models.MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tichetul nu a fost gasit.")
    if ticket.status == models.TicketStatus.FINALIZAT:
        raise HTTPException(status_code=400, detail="Tichetul este deja finalizat.")

    # 1. Validam stocul pentru toate piesele inainte sa facem modificari
    parts_to_update = []
    for item in payload.parts_used:
        part = db.query(models.SparePart).filter(models.SparePart.id == item.part_id).first()
        if not part:
            raise HTTPException(status_code=404, detail=f"Piesa cu ID {item.part_id} nu exista.")
        if part.quantity < item.quantity_used:
            raise HTTPException(
                status_code=400,
                detail=f"Stoc insuficient pentru '{part.name}' (disponibil: {part.quantity}, cerut: {item.quantity_used})."
            )
        parts_to_update.append((part, item.quantity_used))

    # 2. Scadem stocul, inregistram consumul si declansam alerte daca e cazul
    for part, qty_used in parts_to_update:
        part.quantity -= qty_used
        db.add(models.TicketPart(ticket_id=ticket.id, part_id=part.id, quantity_used=qty_used))
        check_and_create_stock_alert(db, part)

    # 3. Inchidem tichetul si repunem echipamentul in functiune
    ticket.status = models.TicketStatus.FINALIZAT
    ticket.completed_at = datetime.utcnow()
    ticket.equipment.status = models.EquipmentStatus.FUNCTIONAL

    db.commit()
    db.refresh(ticket)
    return ticket