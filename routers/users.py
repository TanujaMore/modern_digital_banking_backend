from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database import SessionLocal
from models import User

from schemas import RegisterUser
from auth import hash_password, verify_password, create_access_token
from database import get_db
router = APIRouter(tags=["Users"])


# ================= REGISTER =================

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        phone=user.phone,
     
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}

# ================= LOGIN =================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password,user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ TOKEN STORES user.id
    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }