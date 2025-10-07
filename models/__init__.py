from .base import Base
from .utilisateur import Utilisateur
from .ordonnance import Ordonnance
from .medicament import Medicament
from .allergie import Allergie
from .antecedent import AntecedentMedical
from .event import Event

from .conversation import Conversation  # Ajout
from .message import Message  # Ajout
from .event import Event 


__all__ = [
    "Base",
    "Utilisateur",
    "Ordonnance",
    "Medicament",
    "Allergie",
    "AntecedentMedical",
    "Event",
    "Conversation",
    "Message",
]