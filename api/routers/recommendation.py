"""
V1의 recommendation_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
get_user_profile -> get_candidate_recipes -> score_by_ingredients 순서는 그대로 유지한다.

목업 대비 디자인 재검토(2026-07-18)에서 추천 카드에 4대 영양소(칼로리/단백질/지방/탄수화물)
요약을 보여주기로 해서, get_candidate_recipes가 이미 SELECT해오는 nutrients_json을
(agent 함수는 건드리지 않고) 이 라우터 계층에서만 파싱해 개별 필드로 노출한다.
"""

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.auth_token import get_current_user_id, require_self
from api.deps import get_db
from src.agents import pantry_agent, recommendation_agent

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


def _parse_nutrients(nutrients_json: str | None) -> dict:
    if not nutrients_json:
        return {}
    try:
        raw = json.loads(nutrients_json)
    except (ValueError, TypeError):
        return {}
    parsed = {}
    for key in ("energy_kcal", "protein_g", "fat_g", "carbs_g"):
        value = raw.get(key)
        try:
            parsed[key] = float(value) if value is not None else None
        except (ValueError, TypeError):
            parsed[key] = None
    return parsed


class RecommendationItem(BaseModel):
    id: int
    menu_name: str
    category: str | None
    calorie: float | None
    nutrition_group: str
    image_url: str | None
    youtube_url: str | None
    ingredient_overlap: int
    coverage_ratio: float
    qualifies: bool
    has_protein_match: bool
    energy_kcal: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None


class RecipeDetail(BaseModel):
    id: int
    menu_name: str
    cook_method: str | None
    category: str | None
    calorie: float | None
    nutrition_group: str
    nutrients_json: str | None
    steps_json: str | None
    youtube_url: str | None
    image_url: str | None


@router.get("/{user_id}", response_model=list[RecommendationItem])
def recommend(
    user_id: int,
    limit: int = 10,
    cur: sqlite3.Cursor = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    require_self(user_id, current_user_id)
    profile = recommendation_agent.get_user_profile(cur, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 user_id입니다.")

    pantry_items = pantry_agent.get_pantry_ingredients(cur, user_id)
    user_ingredients = [item["name"] for item in pantry_items]

    candidates = recommendation_agent.get_candidate_recipes(cur, profile)
    scored = recommendation_agent.score_by_ingredients(cur, candidates, user_ingredients)

    top = scored[:limit]
    for item in top:
        item.update(_parse_nutrients(item.get("nutrients_json")))
    return top


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: int, cur: sqlite3.Cursor = Depends(get_db)):
    recipe = recommendation_agent.get_recipe_by_id(cur, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 recipe_id입니다.")
    return recipe
