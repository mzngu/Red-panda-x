from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Ordonnance(Base):
    __tablename__ = 'ordonnance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateur.id'), nullable=False)
    nom = Column(String, nullable=True, default="")
    date_ordonnance = Column(Date, nullable=False)
   
    utilisateur = relationship("Utilisateur", back_populates="ordonnances")
    medicaments = relationship("Medicament", back_populates="ordonnance", cascade="all, delete")
