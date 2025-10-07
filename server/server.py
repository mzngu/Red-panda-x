import asyncio
import json
import websockets
import sys
import os
import base64
import logging
import smtplib
import ssl
import uuid
import time
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime, timedelta
from urllib.parse import unquote
from threading import Thread
from typing import List, Optional
import uvicorn
import re


from fastapi import FastAPI, Depends, HTTPException, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

# Routes modulaires
from server.routes import ordonnances, calendar

# ── Chemin projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Services / DB / Auth
from services.service import generate_response, generate_response_with_tools, system_instruction
from database.database import bootstrap_database, init_db, get_db, SessionLocal
from services.ordo_extract import extract_meds
from database.auth import AuthService, get_current_user, get_current_user_optional
import database.controller as crud
from database.controller import create_ordonnance_with_meds
import database.schemas as schemas
import models

# ──────────────────────────────────────────────────────────────────────────────
# Config & init
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv(override=True)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4321")
SMTP_HOST    = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT    = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER    = os.getenv("SMTP_USER", "")
SMTP_PASS    = os.getenv("SMTP_PASS", "")
SMTP_FROM    = os.getenv("SMTP_FROM", "no-reply@dontpanic.local")

JWT_SECRET   = os.getenv("JWT_SECRET", "change-me")
JWT_ALG      = os.getenv("JWT_ALGORITHM", "HS256")

HOST = os.getenv("HOST", "0.0.0.0")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "8090"))
FASTAPI_PORT   = int(os.getenv("FASTAPI_PORT", "8080"))

# Stockage in-memory par socket
conversations = {}
_consumed_jti = set()

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sorrel API",
    description="API pour la gestion des données médicales des utilisateurs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.include_router(ordonnances.router)
app.include_router(calendar.router)

# ──────────────────────────────────────────────────────────────────────────────
# Utils
# ──────────────────────────────────────────────────────────────────────────────
def _get_cookie_from_headers(headers: dict, name: str) -> str | None:
    cookie_header = headers.get("cookie") or headers.get("Cookie") or ""
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == name and v:
            return unquote(v)
    return None

def _filled(x) -> bool:
    return x is not None and str(x).strip() != ""

def compute_is_profile_complete(user) -> bool:
    return all([
        _filled(getattr(user, "nom", None)),
        _filled(getattr(user, "prenom", None)),
        _filled(getattr(user, "numero_telephone", None)),
        _filled(getattr(user, "sexe", None)),
    ])

def _mask(tok: str) -> str:
    if not tok:
        return "None"
    return tok[:10] + "...(len=" + str(len(tok)) + ")"

def _build_front_url(path: str) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/{path.lstrip('/')}"

# ──────────────────────────────────────────────────────────────────────────────
# Mail: lien sécurisé (reset / magic-link)
# ──────────────────────────────────────────────────────────────────────────────
class SecureLinkRequest(BaseModel):
    email: EmailStr
    path: str = "/home/home"
    login: bool = False

def _send_email_link(to_email: str, link: str):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 Réinitialisation de votre mot de passe"
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2c3e50;">Bonjour,</h2>
            <p>Vous avez demandé à réinitialiser votre mot de passe.</p>
            <p>Cliquez sur le bouton ci-dessous pour accéder au lien sécurisé :</p>
            <p style="text-align: center; margin: 30px;">
              <a href="{link}" style="background-color: #4CAF50; 
                                       color: white; 
                                       padding: 12px 20px; 
                                       text-decoration: none; 
                                       border-radius: 5px;">
                Réinitialiser mon mot de passe
              </a>
            </p>
            <p>⚠️ Ce lien est valable <b>15 minutes</b> uniquement.</p>
            <p>Si vous n’êtes pas à l’origine de cette demande, ignorez cet email.</p>
            <br>
            <p style="font-size: 12px; color: #777;">L'équipe Don't Panic 🚀</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        print(f"✅ Mail envoyé à {to_email}")
    except Exception as e:
        print(f"❌ Erreur envoi mail : {e}")


