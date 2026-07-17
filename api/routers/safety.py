"""
V1의 safety_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
회수정보 조회는 식약처 공공 API를 매 요청마다 그대로 호출한다 (agent 원본 동작 유지).

2026-07-18 전체 화면 재검증 중 발견: 식약처 공공 API(openapi.foodsafetykorea.go.kr)가
가끔 응답을 아예 안 주는데(TCP 연결은 되지만 HTTP 응답이 없음), safety_agent.py는
그 경우를 잡지 않아서 requests.exceptions.RequestException이 그대로 터져 사용자에게는
설명 없는 500만 보였다. agent 파일은 그대로 두고, 이 라우터 계층에서만 예외를 잡아
"외부 서비스 응답 지연" 같은 명확한 메시지의 503으로 바꾼다.
"""

import sqlite3

import requests
from fastapi import APIRouter, Depends, HTTPException

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
    try:
        recalls = safety_agent.get_all_recalls()
    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="식약처 회수정보 서비스가 응답하지 않습니다. 잠시 후 다시 시도해주세요.",
        )
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
