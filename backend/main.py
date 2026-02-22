from typing import Annotated
import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Header
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import yfinance as yf
import pandas as pd
import datetime
from zoneinfo import ZoneInfo

load_dotenv('.env')

class Users(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    Email: str

class Notifications(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    UserID: int = Field(foreign_key="users.ID")
    Tick: str
    Status: bool


database_url = ""
if os.getenv("ENV") == "prod":
    db_user = os.getenv('DB_USER')
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    db_host = os.getenv('DB_HOST')
    
    database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
else:
    # ローカル用
    database_url =  os.getenv('DB_URL')
engine = create_engine(database_url)

engine = create_engine(database_url, echo=True)

def create_db_and_tables():
    try:
        # ここで処理が止まってタイムアウトするのを防ぐ
        SQLModel.metadata.create_all(engine)
        print("DB status: Tables created/checked successfully.")
    except Exception as e:
        # エラーをログに出すが、raiseせずにアプリの起動を優先する
        print(f"DB status: Connection failed (but app will start): {e}")

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
    status: bool
    price_today: float
    price_yesterday: float

class StockDetail(BaseModel):
    tick: str
    company: str
    status: bool
    prices: list[float]
    dates: list[str]

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
        status = notification.Status

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
            status=status,
            price_today=price_today,
            price_yesterday=price_yesterday
        )

        res.append(stock_data)

    return res

@app.get("/stocks/{stock_id}")
async def get_stocks(x_user_id: Annotated[int, Header()], stock_id, tick: str, date: str, offset: int, session: SessionDep):

    notification = session.exec(select(Notifications).where(Notifications.UserID == x_user_id, Notifications.Tick == stock_id)).all()

    if len(notification) != 0:
        status = notification[0].Status

    #Tikerで一つの銘柄の情報を取得
    stock = yf.Ticker(stock_id) 

    if "longName" not in stock.info:
        raise HTTPException(status_code=404, detail="The stock does not exist.")

    # 情報取得(.info)
    stock_info = stock.info

    stock_download = stock.history(interval="1h").tail(offset)

    res_tick = stock_info["symbol"]
    res_company = stock_info["longName"]

    if stock_download.empty:
        return StockDetail(
            tick = res_tick,
            company = res_company,
            status = status,
            prices = [],
            dates = []
        )

    stock_download.index = stock_download.index.tz_convert('Asia/Tokyo')

    return StockDetail(
        tick = res_tick,
        company = res_company,
        status = status,
        prices = stock_download["Close"].values.tolist(),
        dates = stock_download.index.strftime("%Y/%m/%d %H:%M").tolist()
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
    
@app.post("/tasks/send-mail")
async def send_main(session: SessionDep):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"--- Stock Check Task Start ---")
    notifications = session.exec(select(Notifications, Users).join(Users).where(Notifications.Status == True)).all()

    for notification, user in notifications:
        tick = notification.Tick
        stock = yf.Ticker(tick)
        stock_history = stock.history(period="1mo")
        mean_day7_price = stock_history['Close'].iloc[-8:-1].mean()
        current_price = stock_history['Close'].iloc[-1]
        diff_ratio = 100 * (current_price - mean_day7_price) / mean_day7_price
        
        if (diff_ratio >= 1.00):
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.getenv('SENDGRID_API_KEY'))
            from_email = Email("test@example.com")  # Change to your verified sender
            to_email = To(user.Email)  # Change to your recipient
            subject = f"【アラート】{tick}が{diff_ratio}%上昇しました",
            content = Content("text/plain", f"【アラート】{tick}が{diff_ratio}%上昇しました")
            mail = Mail(from_email, to_email, subject, content)

            # Get a JSON-ready representation of the Mail object
            mail_json = mail.get()

            # Send an HTTP POST request to /mail/send
            response = sg.client.mail.send.post(request_body=mail_json)
            print(response.status_code)
            print(response.headers)
    logger.info(f"--- Stock Check Task Completed ---")



