"""
V1의 auth_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
signup/login 함수 자체는 수정하지 않고 그대로 가져다 쓴다.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.deps import get_db
from src.agents import auth_agent

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    username: str
    password: str


class SignupResponse(BaseModel):
    user_id: int


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: int


@router.post("/signup", response_model=SignupResponse)
def signup(body: SignupRequest, cur: sqlite3.Cursor = Depends(get_db)):
    user_id = auth_agent.signup(cur, body.username, body.password)
    if user_id is None:
        raise HTTPException(status_code=409, detail="이미 존재하는 아이디입니다.")
    return SignupResponse(user_id=user_id)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, cur: sqlite3.Cursor = Depends(get_db)):
    user_id = auth_agent.login(cur, body.username, body.password)
    if user_id is None:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    return LoginResponse(user_id=user_id)