@app.post("/mail/send-secure-link", tags=["Mail"])
async def send_secure_link(payload: SecureLinkRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    user = crud.get_utilisateur_by_email(db, email=payload.email)
    user_id = str(user.id) if user else "anonymous"

    jti = str(uuid.uuid4())
    token = jwt.encode(
        {
            "sub": user_id,
            "purpose": "magic-link",
            "jti": jti,
            "path": payload.path,
            "login": payload.login,
            "exp": int(time.time()) + 15 * 60
        },
        JWT_SECRET,
        algorithm=JWT_ALG,
    )

    reset_url = f"{FRONTEND_URL}/reset-password/reset-password?token={token}"
    background.add_task(_send_email_link, payload.email, reset_url)
    return {"ok": True}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.post("/auth/reset-password", tags=["Authentication"])
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = AuthService.verify_access_token(data.token, JWT_SECRET, JWT_ALG)
    if not payload or payload.get("purpose") != "magic-link":
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")

    user_id = payload.get("sub")
    if not user_id or user_id == "anonymous":
        raise HTTPException(status_code=400, detail="Utilisateur introuvable")

    user = crud.get_utilisateur(db, utilisateur_id=int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    hashed = AuthService.get_password_hash(data.new_password)
    crud.update_utilisateur_password(db, utilisateur_id=user.id, hashed_password=hashed)

    return {"message": "Mot de passe réinitialisé avec succès"}

# ──────────────────────────────────────────────────────────────────────────────
# Auth routes
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/auth/register", tags=["Authentication"])
async def register(user_data: schemas.RegisterRequest, response: Response, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_utilisateur_by_email(db, email=user_data.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Un compte avec cet email existe déjà")

        new_user = crud.create_utilisateur_simple(
            db=db,
            email=user_data.email,
            mot_de_passe=user_data.mot_de_passe,
            role=user_data.role
        )

        access_token = AuthService.create_access_token(
            data={"sub": str(new_user.id)},
            expires_delta=timedelta(days=7)
        )
        response.set_cookie(
            key="session_token", value=access_token, httponly=True,
            secure=False, samesite="lax", max_age=7 * 24 * 60 * 60
        )
        return {
            "message": "Inscription réussie",
            "user": {"id": new_user.id, "email": new_user.email, "role": new_user.role}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.post("/auth/login", tags=["Authentication"])
async def login(login_data: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = AuthService.authenticate_user(db, login_data.email, login_data.mot_de_passe)
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

        access_token = AuthService.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=7)
        )
        response.set_cookie(
            key="session_token", value=access_token, httponly=True,
            secure=False, samesite="lax", max_age=7 * 24 * 60 * 60
        )
        return {"message": "Connexion réussie", "user": {"id": user.id, "email": user.email, "role": user.role}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.post("/auth/logout", tags=["Authentication"])
async def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Déconnexion réussie"}

@app.get("/auth/consume-link", tags=["Authentication"])
async def consume_link(token: str, response: Response):
    fallback_ok = _build_front_url("/verified")
    fallback_err = _build_front_url("/verify-error")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        if payload.get("purpose") != "magic-link":
            return RedirectResponse(fallback_err, status_code=302)

        jti = payload.get("jti")
        if not jti or jti in _consumed_jti:
            return RedirectResponse(fallback_err, status_code=302)
        _consumed_jti.add(jti)

        safe_target = _build_front_url(payload.get("path") or "/")
        resp = RedirectResponse(safe_target, status_code=302)

        if payload.get("login") and payload.get("sub") and payload.get("sub") != "anonymous":
            access_token = AuthService.create_access_token(
                data={"sub": payload["sub"]},
                expires_delta=timedelta(days=7)
            )
            resp.set_cookie(
                key="session_token", value=access_token, httponly=True,
                secure=False, samesite="lax", max_age=7 * 24 * 60 * 60
            )

        return resp
    except JWTError:
        return RedirectResponse(fallback_err, status_code=302)
    except Exception as e:
        print(f"Erreur consume_link : {e}")
        return RedirectResponse(fallback_err, status_code=302)

@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    is_complete = compute_is_profile_complete(current_user)

    allergies = []
    antecedents = []
    try:
        allergies_rows = crud.get_allergies_par_utilisateur(db, current_user.id)
        allergies = [{"id": a.id, "nom": a.nom or ""} for a in allergies_rows]
        antecedent_rows = crud.get_antecedents_par_utilisateur(db, current_user.id)
        antecedents = [{"id": m.id, "nom": m.nom or ""} for m in antecedent_rows]
    except Exception:
        pass

    return {
        "id": current_user.id,
        "email": current_user.email,
        "nom": current_user.nom or "",
        "prenom": current_user.prenom or "",
        "date_naissance": current_user.date_naissance.isoformat() if current_user.date_naissance else None,
        "numero_telephone": current_user.numero_telephone,
        "role": current_user.role,
        "avatar": current_user.avatar or "normal",
        "isProfileComplete": is_complete,
        "sexe": current_user.sexe,
        "allergies": allergies,
        "antecedents": antecedents,
    }

@app.get("/auth/check", tags=["Authentication"])
async def check_auth(current_user = Depends(get_current_user_optional)):
    if not current_user:
        return {"authenticated": False, "user": None}
    is_complete = compute_is_profile_complete(current_user)
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "nom": current_user.nom or "",
            "prenom": current_user.prenom or "",
            "date_naissance": current_user.date_naissance.isoformat() if current_user.date_naissance else None,
            "numero_telephone": current_user.numero_telephone,
            "role": current_user.role,
            "avatar": current_user.avatar or "normal",
            "isProfileComplete": is_complete,
            "sexe": current_user.sexe,
        }
    }

# ──────────────────────────────────────────────────────────────────────────────
# Utilisateurs / Allergies / Antécédents
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/utilisateurs/", tags=["Utilisateurs"])
def create_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    db_utilisateur = crud.get_utilisateur_by_email(db, email=utilisateur.email)
    if db_utilisateur:
        raise HTTPException(status_code=400, detail="Cet email est déjà enregistré.")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.get("/utilisateurs/", tags=["Utilisateurs"])
def read_utilisateurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    return crud.get_utilisateurs(db, skip=skip, limit=limit)

@app.put("/utilisateurs/{utilisateur_id}", tags=["Utilisateurs"])
def update_utilisateur(utilisateur_id: int, utilisateur: schemas.UtilisateurUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    try:
        data = utilisateur.model_dump(exclude_unset=True)
        new_pw = data.pop("mot_de_passe", None)
        if new_pw:
            hashed = AuthService.get_password_hash(new_pw)
            crud.update_utilisateur_password(db, utilisateur_id=utilisateur_id, hashed_password=hashed)
        db_utilisateur = crud.update_utilisateur(db=db, utilisateur_id=utilisateur_id, utilisateur_data=data)
        if db_utilisateur is None:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return {
            "id": db_utilisateur.id,
            "email": db_utilisateur.email,
            "nom": db_utilisateur.nom or "",
            "prenom": db_utilisateur.prenom or "",
            "date_naissance": db_utilisateur.date_naissance.isoformat() if db_utilisateur.date_naissance else None,
            "numero_telephone": db_utilisateur.numero_telephone,
            "role": db_utilisateur.role,
            "avatar": db_utilisateur.avatar,
            "sexe": db_utilisateur.sexe or ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/utilisateurs/{utilisateur_id}", tags=["Utilisateurs"])
def read_utilisateur(utilisateur_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    return {
        "id": db_utilisateur.id,
        "email": db_utilisateur.email,
        "nom": db_utilisateur.nom or "",
        "prenom": db_utilisateur.prenom or "",
        "date_naissance": db_utilisateur.date_naissance.isoformat() if db_utilisateur.date_naissance else None,
        "numero_telephone": db_utilisateur.numero_telephone,
        "role": db_utilisateur.role,
        "sexe": db_utilisateur.sexe or "",
    }

# Allergies
@app.get("/utilisateurs/{utilisateur_id}/allergies", tags=["Allergies"])
def list_allergies(utilisateur_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    rows = crud.get_allergies_par_utilisateur(db, utilisateur_id)
    return [{"id": a.id, "nom": a.nom or "", "description": a.description_allergie or ""} for a in rows]

@app.post("/utilisateurs/{utilisateur_id}/allergies", tags=["Allergies"])
def add_allergie(utilisateur_id: int, payload: schemas.AllergieCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    row = crud.create_allergie_pour_utilisateur(db, payload, utilisateur_id)
    return {"id": row.id, "nom": row.nom or "", "description": row.description_allergie or ""}

@app.delete("/utilisateurs/{utilisateur_id}/allergies/{allergie_id}", tags=["Allergies"])
def delete_allergie(utilisateur_id: int, allergie_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    row = crud.get_allergie(db, allergie_id)
    if not row or row.utilisateur_id != utilisateur_id:
        raise HTTPException(status_code=404, detail="Allergie introuvable")
    crud.delete_allergie(db, allergie_id)
    return {"ok": True}

# Antécédents
@app.get("/utilisateurs/{utilisateur_id}/antecedents", tags=["Antecedents"])
def list_antecedents(utilisateur_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    rows = crud.get_antecedents_par_utilisateur(db, utilisateur_id)
    return [{
        "id": r.id,
        "nom": r.nom or "",
        "description": r.description or "",
        "date_diagnostic": (r.date_diagnostic.isoformat() if r.date_diagnostic else None),
        "type": r.type or ""
    } for r in rows]

@app.post("/utilisateurs/{utilisateur_id}/antecedents", tags=["Antecedents"])
def add_antecedent(utilisateur_id: int, payload: schemas.AntecedentMedicalCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    row = crud.create_antecedent_pour_utilisateur(db, payload, utilisateur_id)
    return {
        "id": row.id,
        "nom": row.nom or "",
        "description": row.description or "",
        "date_diagnostic": (row.date_diagnostic.isoformat() if row.date_diagnostic else None),
        "type": row.type or ""
    }

@app.delete("/utilisateurs/{utilisateur_id}/antecedents/{antecedent_id}", tags=["Antecedents"])
def delete_antecedent(utilisateur_id: int, antecedent_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.id != utilisateur_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    row = db.query(models.AntecedentMedical).filter(models.AntecedentMedical.id == antecedent_id).first()
    if not row or row.utilisateur_id != utilisateur_id:
        raise HTTPException(status_code=404, detail="Antécédent introuvable")
    db.delete(row); db.commit()
    return {"ok": True}

# ──────────────────────────────────────────────────────────────────────────────
# Conversations (CRUD)
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/conversations/", tags=["Conversations"])
async def create_conversation(data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    titre = data.get("titre", "Nouvelle conversation")
    conversation = crud.create_conversation(db, current_user.id, titre)
    return {
        "id": conversation.id,
        "titre": conversation.titre,
        "date_creation": conversation.date_creation.isoformat(),
        "date_derniere_activite": conversation.date_derniere_activite.isoformat()
    }

@app.get("/conversations/", tags=["Conversations"])
async def get_user_conversations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    convs = crud.get_conversations_by_user(db, current_user.id)
    return [
        {
            "id": conv.id,
            "titre": conv.titre,
            "date_creation": conv.date_creation.isoformat(),
            "date_derniere_activite": conv.date_derniere_activite.isoformat(),
            "nb_messages": len(conv.messages) if hasattr(conv, 'messages') else 0
        }
        for conv in convs
    ]

@app.get("/conversations/{conversation_id}", tags=["Conversations"])
async def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conversation = crud.get_conversation_by_id(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conversation.id,
        "titre": conversation.titre,
        "date_creation": conversation.date_creation.isoformat(),
        "date_derniere_activite": conversation.date_derniere_activite.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "contenu": msg.contenu,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in conversation.messages
        ]
    }

@app.put("/conversations/{conversation_id}", tags=["Conversations"])
async def update_conversation(conversation_id: int, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conversation = crud.update_conversation_title(db, conversation_id, current_user.id, data["titre"])
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return {
        "id": conversation.id,
        "titre": conversation.titre,
        "date_creation": conversation.date_creation.isoformat(),
        "date_derniere_activite": conversation.date_derniere_activite.isoformat()
    }

@app.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    success = crud.delete_conversation(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return {"message": "Conversation supprimée avec succès"}

@app.on_event("startup")
def _startup_db():
    # Attend que Postgres soit prêt, crée la DB si besoin, puis crée les tables
    bootstrap_database()
    init_db()

# ──────────────────────────────────────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API Sorrel"}

# ──────────────────────────────────────────────────────────────────────────────
# WebSocket
# ──────────────────────────────────────────────────────────────────────────────
async def handle_client(websocket):
    global current_system_instruction
    headers = dict(websocket.request.headers)
    ws_session_token = _get_cookie_from_headers(headers, "session_token")

    client_id = id(websocket)
    conversations[client_id] = {"history": [], "conversation_id": None, "user_id": None}

    try:
        print(f"✅ Connexion WS client_id={client_id}")
        await websocket.send(json.dumps({"response": "✅ Connexion WebSocket établie"}))

        async for message in websocket:
            print(f"📩 Reçu brut: {message}")
            db = next(get_db())
            try:
                data = json.loads(message)

                # Chargement d'historique optionnel
                if data.get("action") == "load_history":
                    conversations[client_id]["history"] = data.get("history", [])
                    print(f"Client {client_id}: Historique chargé ({len(conversations[client_id]['history'])} messages)")
                    continue

                user_message   = data.get("message", "")
                image_data_url = data.get("image")
                user_context   = data.get("context")
                conversation_id = data.get("conversation_id")
                user_id         = data.get("user_id")

                token_to_use = ws_session_token or data.get("session_token")
                if not token_to_use:
                    await websocket.send(json.dumps({"error": "Non authentifié (aucun session_token)."}))
                    continue

                # Mémoriser conv/user pour cette session
                conversations[client_id]["conversation_id"] = conversation_id
                conversations[client_id]["user_id"] = user_id

                # Construire system prompt
                today_str = datetime.now().strftime("%d/%m/%Y")
                current_system_instruction = system_instruction

                if user_context:
                    context_parts = ["Voici des informations sur l'utilisateur actuel :"]
                    if user_context.get("prenom"):
                        context_parts.append(f"- Prénom: {user_context['prenom']}")
                    if user_context.get("nom"):
                        context_parts.append(f"- Nom: {user_context['nom']}")
                    if user_context.get("sexe"):
                        context_parts.append(f"- Sexe: {user_context['sexe']}")
                    if user_context.get("date_naissance"):
                        try:
                            birth_date = datetime.fromisoformat(user_context['date_naissance'].split('T')[0])
                            age = (datetime.now() - birth_date).days // 365
                            context_parts.append(f"- Âge: {age} ans (né(e) le {birth_date.strftime('%d/%m/%Y')})")
                        except Exception:
                            pass
                    if user_context.get("allergies"):
                        allergies_str = ", ".join([a.get('nom', '') for a in user_context['allergies'] if a.get('nom')])
                        if allergies_str:
                            context_parts.append(f"- Allergies connues: {allergies_str}")
                    if user_context.get("antecedents"):
                        antecedents_str = ", ".join([a.get('nom', '') for a in user_context['antecedents'] if a.get('nom')])
                        if antecedents_str:
                            context_parts.append(f"- Antécédents médicaux: {antecedents_str}")
                    if len(context_parts) > 1:
                        current_system_instruction += "\n\n" + "\n".join(context_parts)
                        current_system_instruction += "\n\nBase tes réponses sur ces infos."

                current_system_instruction += f"""
Aujourd'hui on est le {today_str}
Capacités d’action calendrier :
- Utilise addEvent(title, description?, start_dt RFC3339, end_dt RFC3339, timezone="Europe/Paris", location?)
- Utilise listEvents() pour voir les événements.
- Utilise deleteEvent(id) pour supprimer un rendez-vous.
"""

                # Contenu utilisateur
                user_parts = []
                if user_message:
                    user_parts.append(user_message)
                if image_data_url:
                    try:
                        header, encoded = image_data_url.split(",", 1)
                        image_data = base64.b64decode(encoded)
                        image = Image.open(BytesIO(image_data))
                        user_parts.append(image)

                    except Exception as e:
                        print(f"Erreur traitement image: {e}")
        
                # Historique + persistance message user
                conversations[client_id]["history"].append({"role": "user", "parts": user_parts})
                if conversation_id and user_message:
                    crud.add_message_to_conversation(db, conversation_id, "user", user_message)

                # Génération (avec outils puis fallback)
                try:
                    response_text = generate_response_with_tools(
                        prompt_parts=user_parts,
                        system_instruction_update=current_system_instruction,
                        session_token=token_to_use
                    )
                except Exception:
                    response_text = generate_response(conversations[client_id]["history"], current_system_instruction)

                # NOUVELLE LOGIQUE : Extraire les médicaments de la réponse du LLM
                final_response_to_user = response_text
                try:
                    # Le LLM peut renvoyer du markdown (```json ... ```)
                    json_match = re.search(r'```json\s*([\s\S]+?)\s*```', response_text)
                    if json_match:
                        clean_json_str = json_match.group(1)
                        response_data = json.loads(clean_json_str)
                        
                        meds_from_llm = response_data.get("medicaments")
                        
                        if meds_from_llm and isinstance(meds_from_llm, list):
                            for med in meds_from_llm:
                                if 'dose' not in med:
                                    med['dose'] = None

                            db_session = SessionLocal()
                            try:
                                create_ordonnance_with_meds(
                                    db=db_session,
                                    utilisateur_id=user_id,
                                    meds=meds_from_llm,
                                    valid_until=None
                                )
                                db_session.commit()
                                print(f"✅ Ordonnance sauvegardée pour user {user_id} via LLM.")
                                
                                # Formatter la réponse pour l'utilisateur
                                med_list_str = "\n".join([f"- {med['nom']} ({med.get('frequence', 'fréquence non spécifiée')})" for med in meds_from_llm])
                                final_response_to_user = response_data.get("reponse_textuelle", "J'ai sauvegardé votre ordonnance.") + "\n" + med_list_str

                            except Exception as e:
                                db_session.rollback()
                                print(f"Erreur sauvegarde ordonnance depuis LLM: {e}")
                            finally:
                                db_session.close()
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Réponse du LLM n'était pas un JSON valide: {e}")
                    # On envoie la réponse texte brute du LLM

                # Historique + persistance assistant
                conversations[client_id]["history"].append({"role": "model", "parts": [final_response_to_user]})
                if conversation_id:
                    crud.add_message_to_conversation(db, conversation_id, "assistant", final_response_to_user)

                await websocket.send(json.dumps({
                    "response": final_response_to_user,
                    "conversation_id": conversation_id
                }))

                # --- FIN TRAITEMENT MESSAGE ---

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Format JSON invalide"}))
            except Exception as e:
                logging.exception("❌ Erreur traitement WS")
                await websocket.send(json.dumps({"error": "Une erreur est survenue"}))
            finally:
                db.close()
    finally:
        conversations.pop(client_id, None)
        print(f"🛑 Déconnexion WebSocket client_id={client_id}")

# ──────────────────────────────────────────────────────────────────────────────
# Launchers
# ──────────────────────────────────────────────────────────────────────────────
async def start_websocket_server():
    allowed_origins = [
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "http://frontend:4321", 
    ]
    async with websockets.serve(handle_client, HOST, WEBSOCKET_PORT, origins=allowed_origins):
        print(f"🚀 Serveur WebSocket démarré sur {HOST}:{WEBSOCKET_PORT}")
        await asyncio.Future()

def start_fastapi_server():
    uvicorn.run(app, host=HOST, port=FASTAPI_PORT, log_level="info")

async def main():
    try:
        print("🔧 Bootstrap base de données...")
        from database.database import bootstrap_database
        bootstrap_database()
        init_db()
        print("✅ Base de données initialisée et prête!")

        fastapi_thread = Thread(target=start_fastapi_server, daemon=True)
        fastapi_thread.start()

        print(f"🚀 Serveur FastAPI démarré sur {HOST}:{FASTAPI_PORT}")
        print(f"📖 Documentation API disponible sur http://{HOST}:{FASTAPI_PORT}/docs")

        await start_websocket_server()
    except Exception as e:
        logging.error(f"Erreur lors du démarrage du serveur: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)
