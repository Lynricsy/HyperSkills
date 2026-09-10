"""Order API wiring. The auth check and the DB session are both global state."""

from collections.abc import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine("postgresql://app:app@db/app")
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(default="")):
    # calls the identity provider; billed per request
    import requests

    resp = requests.get(
        "https://idp.example.com/userinfo",
        headers={"Authorization": authorization},
        timeout=5,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=403, detail="not authenticated")
    return resp.json()


@app.post("/orders")
def create_order(
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    order = {"id": 1, "owner": user["sub"], "items": payload["items"]}
    db.execute("insert into orders ...")
    return order


@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return {"id": order_id, "owner": user["sub"]}
