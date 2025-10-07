from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
import models
from . import schemas
from typing import Optional, List
from datetime import date, datetime
from database.schemas import EventCreate




# --- Configuration du hachage de mot de passe ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- CRUD pour Utilisateur ---
def get_utilisateur(db: Session, utilisateur_id: int):
    """Récupère un utilisateur par son ID."""
    return db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()

def get_utilisateur_by_email(db: Session, email: str):
    """Récupère un utilisateur par son email."""
    return db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()

def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100):
    """Récupère une liste d'utilisateurs."""
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

def create_utilisateur(db: Session, utilisateur: schemas.UtilisateurCreate):
    """Crée un nouvel utilisateur avec un mot de passe haché."""
    hashed_password = get_password_hash(utilisateur.mot_de_passe)
    db_utilisateur = models.Utilisateur(
        email=utilisateur.email,
        mot_de_passe=hashed_password,
        nom=utilisateur.nom,
        prenom=utilisateur.prenom,
        date_naissance=utilisateur.date_naissance,
        numero_telephone=utilisateur.numero_telephone,
        role=utilisateur.role,
        sexe=utilisateur.sexe
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def update_utilisateur(db: Session, utilisateur_id: int, utilisateur_data):
    db_utilisateur = get_utilisateur(db, utilisateur_id)
    if not db_utilisateur:
        return None

    if hasattr(utilisateur_data, "model_dump"):
        update_data = utilisateur_data.model_dump(exclude_unset=True)
    elif hasattr(utilisateur_data, "dict"):
        update_data = utilisateur_data.dict(exclude_unset=True)
    else:
        update_data = dict(utilisateur_data)

    update_data.pop("mot_de_passe", None)

    for key, value in update_data.items():
        if hasattr(db_utilisateur, key):
            setattr(db_utilisateur, key, value)

    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def delete_utilisateur(db: Session, utilisateur_id: int):
    """Supprime un utilisateur et ses données en cascade."""
    db_utilisateur = get_utilisateur(db, utilisateur_id)
    if not db_utilisateur:
        return None
    db.delete(db_utilisateur)
    db.commit()
    return db_utilisateur

# --- CRUD pour Ordonnance ---
def create_ordonnance_pour_utilisateur(db: Session, ordonnance: schemas.OrdonnanceCreate, utilisateur_id: int):
    """Crée une nouvelle ordonnance pour un utilisateur."""
    db_ordonnance = models.Ordonnance(**ordonnance.model_dump(), utilisateur_id=utilisateur_id)
    db.add(db_ordonnance)
    db.commit()
    db.refresh(db_ordonnance)
    return db_ordonnance

def get_ordonnances_par_utilisateur(db: Session, utilisateur_id: int, skip: int = 0, limit: int = 100):
    """Récupère toutes les ordonnances d'un utilisateur."""
    return db.query(models.Ordonnance).filter(models.Ordonnance.utilisateur_id == utilisateur_id).offset(skip).limit(limit).all()

def get_ordonnance(db: Session, ordonnance_id: int):
    """Récupère une ordonnance par son ID."""
    return db.query(models.Ordonnance).filter(models.Ordonnance.id == ordonnance_id).first()

def update_ordonnance(db: Session, ordonnance_id: int, ordonnance_data: schemas.OrdonnanceCreate):
    """Met à jour une ordonnance."""
    db_ordonnance = get_ordonnance(db, ordonnance_id)
    if not db_ordonnance:
        return None
    update_data = ordonnance_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ordonnance, key, value)
    db.commit()
    db.refresh(db_ordonnance)
    return db_ordonnance

def delete_ordonnance(db: Session, ordonnance_id: int):
    """Supprime une ordonnance."""
    db_ordonnance = get_ordonnance(db, ordonnance_id)
    if not db_ordonnance:
        return None
    db.delete(db_ordonnance)
    db.commit()
    return db_ordonnance

