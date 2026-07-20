"""
/recommendation/{user_id}, /recommendation/recipes/{id}, /recommendation/recipes/{id}/ingredients를
검증한다. 점수 계산 알고리즘 자체(recommendation_agent.py, 9차 개정을 거친 랭킹 로직)는 이
테스트의 대상이 아니다 - 그건 agent 파일 자체의 관심사고, 이미 실사용 검증을 여러 번 거쳤다.
여기서는 라우터 계층의 계약(404 처리, 응답 모양, 이번 세션에 추가한 영양소 필드 파싱과
재료 목록 엔드포인트)만 확인한다.

seed.sql의 레시피 1개("두부조림", 재료: 두부/양파)를 기준으로, 보유 재료에 "두부"가 있으면
자격(qualifies)을 얻도록 설계했다(메뉴명에 "두부"가 그대로 들어있어 core_ingredients로 잡힘).

2026-07-19 추가: 추천 화면 개편으로 /recommendation/{user_id}가 더 이상 pantry를 자동
조회하지 않고, 쿼리 파라미터 ingredients로 넘긴 목록만 그대로 쓴다 - 그래서 아래 테스트는
pantry에 재료를 넣어두더라도 추천 호출 시 ingredients를 명시적으로 함께 넘긴다.
"""

PROFILE_PAYLOAD = {
    "gender": "여성",
    "age_group": "30대",
    "allergy": "",
    "health_goal": "체중감량",
    "purpose": "자취생 식단관리",
    "cooking_level": "초급",
    "supplements": "없음",
    "household_size": 2,
    "novelty_pref": "새로운 메뉴 선호",
    "cooking_tools": "가스레인지,전자레인지",
    "medical_conditions": "",
}

RECIPE_ID = 1  # seed.sql에 미리 넣어둔 "두부조림"


def _signup_with_pantry(client, username: str, pantry_names: list[str]) -> tuple[int, dict]:
    data = client.post("/auth/signup", json={"username": username, "password": "pw123456"}).json()
    user_id = data["user_id"]
    headers = {"Authorization": f"Bearer {data['token']}"}
    client.put(f"/profile/{user_id}", json=PROFILE_PAYLOAD, headers=headers)
    for name in pantry_names:
        client.post(f"/pantry/{user_id}", json={"name": name, "expiry_date": None}, headers=headers)
    return user_id, headers


def test_recommend_without_token_returns_401(client):
    # 토큰 인가(#63): user_id만 알아서는 남의 추천(프로필 기반 데이터)을 볼 수 없다
    res = client.get("/recommendation/999999999")
    assert res.status_code == 401


def test_recommend_with_matching_pantry_returns_qualified_recipe_with_nutrients(client):
    user_id, headers = _signup_with_pantry(client, "u_reco_1", ["두부"])
    res = client.get(
        f"/recommendation/{user_id}", params={"limit": 10, "ingredients": ["두부"]}, headers=headers,
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    item = next(i for i in items if i["id"] == RECIPE_ID)
    assert item["menu_name"] == "두부조림"
    assert item["qualifies"] is True
    assert item["ingredient_overlap"] >= 1
    # 이번 세션에 추가한 4대 영양소 파싱(_parse_nutrients)이 실제로 채워지는지 확인
    assert item["energy_kcal"] == 120.0
    assert item["protein_g"] == 10.0
    assert item["fat_g"] == 5.0
    assert item["carbs_g"] == 8.0


def test_recommend_without_matching_pantry_recipe_not_qualified_but_still_listed(client):
    # 두부/양파와 전혀 무관한 재료만 보유하면, coverage_ratio가 문턱(0.2) 밑이라 자격을
    # 얻지 못한다 - 다만 알레르기에 걸리지 않는 한 후보 목록 자체에서 빠지지는 않는다.
    user_id, headers = _signup_with_pantry(client, "u_reco_2", ["오이"])
    res = client.get(f"/recommendation/{user_id}", params={"ingredients": ["오이"]}, headers=headers)
    assert res.status_code == 200
    item = next(i for i in res.json() if i["id"] == RECIPE_ID)
    assert item["qualifies"] is False


def test_recommend_without_ingredients_param_returns_unqualified_list(client):
    # 추천 화면 개편(2026-07-19): 재료 목록을 아예 안 넘기면(빈 칸 상태) 더 이상 pantry를
    # 자동으로 읽지 않고, 재료 없는 것으로 취급해서 전부 자격 미달(qualifies=False)로 나온다.
    user_id, headers = _signup_with_pantry(client, "u_reco_5", ["두부"])
    res = client.get(f"/recommendation/{user_id}", headers=headers)
    assert res.status_code == 200
    item = next(i for i in res.json() if i["id"] == RECIPE_ID)
    assert item["qualifies"] is False
    assert item["ingredient_overlap"] == 0


def test_get_recipe_detail(client):
    res = client.get(f"/recommendation/recipes/{RECIPE_ID}")
    assert res.status_code == 200
    body = res.json()
    assert body["menu_name"] == "두부조림"
    assert body["nutrition_group"] == "고단백"


def test_get_recipe_detail_nonexistent_returns_404(client):
    res = client.get("/recommendation/recipes/999999")
    assert res.status_code == 404


def test_recipe_ingredients_scaled_to_household_size(client):
    # base_servings=2, household_size=2 -> 배율 1이라 원본 수량 그대로 나와야 한다.
    user_id, headers = _signup_with_pantry(client, "u_reco_3", [])
    res = client.get(
        f"/recommendation/recipes/{RECIPE_ID}/ingredients",
        params={"user_id": user_id}, headers=headers,
    )
    assert res.status_code == 200
    items = res.json()
    by_name = {i["name"]: i for i in items}
    assert by_name["두부"]["amount"] == 200
    assert by_name["두부"]["display"] == "두부 200g"
    assert by_name["양파"]["amount"] == 50


def test_recipe_ingredients_other_user_returns_403(client):
    _, headers = _signup_with_pantry(client, "u_reco_4", [])
    res = client.get(
        f"/recommendation/recipes/{RECIPE_ID}/ingredients",
        params={"user_id": 999999999}, headers=headers,
    )
    assert res.status_code == 403
