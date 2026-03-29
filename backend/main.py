from typing import Annotated
import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Header, Request
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
import boto3
import re
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

load_dotenv('.env')
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(channel_access_token)

class Users(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    Email: str
    LineUserID: str | None = Field(default=None)

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
    "https://stock-app-c58c5.web.app"
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

    client = boto3.client(
        "ses",
        aws_access_key_id = os.getenv('ses_access_key_id'),
        aws_secret_access_key = os.getenv('ses_secret_access_key'),
        region_name="ap-northeast-1"
    )

    notifications = session.exec(select(Notifications, Users).join(Users).where(Notifications.Status == True)).all()

    for notification, user in notifications:
        tick = notification.Tick
        stock = yf.Ticker(tick)
        stock_history = stock.history(period="1mo")
        mean_day7_price = stock_history['Close'].iloc[-8:-1].mean()
        current_price = stock_history['Close'].iloc[-1]
        diff_ratio = 100 * (current_price - mean_day7_price) / mean_day7_price
        
        if diff_ratio >= 1 or diff_ratio <= -1:
            from_email = os.getenv('FROM_EMAIL')
            to_email = user.Email
            
            # メッセージ内容の条件分岐
            direction = "上昇" if diff_ratio >= 1 else "下降"
            subject = f"【アラート】{tick}が{abs(diff_ratio):.2f}%{direction}しました"
            content = f"【アラート】{tick}が{abs(diff_ratio):.2f}%{direction}しました"
            
            try:
                response = client.send_email(
                    Source = from_email,
                    Destination = {
                        'ToAddresses': [to_email]
                    },
                    Message = {
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': content, 'Charset': 'UTF-8'}
                        }
                    },
                )

                # レスポンスの表示（boto3は辞書形式なので修正）
                logger.info(f"送信成功: MessageId {response['MessageId']}")
                logger.info(f"HTTP Status: {response['ResponseMetadata']['HTTPStatusCode']}")

            except Exception as e:
                logger.error(f"メール送信エラー ({tick}): {e}")
    logger.info(f"--- Stock Check Task Completed ---")

@app.post("/line/webhook")
async def webhook(request: Request, session: SessionDep):
    # LINEからのリクエストボディを取得
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # これで .get() が使えるようになります
    events = data.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            line_uid = event["source"]["userId"]
            text = event["message"]["text"].strip()
            reply_token = event["replyToken"]

            # 関数を呼び出して結果メッセージを取得
            response_message = link_line_user_by_email(session, text, line_uid)

            # LINEに返信
            line_bot_api.reply_message(
                reply_token, 
                TextSendMessage(text=response_message)
            )

    print(f"LINE Webhook received: {data}")
    return "OK"

def link_line_user_by_email(session: Session, email: str, line_uid: str) -> str:
    """
    メールアドレスを元にユーザーを探し、LineUserIDを紐付ける関数
    """
    # 1. 前後の空白削除と小文字化（入力ミス対策）
    clean_email = email.strip().lower()
    
    # 2. メールアドレス形式のバリデーション
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_pattern, clean_email):
        return "メールアドレスを入力してください。例: example@mail.com"

    # 3. DBからEmailが一致するユーザーを検索
    statement = select(Users).where(Users.Email == clean_email)
    users = session.exec(statement).all()

    if users:
        # 4. LineUserIDを更新
        for user in users:
            user.LineUserID = line_uid
            session.add(user)

        session.commit()
        
        for user in users:
            session.refresh(user)

        return f"連携完了！\n{clean_email} とLINEを紐付けました📈"
    else:
        return f"ご入力の {clean_email} はアプリで登録されていないようです。"