# --- CRUD pour Medicament ---
def create_ordonnance_with_meds(
    db: Session,
    utilisateur_id: int,
    valid_until: Optional[date],
    meds: List[dict],
):
    """
    Crée une ordonnance + médicaments liés.
    meds: [{"nom": str, "frequence": str}]
    """
    # Utiliser les modèles importés en haut du fichier
    ordon = models.Ordonnance( 
        utilisateur_id=utilisateur_id, 
        date_ordonnance=date.today(),
        nom="" 
        )
    db.add(ordon)
    db.flush()  # pour obtenir id

    for m in meds:
        # On s'assure que les champs essentiels sont présents
        if not m.get("nom") or not m.get("frequence"):
            continue
        
        # Créer le médicament avec tous les champs fournis
        db_medicament = models.Medicament(
            ordonnance_id=ordon.id,
            nom=m.get("nom"),
            frequence=m.get("frequence"),
            dose=m.get("dose"),
        )
        db.add(db_medicament)
    db.commit()
    db.refresh(ordon)
    return ordon

def get_medicaments_par_ordonnance(db: Session, ordonnance_id: int, skip: int = 0, limit: int = 100):
    """Récupère les médicaments d'une ordonnance."""
    return db.query(models.Medicament).filter(models.Medicament.ordonnance_id == ordonnance_id).offset(skip).limit(limit).all()

def get_medicament(db: Session, medicament_id: int):
    """Récupère un médicament par son ID."""
    return db.query(models.Medicament).filter(models.Medicament.id == medicament_id).first()

def update_medicament(db: Session, medicament_id: int, medicament_data: schemas.MedicamentCreate):
    """Met à jour un médicament."""
    db_medicament = get_medicament(db, medicament_id)
    if not db_medicament:
        return None
    update_data = medicament_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_medicament, key, value)
    db.commit()
    db.refresh(db_medicament)
    return db_medicament

def delete_medicament(db: Session, medicament_id: int):
    """Supprime un médicament."""
    db_medicament = get_medicament(db, medicament_id)
    if not db_medicament:
        return None
    db.delete(db_medicament)
    db.commit()
    return db_medicament

# --- CRUD pour Allergie ---
def create_allergie_pour_utilisateur(db: Session, allergie: schemas.AllergieCreate, utilisateur_id: int):
    """Crée une nouvelle allergie pour un utilisateur."""
    db_allergie = models.Allergie(
        utilisateur_id=utilisateur_id,
        nom=allergie.nom,
        description_allergie=(allergie.description or "")
    )
    db.add(db_allergie)
    db.commit()
    db.refresh(db_allergie)
    return db_allergie

def get_allergies_par_utilisateur(db: Session, utilisateur_id: int, skip: int = 0, limit: int = 100):
    """Récupère les allergies d'un utilisateur."""
    return db.query(models.Allergie).filter(models.Allergie.utilisateur_id == utilisateur_id).offset(skip).limit(limit).all()

def get_allergie(db: Session, allergie_id: int):
    """Récupère une allergie par son ID."""
    return db.query(models.Allergie).filter(models.Allergie.id == allergie_id).first()

def update_allergie(db: Session, allergie_id: int, allergie_data: schemas.AllergieCreate):
    """Met à jour une allergie."""
    db_allergie = get_allergie(db, allergie_id)
    if not db_allergie:
        return None
    if allergie_data.nom is not None:
        db_allergie.nom = allergie_data.nom
    if allergie_data.description is not None:
        db_allergie.description_allergie = allergie_data.description
    db.commit()
    db.refresh(db_allergie)
    return db_allergie

def delete_allergie(db: Session, allergie_id: int):
    """Supprime une allergie."""
    db_allergie = get_allergie(db, allergie_id)
    if not db_allergie:
        return None
    db.delete(db_allergie)
    db.commit()
    return db_allergie

# --- CRUD pour AntecedentMedical ---
def create_antecedent_pour_utilisateur(db: Session, antecedent: schemas.AntecedentMedicalCreate, utilisateur_id: int):
    db_antecedent = models.AntecedentMedical(
        utilisateur_id=utilisateur_id,
        nom=antecedent.nom,
        description=antecedent.description,
        date_diagnostic=antecedent.date_diagnostic,
        type=antecedent.type
    )
    db.add(db_antecedent)
    db.commit()
    db.refresh(db_antecedent)
    return db_antecedent

def get_antecedents_par_utilisateur(db: Session, utilisateur_id: int, skip: int = 0, limit: int = 100):
    """Récupère les antécédents d'un utilisateur."""
    return db.query(models.AntecedentMedical).filter(models.AntecedentMedical.utilisateur_id == utilisateur_id).offset(skip).limit(limit).all()

