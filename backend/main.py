from typing import Annotated

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

import yfinance as yf
import pandas as pd

class Users(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    Email: str

class Notifications(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    UserID: int = Field(foreign_key="users.ID")
    Tick: str
    Status: bool

database_url = "postgresql+psycopg2://postgres:password@db:5432/postgresDB"

engine = create_engine(database_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリ起動時に呼ばれる
    print("アプリ開始")
    create_db_and_tables()
    yield
    print("アプリ終了")

app = FastAPI(lifespan=lifespan)

class UserRequest(BaseModel):
    id: str
    email: str

class Stock(BaseModel):
    tick: str
    company: str
    price_today: float
    price_yesterday: float

@app.post("/users")
async def create_user(user_request: UserRequest, session: SessionDep) -> Users:
    new_user = Users(Email = user_request.email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.get("/stocks/")
async def get_stocks(user_id: int, session: SessionDep) -> list[Stock]:
    notifications = session.exec(select(Notifications).where(Notifications.UserID == user_id)).all()

    res = []

    for notification in notifications:

        tick = notification.Tick

        #Tikerで一つの銘柄の情報を取得
        STOCK = yf.Ticker(tick) 

        # 情報取得(.info)
        STOCK_info = STOCK.info

        company_name = STOCK_info["longName"]
        price_today = STOCK_info["currentPrice"]
        price_yesterday = STOCK_info["regularMarketPreviousClose"]

        stock_data = Stock(
            tick=tick,
            company=company_name,
            price_today=price_today,
            price_yesterday=price_yesterday
        )

        res.append(stock_data)

    return res


