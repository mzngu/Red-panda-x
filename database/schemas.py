from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime

# --- Schémas Utilisateur ---

class UtilisateurBase(BaseModel):
    email: EmailStr
    nom: Optional[str] = ""
    prenom: Optional[str] = ""
    date_naissance: Optional[date] = None
    numero_telephone: Optional[str] = None
    role: str = "utilisateur"
    sexe : Optional[str] = ""

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

class UtilisateurUpdate(UtilisateurBase):
    email: EmailStr
    mot_de_passe: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[date] = None
    numero_telephone: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None  
    sexe : Optional[str] = None

class Utilisateur(UtilisateurBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schémas Ordonnance ---

class OrdonnanceBase(BaseModel):
    nom: str
    lieu: Optional[str] = None
    date: date
    details: Optional[str] = None
    nom_docteur: str
    type_docteur: str

class OrdonnanceCreate(OrdonnanceBase):
    pass

class OrdonnanceUpdate(OrdonnanceBase):
    nom: Optional[str] = None
    date: Optional[date] = None
    nom_docteur: Optional[str] = None
    type_docteur: Optional[str] = None

class Ordonnance(OrdonnanceBase):
    id: int
    utilisateur_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schémas Medicament ---

class MedicamentBase(BaseModel):
    nom: str
    description: Optional[str] = None
    dose: Optional[str] = None
    composant: Optional[str] = None

class MedicamentCreate(MedicamentBase):
    pass

class MedicamentUpdate(MedicamentBase):
    nom: Optional[str] = None

class Medicament(MedicamentBase):
    id: int
    ordonnance_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schémas Allergie ---

class AllergieBase(BaseModel):
    nom: str
    description: Optional[str] = None  # sera mappé vers description_allergie côté modèle

class AllergieCreate(AllergieBase):
    pass

class AllergieUpdate(AllergieBase):
    nom: Optional[str] = None

class Allergie(AllergieBase):
    id: int
    utilisateur_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schémas Antecedent Médical ---

class AntecedentMedicalBase(BaseModel):
    nom: str
    description: Optional[str] = None
    date_diagnostic: Optional[date] = None

class AntecedentMedicalCreate(BaseModel):
    nom: str
    description: Optional[str] = ""
    date_diagnostic: Optional[datetime] = None
    type: str = "maladie"  # Valeur par défaut

class AntecedentMedical(BaseModel):
    id: int
    nom: str
    description: Optional[str] = ""
    date_diagnostic: Optional[datetime] = None
    type: str
    utilisateur_id: int

    class Config:
        from_attributes = True

# --- Schémas d'authentification ---

class LoginRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str

class LoginResponse(BaseModel):
    message: str
    user: Utilisateur

class RegisterRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str
    role: str = "utilisateur"

class LogoutResponse(BaseModel):
    message: str

# --- Schémas d'events ---

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_dt: datetime
    end_dt: datetime
    timezone: str = "Europe/Paris"
    location: Optional[str] = None
    done: bool = False 

class EventOut(EventCreate):
    id: int
    class Config:
        from_attributes = True

# --- Schémas de Messagerie ---

class MessageBase(BaseModel):
    role: str
    contenu: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    titre: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    utilisateur_id: int
    date_creation: datetime
    date_derniere_activite: datetime
    messages: List[Message] = []
    
    class Config:
        from_attributes = True
