from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Allergie(Base):
    __tablename__ = 'allergies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateur.id'), nullable=False)
    nom = Column(String, nullable=True, default="")
    description_allergie = Column(Text, nullable=True, default="")

    utilisateur = relationship("Utilisateur", back_populates="allergies")
