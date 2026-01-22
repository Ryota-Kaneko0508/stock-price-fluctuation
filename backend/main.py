from typing import Annotated

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str

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

@app.post("/users")
async def create_user(user_request: UserRequest, session: SessionDep) -> Users:
    new_user = Users(email = user_request.email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user
