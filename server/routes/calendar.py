from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.schemas import EventCreate, EventOut
import database.controller as crud
from database.auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/calendar", tags=["Calendar"])

class DonePayload(BaseModel):
    done: bool
    
@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return crud.list_events_for_user(db, current_user.id)

@router.post("/events", response_model=EventOut)
def create_event(event: EventCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return crud.create_event(db, current_user.id, event)
    

@router.delete("/events/{event_id}")
def remove_event(event_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ok = crud.delete_event(db, current_user.id, event_id)
    if not ok:
        raise HTTPException(404, "Event not found")
    return {"ok": True}

@router.patch("/events/{event_id}/done", response_model=EventOut)
def set_event_done(event_id: int, payload: DonePayload, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ev = crud.update_event_done(db, current_user.id, event_id, payload.done)
    if not ev:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    return ev