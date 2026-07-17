"""
V1의 price_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
KAMIS 도매가격을 가져와 레시피의 가격 등급(estimate_recipe_price_tier)과
재료비 추정(estimate_recipe_total_cost)을 그대로 노출한다.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.deps import get_db
from src.agents import portion_agent, price_agent, recommendation_agent

router = APIRouter(prefix="/recommendation/recipes", tags=["price"])


class MatchedIngredient(BaseModel):
    ingredient: str
    item_name: str
    unit: str
    price: float
    ratio: float | None


class IncludedCost(BaseModel):
    ingredient: str
    matched_name: str
    amount_g: float
    cost: float
    is_estimated: bool


class ExcludedCost(BaseModel):
    ingredient: str
    reason: str


class PriceResponse(BaseModel):
    tier: str
    matched: list[MatchedIngredient]
    unmatched: list[str]
    total_cost: float
    included: list[IncludedCost]
    excluded: list[ExcludedCost]


@router.get("/{recipe_id}/price", response_model=PriceResponse)
def get_recipe_price(recipe_id: int, user_id: int, cur: sqlite3.Cursor = Depends(get_db)):
    profile = recommendation_agent.get_user_profile(cur, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 user_id입니다.")

    cur.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 recipe_id입니다.")

    try:
        household_size = int(profile.get("household_size") or 1)
    except (TypeError, ValueError):
        household_size = 1

    base_servings, items = portion_agent.get_recipe_ingredients(cur, recipe_id)
    if not items:
        raise HTTPException(status_code=404, detail="이 레시피에는 재료 수량 정보가 없습니다.")

    scaled_items = portion_agent.scale_ingredients(items, base_servings, household_size)
    ingredient_names = [item["name"] for item in items]

    all_items = price_agent.get_all_prices()
    tier_result = price_agent.estimate_recipe_price_tier(ingredient_names, all_items)
    cost_result = price_agent.estimate_recipe_total_cost(scaled_items, all_items)

    return PriceResponse(
        tier=tier_result["tier"],
        matched=tier_result["matched"],
        unmatched=tier_result["unmatched"],
        total_cost=cost_result["total_cost"],
        included=cost_result["included"],
        excluded=cost_result["excluded"],
    )
