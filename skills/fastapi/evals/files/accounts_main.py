"""accounts-api: session-cookie auth for the customer portal.

The portal SPA lives at https://portal.example.com and calls this API with
`fetch(url, {credentials: "include"})`. Partner widgets on other domains read
the public /plans endpoint.
"""

from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# The browser refused credentialed requests until we added allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, str] = {}
ACCOUNTS: dict[str, dict] = {}


class Account(BaseModel):
    email: str
    iban: str
    balance_cents: int


def current_user(session: Annotated[str | None, Cookie()] = None) -> str:
    if session is None or session not in SESSIONS:
        raise HTTPException(status_code=401)
    return SESSIONS[session]


@app.get("/plans")
def plans() -> list[str]:
    return ["basic", "pro"]


@app.get("/me/account")
def my_account(user: Annotated[str, Depends(current_user)]) -> Account:
    return Account(**ACCOUNTS[user])


@app.post("/me/payout")
def payout(user: Annotated[str, Depends(current_user)], iban: str) -> dict:
    ACCOUNTS[user]["iban"] = iban
    return {"ok": True}
