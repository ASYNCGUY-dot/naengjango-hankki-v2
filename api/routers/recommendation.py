"""
V1의 recommendation_agent.py 로직을 HTTP 엔드포인트로 감싸는 얇은 래퍼.
get_user_profile -> get_candidate_recipes -> score_by_ingredients 순서는 그대로 유지한다.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from api.deps import get_db
from src.agents import pantry_agent, recommendation_agent

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


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
def recommend(user_id: int, limit: int = 10, cur: sqlite3.Cursor = Depends(get_db)):
    profile = recommendation_agent.get_user_profile(cur, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 user_id입니다.")

    pantry_items = pantry_agent.get_pantry_ingredients(cur, user_id)
    user_ingredients = [item["name"] for item in pantry_items]

    candidates = recommendation_agent.get_candidate_recipes(cur, profile)
    scored = recommendation_agent.score_by_ingredients(cur, candidates, user_ingredients)

    return scored[:limit]


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: int, cur: sqlite3.Cursor = Depends(get_db)):
    recipe = recommendation_agent.get_recipe_by_id(cur, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 recipe_id입니다.")
    return recipe
