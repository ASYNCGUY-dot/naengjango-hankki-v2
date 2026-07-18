"""
/recommendation/{user_id}, /recommendation/recipes/{id}, /recommendation/recipes/{id}/ingredients를
검증한다. 점수 계산 알고리즘 자체(recommendation_agent.py, 9차 개정을 거친 랭킹 로직)는 이
테스트의 대상이 아니다 - 그건 agent 파일 자체의 관심사고, 이미 실사용 검증을 여러 번 거쳤다.
여기서는 라우터 계층의 계약(404 처리, 응답 모양, 이번 세션에 추가한 영양소 필드 파싱과
재료 목록 엔드포인트)만 확인한다.

seed.sql의 레시피 1개("두부조림", 재료: 두부/양파)를 기준으로, 보유 재료에 "두부"가 있으면
자격(qualifies)을 얻도록 설계했다(메뉴명에 "두부"가 그대로 들어있어 core_ingredients로 잡힘).
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


def _signup_with_pantry(client, username: str, pantry_names: list[str]) -> int:
    user_id = client.post("/auth/signup", json={"username": username, "password": "pw123456"}).json()["user_id"]
    client.put(f"/profile/{user_id}", json=PROFILE_PAYLOAD)
    for name in pantry_names:
        client.post(f"/pantry/{user_id}", json={"name": name, "expiry_date": None})
    return user_id


def test_recommend_nonexistent_user_returns_404(client):
    res = client.get("/recommendation/999999999")
    assert res.status_code == 404


def test_recommend_with_matching_pantry_returns_qualified_recipe_with_nutrients(client):
    user_id = _signup_with_pantry(client, "u_reco_1", ["두부"])
    res = client.get(f"/recommendation/{user_id}", params={"limit": 10})
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
    user_id = _signup_with_pantry(client, "u_reco_2", ["오이"])
    res = client.get(f"/recommendation/{user_id}")
    assert res.status_code == 200
    item = next(i for i in res.json() if i["id"] == RECIPE_ID)
    assert item["qualifies"] is False


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
    user_id = _signup_with_pantry(client, "u_reco_3", [])
    res = client.get(f"/recommendation/recipes/{RECIPE_ID}/ingredients", params={"user_id": user_id})
    assert res.status_code == 200
    items = res.json()
    by_name = {i["name"]: i for i in items}
    assert by_name["두부"]["amount"] == 200
    assert by_name["두부"]["display"] == "두부 200g"
    assert by_name["양파"]["amount"] == 50


def test_recipe_ingredients_nonexistent_user_returns_404(client):
    res = client.get(f"/recommendation/recipes/{RECIPE_ID}/ingredients", params={"user_id": 999999999})
    assert res.status_code == 404
