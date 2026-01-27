from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
from models import Category, User
from schemas import CategoryCreate, CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# 🔹 GET ALL CATEGORIES
@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Category).all()


# 🔹 CREATE NEW CATEGORY (WITH KEYWORDS)
@router.post("/", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    cat = Category(
        name=data.name,
        keywords=data.keywords
    )

    db.add(cat)
    db.commit()
    db.refresh(cat)

    return cat


# 🔹 UPDATE CATEGORY KEYWORDS
@router.put("/{cat_id}", response_model=CategoryResponse)
def update_category(
    cat_id: int,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cat = db.query(Category).filter(Category.id == cat_id).first()

    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    cat.name = data.name
    cat.keywords = data.keywords

    db.commit()
    db.refresh(cat)

    return cat


# 🔹 DELETE CATEGORY (OPTIONAL)
@router.delete("/{cat_id}")
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cat = db.query(Category).filter(Category.id == cat_id).first()

    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(cat)
    db.commit()

    return {"message": "Category deleted successfully"}

def auto_assign_category(db, transaction):
    text = ""

    # take merchant and description text
    if transaction.merchant:
        text += transaction.merchant.lower() + " "
    if transaction.description:
        text += transaction.description.lower()

    # get all categories from DB
    categories = db.query(Category).all()

    # match keywords
    for cat in categories:
        if cat.keywords:
            words = cat.keywords.split(",")
            for word in words:
                if word.strip().lower() in text:
                    return cat.name 
            

    