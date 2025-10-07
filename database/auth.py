# //TIFFANY//

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Cookie
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from . import controller as crud
from .database import get_db
import time


load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # A CHANGER
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration du hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide",
                )
            return user_id
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide",
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = crud.get_utilisateur_by_email(db, email=email)
        if not user:
            return False
        if not AuthService.verify_password(password, user.mot_de_passe):
            return False
        return user

    @staticmethod
    def verify_access_token(token: str, secret_key: str, algorithm: str):
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            # Vérifie l'expiration
            if payload.get("exp") and int(time.time()) > payload["exp"]:
                return None
            return payload
        except JWTError:
            return None


# Dépendance pour récupérer l'utilisateur actuel
def get_current_user(
    session_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non authentifié",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not session_token:
        raise credentials_exception
    
    try:
        user_id = AuthService.verify_token(session_token)
        user = crud.get_utilisateur(db, utilisateur_id=user_id)
        if user is None:
            raise credentials_exception
        return user
    except HTTPException:
        raise credentials_exception

# Dépendance optionnelle pour récupérer l'utilisateur (peut être None)
def get_current_user_optional(
    session_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    if not session_token:
        return None
    
    try:
        user_id = AuthService.verify_token(session_token)
        user = crud.get_utilisateur(db, utilisateur_id=user_id)
        return user
    except:
        return None