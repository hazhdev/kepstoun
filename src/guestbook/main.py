import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from guestbook import db
from guestbook.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.migrate(get_settings().database_url)
    yield


app = FastAPI(title="Guestbook", lifespan=lifespan)


class MessageIn(BaseModel):
    author: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1000)


class MessageOut(MessageIn):
    id: int
    created_at: datetime


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    try:
        with db.connect(settings.database_url) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok", "version": settings.app_version}


@app.get("/messages")
def list_messages(limit: int = 50) -> list[MessageOut]:
    with db.connect(get_settings().database_url) as conn:
        rows = conn.execute(
            "SELECT id, author, text, created_at FROM messages ORDER BY id DESC LIMIT %s",
            (min(max(limit, 1), 200),),
        ).fetchall()
    return [MessageOut(id=r[0], author=r[1], text=r[2], created_at=r[3]) for r in rows]


@app.post("/messages", status_code=201)
def create_message(msg: MessageIn) -> MessageOut:
    with db.connect(get_settings().database_url) as conn:
        r = conn.execute(
            "INSERT INTO messages (author, text) VALUES (%s, %s) "
            "RETURNING id, author, text, created_at",
            (msg.author, msg.text),
        ).fetchone()
    return MessageOut(id=r[0], author=r[1], text=r[2], created_at=r[3])
