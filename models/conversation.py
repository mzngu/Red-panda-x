from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Conversation(Base):
    __tablename__ = "conversation"
    
    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    titre = Column(String, nullable=False)
    date_creation = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_derniere_activite = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    utilisateur = relationship("Utilisateur", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")