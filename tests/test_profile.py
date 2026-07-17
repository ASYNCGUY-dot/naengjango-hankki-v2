"""/profile/{user_id} GET·POST·PUT를 검증한다 - 로그인 후 온보딩 완료 여부 판단에 쓰이는 핵심 경로."""

PROFILE_PAYLOAD = {
    "gender": "여성",
    "age_group": "30대",
    "allergy": "",
    "health_goal": "체중감량",
    "purpose": "자취생 식단관리",
    "cooking_level": "초급",
    "supplements": "없음",
    "household_size": 1,
    "novelty_pref": "새로운 메뉴 선호",
    "cooking_tools": "가스레인지,전자레인지",
    "medical_conditions": "",
}


def _signup(client, username: str) -> int:
    res = client.post("/auth/signup", json={"username": username, "password": "pw123456"})
    return res.json()["user_id"]


def test_get_profile_before_completion_has_profile_false(client):
    user_id = _signup(client, "u_profile_1")
    res = client.get(f"/profile/{user_id}")
    assert res.status_code == 200
    assert res.json()["has_profile"] is False


def test_get_profile_nonexistent_user_returns_404(client):
    res = client.get("/profile/999999999")
    assert res.status_code == 404


def test_put_then_get_profile_reflects_saved_data(client):
    user_id = _signup(client, "u_profile_2")

    put_res = client.put(f"/profile/{user_id}", json=PROFILE_PAYLOAD)
    assert put_res.status_code == 200
    assert put_res.json() == {"user_id": user_id, "updated": True}

    get_res = client.get(f"/profile/{user_id}")
    assert get_res.status_code == 200
    body = get_res.json()
    assert body["has_profile"] is True
    assert body["gender"] == "여성"
    assert body["health_goal"] == "체중감량"
    assert body["household_size"] == 1


def test_put_profile_missing_required_field_returns_422(client):
    # validate_profile()은 키의 "존재"만 보고(빈 문자열도 존재로 침) - 실제로 422가
    # 나는 건 ProfileRequest(Pydantic)가 이 필드에 기본값이 없어서 요청 자체를 거부하기
    # 때문이다. 그래서 값을 비우는 게 아니라 키 자체를 빼야 한다.
    user_id = _signup(client, "u_profile_3")
    incomplete = {k: v for k, v in PROFILE_PAYLOAD.items() if k != "health_goal"}
    res = client.put(f"/profile/{user_id}", json=incomplete)
    assert res.status_code == 422


def test_put_profile_nonexistent_user_returns_404(client):
    res = client.put("/profile/999999999", json=PROFILE_PAYLOAD)
    assert res.status_code == 404
