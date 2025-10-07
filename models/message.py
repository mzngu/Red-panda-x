from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id"), nullable=False)
    role = Column(String, nullable=False)
    contenu = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relation
    conversation = relationship("Conversation", back_populates="messages")