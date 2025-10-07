from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)

    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    start_dt = Column(DateTime, nullable=False)
    end_dt = Column(DateTime, nullable=False)
    timezone = Column(String(64), default="Europe/Paris")
    location = Column(String(255), nullable=True)
    done = Column(Boolean, nullable=False, default=False)

    utilisateur = relationship("Utilisateur", back_populates="events")
