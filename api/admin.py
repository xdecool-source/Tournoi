"""
Protocole HTTP
POST    /inscription             -> créer
PUT     /inscription/{licence}   -> modifier
DELETE  /inscription/{licence}   -> supprimer
GET     /inscription/{licence}   -> consulter
GET     /inscriptions            -> liste

Gère l'authentification administrateur (mot de passe, JWT, sessions).
GET  /me 
POST /login-admin 
POST /logout-admin

"""


from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import ExpiredSignatureError, JWTError, jwt
from core.config import ADMIN_PASS_HASH

import os
import bcrypt

router = APIRouter()

# Configuration JWT

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquante")
ALGORITHM = "HS256"
TIME_ADMIN_SESSION = int(
    os.getenv("TIME_ADMIN_SESSION", 15)
)
ACCESS_TOKEN_EXPIRE_MINUTES = TIME_ADMIN_SESSION

# JWT

def create_access_token(data: dict):

    to_encode = data.copy()
    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )
    to_encode.update(
        {
            "exp": expire,
            "type": "access"
        }
    )
    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(token: str):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_exp": True
            }
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expiré"
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token invalide"
        )


def get_current_admin(request: Request):

    token = request.cookies.get(
        "access_token"
    )
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Non authentifié"
        )
    payload = verify_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin only"
        )
    return payload

# Vérification connexion

@router.get("/me")

def me(request: Request):

    token = request.cookies.get(
        "access_token"
    )
    if not token:
        return {
            "admin": False
        }
    try:
        payload = verify_token(token)
        return {
            "admin": payload.get("role") == "admin"
        }
    except Exception:
        return {
            "admin": False
        }

# Login admin

@router.post("/login-admin")

def login_admin(
    data: dict,
    response: Response
):
    if bcrypt.checkpw(
        data.get(
            "pwd",
            ""
        ).encode(),
        ADMIN_PASS_HASH.encode()
    ):
        token = create_access_token(
            {
                "role": "admin"
            }
        )
        IS_PROD = (
            os.getenv("ENV") == "prod"
        )
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=IS_PROD,
            samesite="none" if IS_PROD else "lax",
            path="/"
        )
        return {
            "success": True
        }
    return {
        "success": False
    }

# Logout

@router.post("/logout-admin")

def logout_admin(
    response: Response
):
    response.delete_cookie(
        "access_token"
    )
    return {
        "success": True
    }
    