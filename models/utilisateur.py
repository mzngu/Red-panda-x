from sqlalchemy import Column, Integer, String, Date, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base
from datetime import date

class Utilisateur(Base):
    __tablename__ = 'utilisateur'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=True, default="")  
    prenom = Column(String, nullable=True, default="") 
    date_naissance = Column(Date, nullable=True, default=date.today)  
    email = Column(String, nullable=False, unique=True)
    mot_de_passe = Column(String, nullable=False)
    numero_telephone = Column(String, nullable=True)
    role = Column(String, nullable=False, default='utilisateur')
    avatar = Column(String, nullable=True, default="normal") 
    sexe = Column(String, nullable=True, default="") 

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'utilisateur')", name='check_role'),
    )

    ordonnances = relationship("Ordonnance", back_populates="utilisateur", cascade="all, delete")
    allergies = relationship("Allergie", back_populates="utilisateur", cascade="all, delete")
    antecedents = relationship("AntecedentMedical", back_populates="utilisateur", cascade="all, delete")
    events = relationship("Event", back_populates="utilisateur", cascade="all, delete-orphan")

    conversations = relationship("Conversation", back_populates="utilisateur", cascade="all, delete")  # Ajout
