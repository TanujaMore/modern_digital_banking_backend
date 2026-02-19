from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers import users, accounts,alerts, transactions, exports,insights,categorize,budgets,bills,dashboard,rewards
from routers import tickets
from fastapi.staticfiles import StaticFiles


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Modern Digital Banking Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users.router,prefix="/users")
app.include_router(accounts.router,prefix="/accounts")
app.include_router(transactions.router)
app.include_router(categorize.router)
app.include_router(budgets.router)
app.include_router(bills.router)
app.include_router(rewards.router)
app.include_router(tickets.router) # new one
app.include_router(insights.router)
app.include_router(exports.router)
app.include_router(alerts.router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(dashboard.router)





@app.get("/")
def root():
    return {"message": "Backend running"}