from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from auth import get_current_user
from models import Reward, Account, Transaction, User
from schemas import RewardCreate, RewardUpdate, RewardResponse

router = APIRouter(
    prefix="/rewards",
    tags=["Rewards"]
)

# =====================================================
# CREATE REWARD (KEEPED – NOT USED IN AUTO MODE)
# =====================================================
@router.post("/", response_model=RewardResponse)
def create_reward(
    reward: RewardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_reward = Reward(
        user_id=current_user.id,
        program_name=reward.program_name,
        points_balance=reward.points_balance
    )
    db.add(new_reward)
    db.commit()
    db.refresh(new_reward)
    return new_reward


# =====================================================
# LIST REWARDS (ALWAYS RETURN BANK REWARDS)
# =====================================================
@router.get("/", response_model=list[RewardResponse])
def list_rewards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reward = db.query(Reward).filter(
        Reward.user_id == current_user.id,
        Reward.program_name == "Bank Rewards"
    ).first()

    # 🔥 Auto-create if missing
    if not reward:
        reward = Reward(
            user_id=current_user.id,
            program_name="Bank Rewards",
            points_balance=0
        )
        db.add(reward)
        db.commit()
        db.refresh(reward)

    # Frontend expects array
    return [reward]


# =====================================================
# UPDATE POINTS (KEEPED FOR ADMIN / DEBUG)
# =====================================================
@router.put("/{reward_id}", response_model=RewardResponse)
def update_reward(
    reward_id: int,
    data: RewardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reward = db.query(Reward).filter(
        Reward.id == reward_id,
        Reward.user_id == current_user.id
    ).first()

    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    reward.points_balance = data.points_balance
    db.commit()
    db.refresh(reward)
    return reward


# =====================================================
# DELETE REWARD (KEEPED)
# =====================================================
@router.delete("/{reward_id}")
def delete_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reward = db.query(Reward).filter(
        Reward.id == reward_id,
        Reward.user_id == current_user.id
    ).first()

    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    db.delete(reward)
    db.commit()
    return {"message": "Reward deleted successfully"}


# =====================================================
# REDEEM REWARDS (FINAL & FIXED)
# =====================================================
@router.post("/redeem")
def redeem_rewards(
    account_id: int = Query(...),
    points: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reward = db.query(Reward).filter(
        Reward.user_id == current_user.id,
        Reward.program_name == "Bank Rewards"
    ).first()

    if not reward:
        raise HTTPException(status_code=400, detail="No rewards available")

    if points <= 0:
        raise HTTPException(status_code=400, detail="Invalid points")

    if reward.points_balance < points:
        raise HTTPException(status_code=400, detail="Not enough reward points")

    credited_amount = points // 10  # 🔥 10 points = ₹1

    if credited_amount <= 0:
        raise HTTPException(status_code=400, detail="Minimum 10 points required")

    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # ✅ Credit bank account
    account.balance += credited_amount

    # ✅ Deduct reward points
    reward.points_balance -= points

    # ✅ Record transaction
    txn = Transaction(
        account_id=account.id,
        amount=credited_amount,
        txn_type="credit",
        description="Reward Redeemed",
        category="Rewards",
        txn_date=datetime.utcnow()
    )

    db.add(txn)
    db.commit()

    return {
        "message": "Reward redeemed successfully",
        "credited_amount": credited_amount,
        "remaining_points": reward.points_balance
    }
