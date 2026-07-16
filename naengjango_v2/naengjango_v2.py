"""냉장고 한끼 V2 - 온보딩(프로필 입력) + 재료 태깅(내 냉장고) 화면.

FastAPI 백엔드(api/routers/profile.py, api/routers/pantry.py)를 그대로 호출한다.
새 로직을 만드는 게 아니라, 이미 검증된 백엔드에 화면을 연결하는 작업이다.
"""

import json

import reflex as rx
import requests

API_BASE = "http://127.0.0.1:8001"

GENDER_OPTIONS = ["여성", "남성"]
COOKING_LEVEL_OPTIONS = ["초급", "중급", "고급"]
NOVELTY_OPTIONS = ["새로운 메뉴 선호", "익숙한 메뉴 선호"]


class State(rx.State):
    gender: str = GENDER_OPTIONS[0]
    age_group: str = "20대"
    allergy: str = ""
    health_goal: str = ""
    purpose: str = ""
    cooking_level: str = COOKING_LEVEL_OPTIONS[0]
    supplements: str = "없음"
    household_size: str = "1"
    novelty_pref: str = NOVELTY_OPTIONS[0]
    cooking_tools: str = ""
    medical_conditions: str = ""

    is_submitting: bool = False
    error_message: str = ""
    submitted_user_id: int | None = None

    pantry_items: list[dict] = []
    new_ingredient_name: str = ""
    new_ingredient_expiry: str = ""
    pantry_error: str = ""

    safety_checked_name: str = ""
    safety_recall_matches: list[dict] = []
    safety_expiry_status: str = ""
    safety_checking: bool = False
    safety_error: str = ""

    recommendations: list[dict] = []
    recommending: bool = False
    recommend_error: str = ""

    selected_recipe: dict | None = None
    recipe_steps: list[dict] = []
    recipe_detail_error: str = ""

    @rx.event
    def set_field(self, field: str, value: str):
        setattr(self, field, value)

    @rx.event
    def submit_profile(self):
        self.is_submitting = True
        self.error_message = ""
        try:
            household_size_int = int(self.household_size)
        except ValueError:
            self.error_message = "가구 인원은 숫자로 입력해주세요."
            self.is_submitting = False
            return

        payload = {
            "gender": self.gender,
            "age_group": self.age_group,
            "allergy": self.allergy,
            "health_goal": self.health_goal,
            "purpose": self.purpose,
            "cooking_level": self.cooking_level,
            "supplements": self.supplements,
            "household_size": household_size_int,
            "novelty_pref": self.novelty_pref,
            "cooking_tools": self.cooking_tools,
            "medical_conditions": self.medical_conditions,
        }
        try:
            response = requests.post(f"{API_BASE}/profile", json=payload, timeout=10)
        except requests.RequestException as e:
            self.error_message = f"서버에 연결할 수 없습니다: {e}"
            self.is_submitting = False
            return

        if response.status_code == 200:
            self.submitted_user_id = response.json()["user_id"]
            self._fetch_pantry()
        else:
            self.error_message = f"저장 실패 ({response.status_code}): {response.text}"
        self.is_submitting = False

    def _fetch_pantry(self):
        """내 냉장고 목록을 다시 불러온다 (add/remove 후 호출하는 내부 헬퍼)."""
        if self.submitted_user_id is None:
            return
        try:
            response = requests.get(f"{API_BASE}/pantry/{self.submitted_user_id}", timeout=10)
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.pantry_items = response.json()
            self.pantry_error = ""
        else:
            self.pantry_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def add_ingredient(self):
        if not self.new_ingredient_name.strip():
            self.pantry_error = "재료 이름을 입력해주세요."
            return
        payload = {
            "name": self.new_ingredient_name.strip(),
            "expiry_date": self.new_ingredient_expiry.strip() or None,
        }
        try:
            response = requests.post(
                f"{API_BASE}/pantry/{self.submitted_user_id}", json=payload, timeout=10
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.new_ingredient_name = ""
            self.new_ingredient_expiry = ""
            self._fetch_pantry()
        else:
            self.pantry_error = f"추가 실패 ({response.status_code})"

    @rx.event
    def remove_ingredient(self, ingredient_id: int):
        try:
            response = requests.delete(
                f"{API_BASE}/pantry/{self.submitted_user_id}/{ingredient_id}", timeout=10
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self._fetch_pantry()
        else:
            self.pantry_error = f"삭제 실패 ({response.status_code})"

    @rx.event
    def check_safety(self, name: str, expiry_date: str | None):
        self.safety_checking = True
        self.safety_error = ""
        payload = {"ingredient_name": name, "expiry_date": expiry_date}
        try:
            response = requests.post(f"{API_BASE}/safety/check", json=payload, timeout=15)
        except requests.RequestException as e:
            self.safety_error = f"서버에 연결할 수 없습니다: {e}"
            self.safety_checking = False
            return
        if response.status_code == 200:
            data = response.json()
            self.safety_checked_name = name
            self.safety_recall_matches = data["recall_matches"]
            self.safety_expiry_status = data["expiry_status"] or ""
        else:
            self.safety_error = f"확인 실패 ({response.status_code})"
        self.safety_checking = False

    @rx.event
    def get_recommendations(self):
        self.recommending = True
        self.recommend_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/{self.submitted_user_id}",
                params={"limit": 5},
                # 추천 계산이 레시피 1,148개를 훑는 방식이라 느리다(수 초~십수 초) - 넉넉하게 잡는다.
                timeout=60,
            )
        except requests.RequestException as e:
            self.recommend_error = f"서버에 연결할 수 없습니다: {e}"
            self.recommending = False
            return
        if response.status_code == 200:
            self.recommendations = response.json()
        else:
            self.recommend_error = f"추천 실패 ({response.status_code})"
        self.recommending = False

    @rx.event
    def view_recipe(self, recipe_id: int):
        self.recipe_detail_error = ""
        try:
            response = requests.get(f"{API_BASE}/recommendation/recipes/{recipe_id}", timeout=10)
        except requests.RequestException as e:
            self.recipe_detail_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            recipe = response.json()
            self.selected_recipe = recipe
            try:
                self.recipe_steps = json.loads(recipe["steps_json"]) if recipe["steps_json"] else []
            except (json.JSONDecodeError, TypeError):
                self.recipe_steps = []
        else:
            self.recipe_detail_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def back_to_recommendations(self):
        self.selected_recipe = None
        self.recipe_steps = []


def labeled_input(label: str, field: str, placeholder: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold"),
        rx.input(
            placeholder=placeholder,
            value=getattr(State, field),
            on_change=lambda v: State.set_field(field, v),
            width="100%",
        ),
        width="100%",
        spacing="1",
    )


def labeled_select(label: str, field: str, options: list[str]) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold"),
        rx.select(
            options,
            value=getattr(State, field),
            on_change=lambda v: State.set_field(field, v),
            width="100%",
        ),
        width="100%",
        spacing="1",
    )


