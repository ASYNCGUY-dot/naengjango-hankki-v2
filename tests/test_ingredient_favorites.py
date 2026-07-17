"""
/ingredients/search, /ingredients/{user_id}/{food_code}/toggle, /ingredients/{user_id}/favorites를
검증한다 - 오늘 프론트엔드를 새로 연결한 재료 즐겨찾기 기능.
"""


def _signup(client, username: str) -> int:
    res = client.post("/auth/signup", json={"username": username, "password": "pw123456"})
    return res.json()["user_id"]


def _first_food_code(client) -> str:
    res = client.get("/ingredients/search", params={"keyword": "두부", "limit": 1})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0, "테스트 DB의 ingredient_catalog에 '두부' 검색 결과가 없습니다."
    return items[0]["food_code"]


def test_search_ingredients_returns_results(client):
    res = client.get("/ingredients/search", params={"keyword": "두부", "limit": 5})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] > 0
    assert len(body["items"]) > 0
    assert "food_code" in body["items"][0]


def test_favorites_list_empty_before_any_toggle(client):
    user_id = _signup(client, "u_favfood_1")
    res = client.get(f"/ingredients/{user_id}/favorites")
    assert res.status_code == 200
    assert res.json() == []


def test_toggle_favorite_adds_then_removes(client):
    user_id = _signup(client, "u_favfood_2")
    food_code = _first_food_code(client)

    add_res = client.post(f"/ingredients/{user_id}/{food_code}/toggle")
    assert add_res.status_code == 200
    assert add_res.json()["favorited"] is True

    list_res = client.get(f"/ingredients/{user_id}/favorites")
    codes = [item["food_code"] for item in list_res.json()]
    assert food_code in codes

    remove_res = client.post(f"/ingredients/{user_id}/{food_code}/toggle")
    assert remove_res.status_code == 200
    assert remove_res.json()["favorited"] is False

    list_res_after = client.get(f"/ingredients/{user_id}/favorites")
    codes_after = [item["food_code"] for item in list_res_after.json()]
    assert food_code not in codes_after
