from fastapi import FastAPI
from database import engine
import models

from routers import users, accounts, transactions

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Modern Digital Banking Dashboard")


@app.get("/",tags=["System"])
def root():
    return {"message": "Backend running"}

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["Accounts"]
)

app.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"]
)