def delete_antecedent(db: Session, antecedent_id: int):
    """Supprime un antécédent."""
    row = db.query(models.AntecedentMedical).filter(models.AntecedentMedical.id == antecedent_id).first()
    if not row:
        return None
    db.delete(row)
    db.commit()
    return row

# --- Utilitaires Auth ---
def create_utilisateur_simple(db: Session, email: str, mot_de_passe: str, role: str = "utilisateur"):
    """Crée un utilisateur avec seulement email et mot de passe."""
    from datetime import date
    import sys
    import os
    
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from models.utilisateur import Utilisateur
    
    hashed_password = get_password_hash(mot_de_passe)
    db_utilisateur = Utilisateur(
        email=email,
        mot_de_passe=hashed_password,
        nom="",
        prenom="",
        date_naissance=date.today(),
        numero_telephone=None,
        role=role,
        sexe=""
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def update_utilisateur_password(db: Session, utilisateur_id: int, hashed_password: str):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not user:
        return None
    user.mot_de_passe = hashed_password
    db.commit()
    db.refresh(user)
    return user

# --- CRUD pour Event ---

def create_event(db: Session, utilisateur_id: int, payload: EventCreate) -> models.Event:
    ev = models.Event(
        utilisateur_id=utilisateur_id,
        title=payload.title,
        description=payload.description,
        start_dt=payload.start_dt,
        end_dt=payload.end_dt,
        timezone=payload.timezone,
        location=payload.location,
        done=payload.done, 
    )
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

def list_events_for_user(db: Session, utilisateur_id: int):
    return db.query(models.Event).filter(models.Event.utilisateur_id == utilisateur_id).order_by(models.Event.start_dt.asc()).all()

def delete_event(db: Session, utilisateur_id: int, event_id: int) -> bool:
    ev = db.query(models.Event).filter(models.Event.id == event_id, models.Event.utilisateur_id == utilisateur_id).first()
    if not ev:
        return False
    db.delete(ev); db.commit()
    return True

def update_event_done(db: Session, utilisateur_id: int, event_id: int, done: bool) -> Optional[models.Event]:
    ev = db.query(models.Event).filter(
        models.Event.id == event_id,
        models.Event.utilisateur_id == utilisateur_id
    ).first()
    if not ev:
        return None
    ev.done = done
    db.commit()
    db.refresh(ev)
    return ev

def update_utilisateur_password(db: Session, utilisateur_id: int, hashed_password: str):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not user:
        return None
    user.mot_de_passe = hashed_password
    db.commit()
    db.refresh(user)
    return user

def create_conversation(db: Session, utilisateur_id: int, titre: str):
    """Créer une nouvelle conversation"""
    from models import Conversation
    db_conversation = Conversation(
        utilisateur_id=utilisateur_id,
        titre=titre,
        date_creation=datetime.utcnow(),
        date_derniere_activite=datetime.utcnow()
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def get_conversations_by_user(db: Session, user_id: int):
    return db.query(models.Conversation).filter(models.Conversation.utilisateur_id == user_id).order_by(models.Conversation.date_derniere_activite.desc()).all()

def get_conversation_by_id(db: Session, conversation_id: int, user_id: int):
    return db.query(models.Conversation).options(
        joinedload(models.Conversation.messages)
    ).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.utilisateur_id == user_id
    ).first()

def update_conversation_title(db: Session, conversation_id: int, user_id: int, new_title: str):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.utilisateur_id == user_id
    ).first()
    
    if conversation:
        conversation.titre = new_title
        db.commit()
        db.refresh(conversation)
    return conversation

def add_message_to_conversation(db: Session, conversation_id: int, role: str, contenu: str):
    """Ajouter un message à une conversation et mettre à jour la date d'activité."""
    from models import Message, Conversation
    
    # Ajouter le message
    db_message = Message(
        conversation_id=conversation_id,
        role=role,
        contenu=contenu,
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    
    # Mettre à jour la date de dernière activité de la conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.date_derniere_activite = datetime.utcnow()
        
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_conversation(db: Session, conversation_id: int, utilisateur_id: int):
    """Supprimer une conversation"""
    from models import Conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.utilisateur_id == utilisateur_id
    ).first()
    
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False
