from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class AntecedentMedical(Base):
    __tablename__ = "antecedent_medical"
    
    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    nom = Column(String)
    description = Column(String)
    date_diagnostic = Column(Date)
    type = Column(String, nullable=False, default="maladie")
    
    # Relation
    utilisateur = relationship("Utilisateur", back_populates="antecedents")