def onboarding_form() -> rx.Component:
    return rx.vstack(
        labeled_select("성별", "gender", GENDER_OPTIONS),
        labeled_input("연령대", "age_group", "예: 20대"),
        labeled_input("알레르기 (콤마로 구분)", "allergy", "예: 새우,땅콩"),
        labeled_input("건강 목표", "health_goal", "예: 체중감량"),
        labeled_input("이용 목적", "purpose", "예: 자취생 식단관리"),
        labeled_select("요리 수준", "cooking_level", COOKING_LEVEL_OPTIONS),
        labeled_input("복용 중인 보충제", "supplements", "없으면 '없음'"),
        labeled_input("가구 인원", "household_size", "숫자로 입력"),
        labeled_select("메뉴 선호", "novelty_pref", NOVELTY_OPTIONS),
        labeled_input("보유 조리도구 (콤마로 구분)", "cooking_tools", "예: 가스레인지,전자레인지"),
        labeled_input("병력 정보 (선택)", "medical_conditions", "없으면 비워두세요"),
        rx.cond(
            State.error_message != "",
            rx.callout(State.error_message, color_scheme="red", width="100%"),
        ),
        rx.button(
            "프로필 저장",
            on_click=State.submit_profile,
            loading=State.is_submitting,
            width="100%",
        ),
        spacing="3",
        width="100%",
        max_width="480px",
    )


def pantry_item_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["name"], weight="medium"),
        rx.text(
            rx.cond(item["expiry_date"], item["expiry_date"], "유통기한 미입력"),
            size="2",
            color="gray",
        ),
        rx.spacer(),
        rx.button(
            "안전확인",
            size="1",
            variant="soft",
            loading=State.safety_checking,
            on_click=lambda: State.check_safety(item["name"], item["expiry_date"]),
        ),
        rx.button(
            "삭제",
            size="1",
            color_scheme="red",
            variant="soft",
            on_click=lambda: State.remove_ingredient(item["id"]),
        ),
        width="100%",
        align="center",
    )


