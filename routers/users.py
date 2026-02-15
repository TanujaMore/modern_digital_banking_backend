from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database import SessionLocal
from models import User
from models import Ticket

from auth import get_current_user
from schemas import UserResponse, UpdateProfile, ChangePassword, TwoFactorUpdate,UserOut


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

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
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
    # 🔥 First delete user tickets
    db.query(Ticket).filter(Ticket.user_id == current_user.id).delete()

    # Then delete user
    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}


@router.get("/me", response_model=UserOut)
def get_my_profile(
    current_user = Depends(get_current_user)
):
    return current_user
