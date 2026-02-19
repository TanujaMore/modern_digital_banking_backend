from fastapi import APIRouter, Depends, HTTPException,UploadFile,File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import re
from sqlalchemy.exc import IntegrityError
import random

from models import User, Ticket
from auth import get_current_user
from schemas import UserResponse, UpdateProfile, ChangePassword, TwoFactorUpdate, UserOut
from schemas import RegisterUser,ForgotPasswordRequest,VerifyOtpRequest,ResetPasswordRequest
from auth import hash_password, verify_password, create_access_token
from database import get_db
import shutil
import os
from passlib.context import CryptContext
router = APIRouter(tags=["Users"])

def get_my_profile(current_user = Depends(get_current_user)):
    return current_user

UPLOAD_DIR = "uploads/profile"
os.makedirs(UPLOAD_DIR, exist_ok=True)

forgot_otp_store = {}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
verified_forgot_users = set()


# ================= REGISTER =================

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    try:
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

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


# ================= LOGIN (UNCHANGED) =================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/update-profile")
def update_profile(
    data: UpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.name = data.name
    current_user.phone = data.phone
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}


@router.put("/change-password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    current_user.password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.put("/two-factor")
def update_two_factor(
    data: TwoFactorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.two_factor_enabled = data.enabled
    db.commit()
    return {"message": "Two-factor updated"}


@router.delete("/delete-account")
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Ticket).filter(Ticket.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user = Depends(get_current_user)):
    return current_user


@router.post("/upload-profile")
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = f"user_{current_user.id}.png"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_image = f"/{path}"
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile image uploaded",
        "profile_image": current_user.profile_image
    }



@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = str(random.randint(100000, 999999))
    forgot_otp_store[email] = otp

    print("Forgot OTP:", otp)
    return {
    "message": "OTP sent",
    "otp": otp   # 👈 send OTP to frontend (DEMO ONLY)
}



@router.post("/verify-forgot-otp")
def verify_forgot_otp(data: VerifyOtpRequest):
    email = data.email.lower().strip()

    if forgot_otp_store.get(email) != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"message": "OTP verified"}



@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = pwd_context.hash(data.new_password)
    db.commit()

    forgot_otp_store.pop(email, None)
    return {"message": "Password updated successfully"}