def safety_result_panel() -> rx.Component:
    return rx.cond(
        State.safety_checked_name != "",
        rx.vstack(
            rx.divider(),
            rx.heading(f"안전정보: {State.safety_checked_name}", size="4"),
            rx.cond(
                State.safety_expiry_status != "",
                rx.callout(f"유통기한 - {State.safety_expiry_status}", color_scheme="orange"),
                rx.callout("유통기한 여유 있음", color_scheme="green"),
            ),
            rx.cond(
                State.safety_recall_matches.length() > 0,
                rx.vstack(
                    rx.text("회수·판매중지 이력이 있습니다:", color="red", weight="bold"),
                    rx.foreach(
                        State.safety_recall_matches,
                        lambda m: rx.text(f"- {m['PRDTNM']}: {m['RTRVLPRVNS']}", size="2"),
                    ),
                    width="100%",
                ),
                rx.callout("회수·판매중지 이력 없음", color_scheme="green"),
            ),
            width="100%",
            spacing="2",
        ),
    )


def recommendation_card(item: dict) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(item["menu_name"], weight="bold", size="4"),
            rx.spacer(),
            rx.cond(
                item["qualifies"],
                rx.badge("보유재료 활용", color_scheme="green"),
                rx.badge("참고용", color_scheme="gray"),
            ),
            width="100%",
        ),
        rx.text(
            f"{item['category']} · {item['calorie']}kcal · 겹치는 재료 {item['ingredient_overlap']}개",
            size="2",
            color="gray",
        ),
        rx.button("상세보기 (조리단계)", size="2", on_click=lambda: State.view_recipe(item["id"])),
        border="1px solid var(--gray-6)",
        border_radius="8px",
        padding="3",
        width="100%",
        spacing="2",
    )


def recommendation_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("오늘의 추천", size="6"),
        rx.button(
            "추천 받기",
            on_click=State.get_recommendations,
            loading=State.recommending,
            width="100%",
        ),
        rx.cond(
            State.recommend_error != "",
            rx.callout(State.recommend_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.recommendations.length() > 0,
            rx.vstack(
                rx.foreach(State.recommendations, recommendation_card),
                width="100%",
                spacing="3",
            ),
        ),
        width="100%",
        spacing="4",
    )


def recipe_step_row(step: dict) -> rx.Component:
    return rx.vstack(
        rx.text(step["text"], size="2"),
        width="100%",
        padding_y="2",
    )


def recipe_detail_view() -> rx.Component:
    return rx.vstack(
        rx.button("← 추천 목록으로", size="2", variant="soft", on_click=State.back_to_recommendations),
        rx.heading(State.selected_recipe["menu_name"], size="6"),
        rx.text(
            f"{State.selected_recipe['category']} · {State.selected_recipe['calorie']}kcal",
            color="gray",
        ),
        rx.cond(
            State.recipe_detail_error != "",
            rx.callout(State.recipe_detail_error, color_scheme="red", width="100%"),
        ),
        rx.heading("조리 단계", size="4"),
        rx.vstack(
            rx.foreach(State.recipe_steps, recipe_step_row),
            width="100%",
            spacing="1",
        ),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def pantry_section() -> rx.Component:
    return rx.vstack(
        rx.heading("내 냉장고", size="6"),
        rx.text(f"user_id = {State.submitted_user_id}", color="gray", size="2"),
        rx.hstack(
            rx.input(
                placeholder="재료 이름 (예: 두부)",
                value=State.new_ingredient_name,
                on_change=lambda v: State.set_field("new_ingredient_name", v),
                width="100%",
            ),
            rx.input(
                placeholder="유통기한 YYYY-MM-DD (선택)",
                value=State.new_ingredient_expiry,
                on_change=lambda v: State.set_field("new_ingredient_expiry", v),
                width="100%",
            ),
            rx.button("추가", on_click=State.add_ingredient),
            width="100%",
        ),
        rx.cond(
            State.pantry_error != "",
            rx.callout(State.pantry_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.pantry_items.length() > 0,
            rx.vstack(
                rx.foreach(State.pantry_items, pantry_item_row),
                width="100%",
                spacing="2",
            ),
            rx.text("아직 등록된 재료가 없습니다.", color="gray"),
        ),
        rx.cond(
            State.safety_error != "",
            rx.callout(State.safety_error, color_scheme="red", width="100%"),
        ),
        safety_result_panel(),
        recommendation_section(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def main_area() -> rx.Component:
    return rx.cond(
        State.submitted_user_id != None,  # noqa: E711
        rx.cond(State.selected_recipe != None, recipe_detail_view(), pantry_section()),  # noqa: E711
        onboarding_form(),
    )


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("냉장고 한끼 - 온보딩", size="8"),
            main_area(),
            spacing="5",
            justify="center",
            align="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
