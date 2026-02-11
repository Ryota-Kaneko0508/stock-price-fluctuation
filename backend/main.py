from typing import Annotated

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Header
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.middleware.cors import CORSMiddleware

import yfinance as yf
import pandas as pd
import datetime
from zoneinfo import ZoneInfo

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

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    id: str
    email: str

class StockRegistRequest(BaseModel):
    user_id: int
    tick: str

class StockPatchRequest(BaseModel):
    user_id: int
    status: bool

class Stock(BaseModel):
    tick: str
    company: str
    currency: str
    price_today: float
    price_yesterday: float

class StockDetail(BaseModel):
    tick: str
    company: str
    currency: str
    prices: list[float]
    times: list[str]

class Notification(BaseModel):
    user_id: int
    tick: str
    status: bool

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
        currency = stock_info["currency"]

        stock_data = Stock(
            tick=tick,
            company=company_name,
            currency=currency,
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
        raise HTTPException(status_code=404, detail="The stock does not exist.")

    # 情報取得(.info)
    stock_info = stock.info

    time_zone = stock_info["exchangeTimezoneName"]

    start_dt = pd.Timestamp.now(tz=time_zone).floor("D")
    end_dt = pd.Timestamp.now(tz=time_zone).ceil("D")

    stock_download = stock.history("JPY=X", start=start_dt,end=end_dt, interval="1h")

    res_tick = stock_info["symbol"]
    res_company = stock_info["longName"]

    if stock_download.empty:
        return StockDetail(
            tick = res_tick,
            company = res_company,
            prices = [],
            times = []
        )

    stock_download.index = stock_download.index.tz_convert('Asia/Tokyo')

    return StockDetail(
        tick = res_tick,
        company = res_company,
        currency= res_currency,
        prices = stock_download["Close"].values.tolist()[:offset],
        times = stock_download.index.strftime("%H:%M").tolist()[:offset]
    )

@app.post("/stocks/{stock_id}")
async def regist_notification(stock_id, regist_request: StockRegistRequest, session: SessionDep):

    #Tikerで一つの銘柄の情報を取得
    stock = yf.Ticker(stock_id) 

    if "longName" not in stock.info:
        raise HTTPException(status_code=404, detail="The stock does not exist.")
    
    new_notifications = Notifications(UserID=regist_request.user_id, Tick=regist_request.tick, Status=False)
    session.add(new_notifications)
    session.commit()
    session.refresh(new_notifications)

    res = Notification(user_id=regist_request.user_id, tick=regist_request.tick, status=False)

    return res

@app.patch("/stocks/{stock_id}")
async def update_notification(stock_id, update_request: StockPatchRequest, session: SessionDep):

        #Tikerで一つの銘柄の情報を取得
    stock = yf.Ticker(stock_id) 

    if "longName" not in stock.info:
        raise HTTPException(status_code=404, detail="The stock does not exist.")
    
    notifications = session.exec(select(Notifications).where(
        Notifications.UserID == update_request.user_id,
        Notifications.Tick == stock_id)).all()

    if len(notifications) != 0:
        update_notification = notifications[0]
        update_notification.Status = update_request.status

        session.add(update_notification)
        session.commit()
        session.refresh(update_notification)

        res = Notification(user_id=update_request.user_id, tick=stock_id, status=update_request.status)

        return res
