"""
V1의 auth_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
signup/login 함수 자체는 수정하지 않고 그대로 가져다 쓴다.

로그인 무차별 대입 방지: 이 라우터 계층에서만 아이디별 실패 횟수를 인메모리로 세서
잠깐 잠근다. HTTP 계층의 관심사라 auth_agent.py는 건드리지 않는다. Render 단일
인스턴스 기준 - 재시작/재배포되면 카운터가 초기화되지만 이 규모에서는 감내할 만하다.
"""

import sqlite3
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.deps import get_db
from src.agents import auth_agent

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_WINDOW_SECONDS = 15 * 60

_failed_login_attempts: dict[str, list[float]] = defaultdict(list)


def _prune_old_attempts(username: str) -> list[float]:
    cutoff = time.time() - LOGIN_LOCKOUT_WINDOW_SECONDS
    attempts = [t for t in _failed_login_attempts.get(username, []) if t > cutoff]
    _failed_login_attempts[username] = attempts
    return attempts


def _is_locked_out(username: str) -> bool:
    return len(_prune_old_attempts(username)) >= MAX_LOGIN_ATTEMPTS


def _record_failed_login(username: str):
    _prune_old_attempts(username)
    _failed_login_attempts[username].append(time.time())


def _clear_failed_logins(username: str):
    _failed_login_attempts.pop(username, None)


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
    if _is_locked_out(body.username):
        raise HTTPException(
            status_code=429,
            detail=f"로그인 시도가 너무 많습니다. {LOGIN_LOCKOUT_WINDOW_SECONDS // 60}분 후 다시 시도해주세요.",
        )
    user_id = auth_agent.login(cur, body.username, body.password)
    if user_id is None:
        _record_failed_login(body.username)
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    _clear_failed_logins(body.username)
    return LoginResponse(user_id=user_id)
