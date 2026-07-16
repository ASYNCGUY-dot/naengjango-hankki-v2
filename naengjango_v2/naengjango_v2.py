"""냉장고 한끼 V2 - 온보딩(프로필 입력) 화면.

FastAPI 백엔드(api/routers/profile.py, POST /profile)를 그대로 호출한다.
새 로직을 만드는 게 아니라, 이미 검증된 백엔드에 화면을 연결하는 작업이다.
"""

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
        else:
            self.error_message = f"저장 실패 ({response.status_code}): {response.text}"
        self.is_submitting = False


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


def success_view() -> rx.Component:
    return rx.vstack(
        rx.heading("프로필이 저장됐습니다!", size="6"),
        rx.text(f"user_id = {State.submitted_user_id}"),
        rx.text("다음 화면(재료 태깅)은 곧 이어서 만듭니다.", color="gray"),
        spacing="3",
    )


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("냉장고 한끼 - 온보딩", size="8"),
            rx.cond(State.submitted_user_id != None, success_view(), onboarding_form()),  # noqa: E711
            spacing="5",
            justify="center",
            align="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
