from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Medicament(Base):
    __tablename__ = 'medicaments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ordonnance_id = Column(Integer, ForeignKey('ordonnance.id'), nullable=False)
    nom = Column(String, nullable=True, default="")
    description_medicaments = Column(Text, nullable=True, default="")
    dose = Column(String, nullable=True, default="")
    composant = Column(String, nullable=True, default="")
    frequence = Column(String, nullable=True, default="")  # Ajout pour ordo_extract.py

    ordonnance = relationship("Ordonnance", back_populates="medicaments")