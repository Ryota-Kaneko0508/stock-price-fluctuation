import sendgrid
import logging
from datetime import datetime
import os
import yfinance as yf
from sqlmodel import Field, Session, SQLModel, create_engine, select
from dotenv import load_dotenv
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv('../.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB設定
DATABASE_URL = os.getenv('DB_URL')
engine = create_engine(DATABASE_URL)

class Notifications(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    UserID: int = Field(foreign_key="users.ID")
    Tick: str
    Status: bool

class Users(SQLModel, table=True):
    ID: int | None = Field(default=None, primary_key=True)
    Email: str

def check_stock_and_notify():
  with Session(engine) as session:
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

if __name__ == "__main__":
    logger.info(f"--- Stock Check Task Start {datetime.now()} ---")
    check_stock_and_notify()
    logger.info(f"--- Stock Check Task Completed {datetime.now()} ---")