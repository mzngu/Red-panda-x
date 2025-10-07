from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time


# NEW: charger le .env de façon robuste, même si le CWD varie (VS Code, tests, etc.)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # charge le premier .env trouvé en remontant l’arborescence

# Import des modèles
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.base import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NEW: helper pour bools
def _as_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT_STR = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
SQLALCHEMY_ECHO = _as_bool(os.getenv("SQLALCHEMY_ECHO"), default=False)

# Valider que toutes les variables d'environnement nécessaires sont définies
if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    logger.critical("FATAL: Configuration de la base de données manquante. Veuillez définir les variables d'environnement DB_USER, DB_PASSWORD et DB_NAME.")
    raise ValueError("Configuration de la base de données manquante.")

# Analyser le port en toute sécurité
try:
    db_port = int(DB_PORT_STR)
except (ValueError, TypeError):
    logger.warning(f"Valeur DB_PORT invalide: '{DB_PORT_STR}'. Utilisation du port par défaut 5432.")
    db_port = 5432

def bootstrap_database(max_attempts: int = 60, delay: float = 1.0):
    """
    Attend que Postgres accepte les connexions TCP, puis crée la DB si besoin.
    Retry pour éviter les 'connection refused' au démarrage.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=db_port, user=DB_USER, password=DB_PASSWORD, database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
            if not cur.fetchone():
                logger.info(f"Création de la base '{DB_NAME}'…")
                cur.execute(f'CREATE DATABASE "{DB_NAME}"')
                logger.info(f"Base '{DB_NAME}' créée.")
            else:
                logger.info(f"La base '{DB_NAME}' existe déjà.")
            cur.close(); conn.close()
            logger.info("✅ Bootstrap DB OK")
            return
        except psycopg2.OperationalError as e:
            logger.warning(f"[try {attempt}/{max_attempts}] DB pas prête: {e}. Retry dans {delay}s…")
            time.sleep(delay)
        except Exception:
            logger.exception("Erreur inattendue pendant bootstrap DB")
            raise
    raise RuntimeError("La base n'est pas disponible après les retries.")


# Construire l'URL de la base de données
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{db_port}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Importe tous les modèles pour qu'ils soient enregistrés dans Base
    from models import utilisateur, ordonnance, medicament, allergie, antecedent
    logging.info("Création des tables si non existantes…")
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
