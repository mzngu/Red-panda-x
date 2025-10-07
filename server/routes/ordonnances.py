from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database.database import get_db
from database.controller import create_ordonnance_with_meds, get_ordonnances_par_utilisateur
from services.ordo_extract import extract_meds
from models import Utilisateur
from database.auth import get_current_user

router = APIRouter(prefix="/ordonnances", tags=["ordonnances"])

@router.get("/")
def list_ordonnances(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """Récupère toutes les ordonnances de l'utilisateur connecté."""
    ordonnances = get_ordonnances_par_utilisateur(db, utilisateur_id=current_user.id)
    
    # Formatter la réponse pour correspondre à ce que le front-end attend
    results = []
    for o in ordonnances:
        results.append({
            "id": o.id,
            "title": o.nom or f"Ordonnance du {o.date_ordonnance.strftime('%d/%m/%Y')}",
            "date": o.date_ordonnance.isoformat(),
            "image": "/images/dna.png" # Image par défaut
        })
    return results

@router.post("/scan")
async def scan_ordonnance(
    utilisateur_id: int = Form(...),
    valid_until: Optional[str] = Form(None),  # "YYYY-MM-DD"
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read() if image else None
    meds = extract_meds(image_bytes, typed_text=ocr_text)
    if not meds:
        raise HTTPException(status_code=422, detail="Impossible d'extraire des médicaments.")

    valid_dt = None
    if valid_until:
        try:
            valid_dt = datetime.strptime(valid_until, "%Y-%m-%d").date()
        except ValueError:
            pass



    ordon = create_ordonnance_with_meds(
        db, utilisateur_id=utilisateur_id, valid_until=valid_dt, meds=meds
    )
    return {"id": ordon.id, "medicaments": meds, "valid_until": valid_until}

@router.get("/{ordonnance_id}")
def get_ordonnance(ordonnance_id: int, db: Session = Depends(get_db)):
    from models import Ordonnance, Medicament
    ordon = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not ordon:
        raise HTTPException(404, "Ordonnance introuvable")
    meds = (
        db.query(Medicament)
        .filter(Medicament.ordonnance_id == ordonnance_id)
        .all()
    )
    return {
        "id": ordon.id,
        "valid_until": getattr(ordon, "date_fin", None),
        "medicaments": [
            {"id": m.id, "nom": m.nom, "frequence": m.frequence} for m in meds
        ],
    }
