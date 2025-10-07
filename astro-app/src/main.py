from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas
from .database import init_db, get_db

# Dans une application de production, vous utiliseriez probablement Alembic pour les migrations.
init_db()

app = FastAPI(
    title="Sorrel API",
    description="API pour la gestion des données médicales des utilisateurs.",
    version="1.0.0",
)

# --- Endpoints pour les Utilisateurs ---

@app.post("/utilisateurs/", response_model=schemas.Utilisateur, tags=["Utilisateurs"])
def create_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    """
    Crée un nouvel utilisateur.
    """
    db_utilisateur = crud.get_utilisateur_by_email(db, email=utilisateur.email)
    if db_utilisateur:
        raise HTTPException(status_code=400, detail="Cet email est déjà enregistré.")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.get("/utilisateurs/", response_model=List[schemas.Utilisateur], tags=["Utilisateurs"])
def read_utilisateurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de tous les utilisateurs.
    """
    utilisateurs = crud.get_utilisateurs(db, skip=skip, limit=limit)
    return utilisateurs

@app.get("/utilisateurs/{utilisateur_id}", response_model=schemas.Utilisateur, tags=["Utilisateurs"])
def read_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    """
    Récupère un utilisateur par son ID.
    """
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    return db_utilisateur

# --- Endpoints pour les Ordonnances ---

@app.post("/utilisateurs/{utilisateur_id}/ordonnances/", response_model=schemas.Ordonnance, tags=["Ordonnances"])
def create_ordonnance_pour_utilisateur(
    utilisateur_id: int, ordonnance: schemas.OrdonnanceCreate, db: Session = Depends(get_db)
):
    """
    Crée une nouvelle ordonnance pour un utilisateur spécifique.
    """
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    return crud.create_ordonnance_pour_utilisateur(db=db, ordonnance=ordonnance, utilisateur_id=utilisateur_id)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API Sorrel"}