"""
V1의 profile_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
validate_profile/save_user_profile/update_user_profile은 수정하지 않고 그대로 가져다 쓴다.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.deps import get_db
from src.agents import profile_agent

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileRequest(BaseModel):
    gender: str
    age_group: str
    allergy: str
    health_goal: str
    purpose: str
    cooking_level: str
    supplements: str
    household_size: int
    novelty_pref: str
    cooking_tools: str
    medical_conditions: str = ""


class ProfileResponse(BaseModel):
    user_id: int


@router.post("", response_model=ProfileResponse)
def create_profile(body: ProfileRequest, cur: sqlite3.Cursor = Depends(get_db)):
    profile = body.model_dump()
    missing = profile_agent.validate_profile(profile)
    if missing:
        raise HTTPException(status_code=422, detail=f"필수 항목 누락: {missing}")
    user_id = profile_agent.save_user_profile(cur, profile)
    return ProfileResponse(user_id=user_id)


@router.put("/{user_id}")
def update_profile(user_id: int, body: ProfileRequest, cur: sqlite3.Cursor = Depends(get_db)):
    profile = body.model_dump()
    missing = profile_agent.validate_profile(profile)
    if missing:
        raise HTTPException(status_code=422, detail=f"필수 항목 누락: {missing}")
    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 user_id입니다.")
    profile_agent.update_user_profile(cur, user_id, profile)
    return {"user_id": user_id, "updated": True}
