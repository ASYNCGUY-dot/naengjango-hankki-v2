"""
V1의 safety_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
회수정보 조회는 식약처 공공 API를 매 요청마다 그대로 호출한다 (agent 원본 동작 유지).
"""

import sqlite3

from fastapi import APIRouter, Depends

from pydantic import BaseModel

from api.deps import get_db
from src.agents import safety_agent

router = APIRouter(prefix="/safety", tags=["safety"])


class SafetyCheckRequest(BaseModel):
    ingredient_name: str
    expiry_date: str | None = None


class SafetyCheckResponse(BaseModel):
    recall_matches: list[dict]
    expiry_status: str | None
    saved_notes: int


@router.post("/check", response_model=SafetyCheckResponse)
def check_safety(body: SafetyCheckRequest, cur: sqlite3.Cursor = Depends(get_db)):
    recalls = safety_agent.get_all_recalls()
    recall_matches = safety_agent.check_recall(body.ingredient_name, recalls)

    saved = 0
    for m in recall_matches:
        notice = f"회수 이력 발견: {m.get('PRDTNM')} - 사유: {m.get('RTRVLPRVNS')}"
        safety_agent.save_safety_note(cur, body.ingredient_name, notice, "foodsafetykorea.go.kr")
        saved += 1

    expiry_status = None
    if body.expiry_date:
        expiry_status = safety_agent.check_expiry(body.expiry_date)
        if expiry_status:
            notice = f"유통기한 {expiry_status} (입력값: {body.expiry_date})"
            safety_agent.save_safety_note(cur, body.ingredient_name, notice, "")
            saved += 1

    return SafetyCheckResponse(
        recall_matches=recall_matches,
        expiry_status=expiry_status,
        saved_notes=saved,
    )
