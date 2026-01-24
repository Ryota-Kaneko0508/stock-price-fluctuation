from typing import Annotated

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Header
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

class StockPriceRequest(BaseModel):
    tick: str
    date: str
    offset: int

class Stock(BaseModel):
    tick: str
    company: str
    price_today: float
    price_yesterday: float

class StockDetail(BaseModel):
    tick: str
    company: str
    prices: list[float]

@app.post("/users")
async def create_user(user_request: UserRequest, session: SessionDep) -> Users:
    new_user = Users(Email = user_request.email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.get("/stocks")
async def get_stocks(x_user_id: Annotated[int, Header()], session: SessionDep) -> list[Stock]:
    notifications = session.exec(select(Notifications).where(Notifications.UserID == x_user_id)).all()

    res = []

    for notification in notifications:

        tick = notification.Tick

        #Tikerで一つの銘柄の情報を取得
        stock = yf.Ticker(tick) 

        # 情報取得(.info)
        stock_info = stock.info

        company_name = stock_info["longName"]
        price_today = stock_info["currentPrice"]
        price_yesterday = stock_info["regularMarketPreviousClose"]

        stock_data = Stock(
            tick=tick,
            company=company_name,
            price_today=price_today,
            price_yesterday=price_yesterday
        )

        res.append(stock_data)

    return res

@app.get("/stocks/{stock_id}")
async def get_stocks(stock_id, tick: str, date: str, offset: int):

    #Tikerで一つの銘柄の情報を取得
    stock = yf.Ticker(stock_id) 

    if "longName" not in stock.info:
        raise HTTPException(status_code=404, detail="Not found")

    # 情報取得(.info)
    stock_info = stock.info

    formatted_date = date.replace('/', '-')
    stock_download = stock.history(period="1d", interval="1m")

    print(stock_download)

    res = StockDetail()

    res.tick = stock_info["symbol"]
    res.company = stock_info["longName"]

    return res



