"""냉장고 한끼 V2 - 온보딩(프로필 입력) + 재료 태깅(내 냉장고) 화면.

FastAPI 백엔드(api/routers/profile.py, api/routers/pantry.py)를 그대로 호출한다.
새 로직을 만드는 게 아니라, 이미 검증된 백엔드에 화면을 연결하는 작업이다.
"""

import json
import os

import reflex as rx
import requests
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8001")

CATEGORY_INGREDIENTS = {
    "채소/과일": ["대파", "양파", "버섯", "시금치", "방울토마토"],
    "육류/생선": ["닭가슴살", "돼지고기", "소고기", "연어"],
    "유제품/계란": ["계란", "우유", "모짜렐라치즈"],
    "기타": ["두부", "김치", "밥", "식용유", "간장"],
}

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

    allergy_items: list[str] = []
    allergy_chip_input: str = ""
    supplement_items: list[str] = []
    supplement_chip_input: str = ""
    onboarding_step: int = 1

    main_tab: str = "home"

    is_submitting: bool = False
    error_message: str = ""
    submitted_user_id: int | None = None
    profile_complete: bool = False
    auth_token: str = ""
    profile_edit_mode: bool = False

    auth_mode: str = "login"
    auth_username: str = ""
    auth_password: str = ""
    auth_error: str = ""
    is_authenticating: bool = False

    pantry_items: list[dict] = []
    pantry_error: str = ""
    show_photo_upload: bool = False
    expiry_edit_id: int = -1
    expiry_edit_value: str = ""

    pantry_photo_uploading: bool = False
    pantry_photo_error: str = ""
    pantry_photo_detected: list[str] = []
    pantry_photo_selected: list[str] = []

    @rx.var
    def quick_add_names(self) -> list[str]:
        """빠른 추가 칩 목록: 즐겨찾는 재료 우선 + 자주 쓰는 기본 재료. 이미 냉장고에
        있는 재료는 빼서, 칩은 항상 "지금 추가할 수 있는 것"만 보여준다."""
        pantry_names = {item["name"] for item in self.pantry_items}
        names: list[str] = []
        for item in self.favorite_ingredients_list:
            if item["name"] not in pantry_names and item["name"] not in names:
                names.append(item["name"])
        for group in CATEGORY_INGREDIENTS.values():
            for name in group:
                if name not in pantry_names and name not in names:
                    names.append(name)
        return names[:14]

    safety_overview_loading: bool = False
    safety_overview_error: str = ""
    safety_overview_fetched: bool = False
    safety_overview_total: int = 0
    safety_overview_warning: int = 0
    safety_overview_normal: int = 0
    safety_overview_items: list[dict] = []
    safety_overview_filter: str = "전체"

    recommendations: list[dict] = []
    recommending: bool = False
    recommend_error: str = ""
    recommend_filter: str = "전체"
    recommend_fetched: bool = False

    recommend_ingredients: list[str] = []
    recommend_manual_input: str = ""
    recommend_search_keyword: str = ""
    recommend_search_results: list[dict] = []
    recommend_searching: bool = False

    is_page_loading: bool = False

    selected_recipe: dict | None = None
    recipe_steps: list[dict] = []
    recipe_detail_error: str = ""
    recipe_detail_tab: str = "recipe"
    recipe_ingredients_list: list[dict] = []

    recipe_favorited: bool = False
    favorite_error: str = ""

    substitution_coverage: dict = {}
    substitution_missing: list[dict] = []
    substitution_error: str = ""
    substitution_detail_index: int = -1

    review_rating: str = "5"
    review_text_input: str = ""
    reviews_list: list[dict] = []
    review_avg_rating: float = 0.0
    review_count: int = 0
    review_summary: str = ""
    review_error: str = ""
    submitting_review: bool = False
    summarizing: bool = False
    review_photo_url: str = ""
    review_photo_uploading: bool = False
    review_photo_error: str = ""

    favorites_list: list[dict] = []
    favorites_error: str = ""
    loading_favorites: bool = False

    popular_categories: list[str] = []
    popular_videos_list: list[dict] = []
    selected_popular_category: str = ""
    popular_error: str = ""

    catalog_keyword: str = ""
    catalog_results: list[dict] = []
    catalog_total: int = 0
    catalog_error: str = ""
    catalog_searching: bool = False

    favorite_ingredient_codes: list[str] = []
    favorite_ingredients_list: list[dict] = []
    favorite_ingredients_error: str = ""

    my_recipes_list: list[dict] = []
    my_recipes_error: str = ""
    loading_my_recipes: bool = False
    my_recipe_menu_name: str = ""
    my_recipe_category: str = ""
    my_recipe_calorie: str = ""
    my_recipe_ingredients: str = ""
    my_recipe_steps: str = ""
    my_recipe_editing_id: int | None = None
    my_recipe_form_error: str = ""
    my_recipe_submitting: bool = False

    price_tier: str = ""
    price_matched: list[dict] = []
    price_unmatched: list[str] = []
    price_total_cost: float = 0.0
    price_included: list[dict] = []
    price_loading: bool = False
    price_error: str = ""
    price_fetched: bool = False

    @rx.var
    def price_cheap_count(self) -> int:
        """부류 중앙값 대비 0.7배 이하(저렴)로 매칭된 재료 수 - 3단 비교 카드의 "가성비" 칸에 쓴다."""
        return sum(1 for m in self.price_matched if m.get("ratio") is not None and m["ratio"] <= 0.7)

    @rx.var
    def price_expensive_count(self) -> int:
        """부류 중앙값 대비 1.3배 이상(고가)로 매칭된 재료 수 - "프리미엄" 칸에 쓴다."""
        return sum(1 for m in self.price_matched if m.get("ratio") is not None and m["ratio"] >= 1.3)

    @rx.var
    def price_normal_count(self) -> int:
        """비교 가능한(ratio 있는) 재료 중 가성비/프리미엄 둘 다 아닌 나머지 - "기본" 칸에 쓴다."""
        total = sum(1 for m in self.price_matched if m.get("ratio") is not None)
        return total - self.price_cheap_count - self.price_expensive_count

    nutrition_bracket_label: str = ""
    nutrition_is_estimated: bool = False
    nutrition_rows: list[dict] = []
    nutrition_sodium_row: dict | None = None
    nutrition_micro_is_partial: bool = False
    nutrition_condition_notes: list[str] = []
    nutrition_loading: bool = False
    nutrition_error: str = ""
    nutrition_fetched: bool = False

    seasonal_ingredients: list[str] = []
    seasonal_matches: list[str] = []
    seasonal_error: str = ""

    shopping_links: list[dict] = []
    shopping_loading: bool = False
    shopping_error: str = ""
    shopping_fetched: bool = False

    recipe_liked: bool = False
    recipe_like_count: int = 0
    like_error: str = ""

    show_ingredient_submission_form: bool = False
    ingredient_submission_name: str = ""
    ingredient_submission_calorie: str = ""
    ingredient_submission_carbs: str = ""
    ingredient_submission_protein: str = ""
    ingredient_submission_fat: str = ""
    ingredient_submission_sodium: str = ""
    ingredient_submission_price: str = ""
    ingredient_submission_error: str = ""
    ingredient_submission_submitting: bool = False
    my_ingredient_submissions: list[dict] = []
    my_ingredient_submissions_error: str = ""

    is_admin: bool = False
    admin_code_input: str = ""
    admin_promote_error: str = ""
    admin_pending_recipes: list[dict] = []
    admin_pending_ingredients: list[dict] = []
    admin_error: str = ""
    admin_loading: bool = False

    @rx.event
    def set_field(self, field: str, value: str):
        setattr(self, field, value)

    @rx.event
    def register_service_worker(self):
        """PWA 설치 요건 충족용 - 페이지 로드 시 서비스워커를 등록한다.
        rx.el.script(src=...)로 동적 삽입한 태그는 브라우저가 실행하지 않아서
        (React가 DOM에 직접 삽입한 script 태그는 파서가 아니라 실행 안 되는 흔한 문제),
        rx.call_script로 직접 실행하는 방식으로 바꿨다."""
        return rx.call_script(
            "if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js'); }"
        )

    @rx.event
    def next_onboarding_step(self):
        if self.onboarding_step < 5:
            self.onboarding_step += 1

    @rx.event
    def prev_onboarding_step(self):
        if self.onboarding_step > 1:
            self.onboarding_step -= 1

    @rx.event
    def add_allergy_chip(self):
        value = self.allergy_chip_input.strip()
        if value and value not in self.allergy_items:
            self.allergy_items.append(value)
        self.allergy_chip_input = ""

    @rx.event
    def remove_allergy_chip(self, item: str):
        self.allergy_items = [i for i in self.allergy_items if i != item]

    @rx.event
    def add_supplement_chip(self):
        value = self.supplement_chip_input.strip()
        if value and value not in self.supplement_items:
            self.supplement_items.append(value)
        self.supplement_chip_input = ""

    @rx.event
    def remove_supplement_chip(self, item: str):
        self.supplement_items = [i for i in self.supplement_items if i != item]

    def _auth_headers(self) -> dict:
        """보호된 API 호출에 싣는 인증 헤더. 로그인 전(토큰 없음)에는 빈 dict를 돌려줘서
        요청 자체는 나가되 서버가 401로 답하게 한다 - 클라이언트에서 미리 막지 않는 이유는
        서버 검증이 단일 진실이 되게 하기 위해서다."""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    @rx.event
    def set_auth_mode(self, mode: str):
        self.auth_mode = mode
        self.auth_error = ""

    @rx.event
    def signup(self):
        if not self.auth_username.strip() or not self.auth_password.strip():
            self.auth_error = "아이디와 비밀번호를 입력해주세요."
            return
        if len(self.auth_password) < 8:
            self.auth_error = "비밀번호는 최소 8자 이상이어야 합니다."
            return
        self.is_authenticating = True
        self.auth_error = ""
        try:
            response = requests.post(
                f"{API_BASE}/auth/signup",
                json={"username": self.auth_username.strip(), "password": self.auth_password},
                timeout=10,
            )
        except requests.RequestException as e:
            self.auth_error = f"서버에 연결할 수 없습니다: {e}"
            self.is_authenticating = False
            return
        if response.status_code == 200:
            data = response.json()
            self.submitted_user_id = data["user_id"]
            self.auth_token = data["token"]
            self.profile_complete = False
            self.auth_password = ""
        elif response.status_code == 409:
            self.auth_error = "이미 존재하는 아이디입니다."
        elif response.status_code == 422:
            try:
                self.auth_error = response.json().get("detail", "입력값을 확인해주세요.")
            except ValueError:
                self.auth_error = "입력값을 확인해주세요."
        else:
            self.auth_error = f"회원가입 실패 ({response.status_code})"
        self.is_authenticating = False

    @rx.event
    def login(self):
        if not self.auth_username.strip() or not self.auth_password.strip():
            self.auth_error = "아이디와 비밀번호를 입력해주세요."
            return
        self.is_authenticating = True
        self.auth_error = ""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": self.auth_username.strip(), "password": self.auth_password},
                timeout=10,
            )
        except requests.RequestException as e:
            self.auth_error = f"서버에 연결할 수 없습니다: {e}"
            self.is_authenticating = False
            return
        if response.status_code != 200:
            if response.status_code == 401:
                self.auth_error = "아이디 또는 비밀번호가 올바르지 않습니다."
            elif response.status_code == 429:
                try:
                    self.auth_error = response.json().get("detail", "로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.")
                except ValueError:
                    self.auth_error = "로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요."
            else:
                self.auth_error = f"로그인 실패 ({response.status_code})"
            self.is_authenticating = False
            return
        data = response.json()
        self.submitted_user_id = data["user_id"]
        self.auth_token = data["token"]
        self.auth_password = ""
        self._load_profile_after_login()
        self.is_authenticating = False

    def _load_profile_after_login(self):
        try:
            response = requests.get(
                f"{API_BASE}/profile/{self.submitted_user_id}",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.auth_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code != 200:
            self.auth_error = f"프로필 조회 실패 ({response.status_code})"
            return
        data = response.json()
        self.profile_complete = data["has_profile"]
        if self.profile_complete:
            self.gender = data["gender"] or GENDER_OPTIONS[0]
            self.age_group = data["age_group"] or "20대"
            self.allergy_items = [a.strip() for a in (data["allergy"] or "").split(",") if a.strip()]
            self.health_goal = data["health_goal"] or ""
            self.purpose = data["purpose"] or ""
            self.cooking_level = data["cooking_level"] or COOKING_LEVEL_OPTIONS[0]
            self.supplement_items = [
                s.strip() for s in (data["supplements"] or "").split(",")
                if s.strip() and s.strip() != "없음"
            ]
            self.household_size = str(data["household_size"]) if data["household_size"] else "1"
            self.novelty_pref = data["novelty_pref"] or NOVELTY_OPTIONS[0]
            self.cooking_tools = data["cooking_tools"] or ""
            self.medical_conditions = data["medical_conditions"] or ""
            self._fetch_pantry()
            self._fetch_popular_categories()
            self._fetch_seasonal()
            self._fetch_favorite_ingredients()

    @rx.event
    def logout(self):
        # 서버 쪽 토큰을 먼저 폐기한다 - 실패해도(서버 콜드스타트 등) 로컬 상태는 초기화한다.
        if self.auth_token:
            try:
                requests.post(
                    f"{API_BASE}/auth/logout", headers=self._auth_headers(), timeout=10
                )
            except requests.RequestException:
                pass
        self.reset()

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
            "allergy": ",".join(self.allergy_items),
            "health_goal": self.health_goal,
            "purpose": self.purpose,
            "cooking_level": self.cooking_level,
            "supplements": ",".join(self.supplement_items) or "없음",
            "household_size": household_size_int,
            "novelty_pref": self.novelty_pref,
            "cooking_tools": self.cooking_tools,
            "medical_conditions": self.medical_conditions,
        }
        try:
            response = requests.put(
                f"{API_BASE}/profile/{self.submitted_user_id}", json=payload,
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.error_message = f"서버에 연결할 수 없습니다: {e}"
            self.is_submitting = False
            return

        if response.status_code == 200:
            self.profile_complete = True
            self._fetch_pantry()
            self._fetch_popular_categories()
            self._fetch_seasonal()
        else:
            self.error_message = f"저장 실패 ({response.status_code}): {response.text}"
        self.is_submitting = False

    @rx.event
    def toggle_profile_edit(self):
        self.profile_edit_mode = not self.profile_edit_mode
        self.error_message = ""

    @rx.event
    def save_profile_edits(self):
        """홈 화면 프로필 카드의 저장 버튼. 온보딩과 같은 submit_profile 로직을 그대로
        재사용하고, 성공했을 때만 수정 모드를 닫는다."""
        self.submit_profile()
        if not self.error_message:
            self.profile_edit_mode = False

    def _fetch_seasonal(self):
        try:
            response = requests.get(
                f"{API_BASE}/seasonal/{self.submitted_user_id}/matches",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.seasonal_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            data = response.json()
            self.seasonal_ingredients = data["seasonal_ingredients"]
            self.seasonal_matches = data["matches"]
            self.seasonal_error = ""
        else:
            self.seasonal_error = f"조회 실패 ({response.status_code})"

    def _fetch_popular_categories(self):
        try:
            response = requests.get(f"{API_BASE}/popular-videos/categories", timeout=10)
        except requests.RequestException as e:
            self.popular_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            categories = response.json()
            self.popular_categories = categories
            if categories:
                self.selected_popular_category = categories[0]
                self._fetch_popular_videos(categories[0])
        else:
            self.popular_error = f"조회 실패 ({response.status_code})"

    def _fetch_popular_videos(self, category: str):
        try:
            response = requests.get(f"{API_BASE}/popular-videos/{category}", params={"limit": 5}, timeout=10)
        except requests.RequestException as e:
            self.popular_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.popular_videos_list = response.json()
            self.popular_error = ""
        else:
            self.popular_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def select_popular_category(self, category: str):
        self.selected_popular_category = category
        self._fetch_popular_videos(category)

    def _fetch_pantry(self):
        """내 냉장고 목록을 다시 불러온다 (add/remove 후 호출하는 내부 헬퍼)."""
        if self.submitted_user_id is None:
            return
        try:
            response = requests.get(
                f"{API_BASE}/pantry/{self.submitted_user_id}",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.pantry_items = response.json()
            self.pantry_error = ""
        else:
            self.pantry_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def toggle_photo_upload(self):
        self.show_photo_upload = not self.show_photo_upload

    @rx.event
    def add_ingredient_by_keyword(self):
        """검색창에 적힌 이름을 카탈로그 매칭 여부와 무관하게 그대로 냉장고에 추가한다."""
        name = self.catalog_keyword.strip()
        if not name:
            self.pantry_error = "재료 이름을 입력해주세요."
            return
        self.add_ingredient_from_catalog(name)
        if not self.pantry_error:
            self.catalog_keyword = ""
            self.catalog_results = []
            self.catalog_total = 0

    @rx.event
    def open_expiry_edit(self, ingredient_id: int, current: str):
        self.expiry_edit_id = ingredient_id
        self.expiry_edit_value = current or ""

    @rx.event
    def cancel_expiry_edit(self):
        self.expiry_edit_id = -1
        self.expiry_edit_value = ""

    @rx.event
    def save_expiry_edit(self):
        try:
            response = requests.put(
                f"{API_BASE}/pantry/{self.submitted_user_id}/{self.expiry_edit_id}",
                json={"expiry_date": self.expiry_edit_value.strip() or None},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.expiry_edit_id = -1
            self.expiry_edit_value = ""
            self._fetch_pantry()
        else:
            self.pantry_error = f"유통기한 수정 실패 ({response.status_code})"

    @rx.event
    async def handle_pantry_photo_upload(self, files: list[rx.UploadFile]):
        """냉장고 사진에서 OpenAI vision으로 재료명을 인식한다 - 인식 결과는 확인 후
        선택한 것만 실제 냉장고(pantry)에 추가된다(자동 추가 아님)."""
        self.pantry_photo_uploading = True
        self.pantry_photo_error = ""
        self.pantry_photo_detected = []
        self.pantry_photo_selected = []
        if not files:
            self.pantry_photo_uploading = False
            return
        try:
            import base64
            from openai import OpenAI

            data = await files[0].read()
            b64 = base64.b64encode(data).decode("utf-8")
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "이 사진은 냉장고나 식재료 사진이야. 사진에서 알아볼 수 있는 "
                                "식재료 이름만 한국어로, 쉼표로 구분해서 나열해줘. 설명이나 "
                                "문장은 넣지 말고 재료명만 적어줘. 알아볼 수 있는 게 없으면 "
                                "'없음'이라고만 답해줘."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
                max_tokens=200,
            )
            text = (response.choices[0].message.content or "").strip()
            if text and text != "없음":
                names = [n.strip() for n in text.replace("\n", ",").split(",") if n.strip()]
                self.pantry_photo_detected = names[:15]
            else:
                self.pantry_photo_error = "사진에서 식재료를 알아보지 못했어요. 다른 사진으로 시도해주세요."
        except Exception as e:
            self.pantry_photo_error = f"재료 인식 실패: {e}"
        self.pantry_photo_uploading = False

    @rx.event
    def toggle_pantry_photo_ingredient(self, name: str):
        if name in self.pantry_photo_selected:
            self.pantry_photo_selected = [n for n in self.pantry_photo_selected if n != name]
        else:
            self.pantry_photo_selected = self.pantry_photo_selected + [name]

    @rx.event
    def confirm_pantry_photo_ingredients(self):
        for name in self.pantry_photo_selected:
            try:
                requests.post(
                    f"{API_BASE}/pantry/{self.submitted_user_id}",
                    json={"name": name, "expiry_date": None},
                    headers=self._auth_headers(), timeout=10,
                )
            except requests.RequestException as e:
                self.pantry_photo_error = f"서버에 연결할 수 없습니다: {e}"
                return
        self.pantry_photo_detected = []
        self.pantry_photo_selected = []
        self._fetch_pantry()
        self._fetch_seasonal()

    @rx.event
    def search_catalog(self):
        self.catalog_searching = True
        self.catalog_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/ingredients/search",
                params={"keyword": self.catalog_keyword, "limit": 10},
                timeout=15,
            )
        except requests.RequestException as e:
            self.catalog_error = f"서버에 연결할 수 없습니다: {e}"
            self.catalog_searching = False
            return
        if response.status_code == 200:
            data = response.json()
            self.catalog_results = data["items"]
            self.catalog_total = data["total"]
        else:
            self.catalog_error = f"검색 실패 ({response.status_code})"
        self.catalog_searching = False

    @rx.event
    def add_ingredient_from_catalog(self, name: str):
        payload = {"name": name, "expiry_date": None}
        try:
            response = requests.post(
                f"{API_BASE}/pantry/{self.submitted_user_id}", json=payload,
                headers=self._auth_headers(), timeout=10
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.pantry_error = ""
            self._fetch_pantry()
            self._fetch_seasonal()
        else:
            self.pantry_error = f"추가 실패 ({response.status_code})"

    def _fetch_favorite_ingredients(self):
        try:
            response = requests.get(
                f"{API_BASE}/ingredients/{self.submitted_user_id}/favorites",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.favorite_ingredients_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.favorite_ingredients_list = response.json()
            self.favorite_ingredient_codes = [item["food_code"] for item in self.favorite_ingredients_list]
        else:
            self.favorite_ingredients_error = f"불러오기 실패 ({response.status_code})"

    @rx.event
    def toggle_ingredient_favorite(self, food_code: str):
        try:
            response = requests.post(
                f"{API_BASE}/ingredients/{self.submitted_user_id}/{food_code}/toggle",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.favorite_ingredients_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self._fetch_favorite_ingredients()
        else:
            self.favorite_ingredients_error = f"즐겨찾기 실패 ({response.status_code})"

    @rx.event
    def remove_ingredient(self, ingredient_id: int):
        try:
            response = requests.delete(
                f"{API_BASE}/pantry/{self.submitted_user_id}/{ingredient_id}",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self._fetch_pantry()
            self._fetch_seasonal()
        else:
            self.pantry_error = f"삭제 실패 ({response.status_code})"

    @rx.event
    def fetch_safety_overview(self):
        self.safety_overview_loading = True
        self.safety_overview_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/safety/overview",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=20,
            )
        except requests.RequestException as e:
            self.safety_overview_error = f"서버에 연결할 수 없습니다: {e}"
            self.safety_overview_loading = False
            return
        if response.status_code == 200:
            data = response.json()
            self.safety_overview_total = data["total"]
            self.safety_overview_warning = data["warning_count"]
            self.safety_overview_normal = data["normal_count"]
            self.safety_overview_items = data["items"]
            self.safety_overview_filter = "전체"
            self.safety_overview_fetched = True
        elif response.status_code == 503:
            try:
                self.safety_overview_error = response.json().get(
                    "detail", "외부 서비스가 응답하지 않습니다. 잠시 후 다시 시도해주세요."
                )
            except ValueError:
                self.safety_overview_error = "외부 서비스가 응답하지 않습니다. 잠시 후 다시 시도해주세요."
        else:
            self.safety_overview_error = f"확인 실패 ({response.status_code})"
        self.safety_overview_loading = False

    @rx.event
    def set_safety_overview_filter(self, value: str):
        self.safety_overview_filter = value

    @rx.var
    def filtered_safety_items(self) -> list[dict]:
        if self.safety_overview_filter == "전체":
            return self.safety_overview_items
        return [i for i in self.safety_overview_items if i.get("status") == self.safety_overview_filter]

    @rx.event
    def get_recommendations(self):
        """추천 화면 개편(2026-07-19): 더 이상 보유 재료(pantry)를 자동으로 쓰지 않고,
        사용자가 이 화면에서 직접 구성한 recommend_ingredients만 그대로 서버에 넘긴다."""
        self.recommending = True
        self.recommend_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/{self.submitted_user_id}",
                params={"limit": 5, "ingredients": self.recommend_ingredients},
                headers=self._auth_headers(),
                # 추천 계산이 레시피 1,148개를 훑는 방식이라 느리다(수 초~십수 초) - 넉넉하게 잡는다.
                timeout=60,
            )
        except requests.RequestException as e:
            self.recommend_error = f"서버에 연결할 수 없습니다: {e}"
            self.recommending = False
            return
        if response.status_code == 200:
            self.recommendations = response.json()
            self.recommend_fetched = True
        else:
            self.recommend_error = f"추천 실패 ({response.status_code})"
        self.recommending = False

    @rx.event
    def add_recommend_ingredient_manual(self):
        name = self.recommend_manual_input.strip()
        if name and name not in self.recommend_ingredients:
            self.recommend_ingredients = self.recommend_ingredients + [name]
        self.recommend_manual_input = ""

    @rx.event
    def remove_recommend_ingredient(self, name: str):
        self.recommend_ingredients = [n for n in self.recommend_ingredients if n != name]

    @rx.event
    def load_pantry_into_recommend_ingredients(self):
        """"냉장고에서 불러오기" - 지금 보유 재료 전체를 이번 추천용 목록에 합친다(중복 제외)."""
        existing = set(self.recommend_ingredients)
        added = [item["name"] for item in self.pantry_items if item["name"] not in existing]
        self.recommend_ingredients = self.recommend_ingredients + added

    @rx.event
    def search_recommend_ingredient(self):
        keyword = self.recommend_search_keyword.strip()
        if not keyword:
            return
        self.recommend_searching = True
        try:
            response = requests.get(
                f"{API_BASE}/ingredients/search",
                params={"keyword": keyword, "limit": 8},
                timeout=15,
            )
        except requests.RequestException as e:
            self.recommend_error = f"서버에 연결할 수 없습니다: {e}"
            self.recommend_searching = False
            return
        if response.status_code == 200:
            self.recommend_search_results = response.json()["items"]
        else:
            self.recommend_error = f"검색 실패 ({response.status_code})"
        self.recommend_searching = False

    @rx.event
    def add_recommend_ingredient_from_search(self, name: str):
        if name not in self.recommend_ingredients:
            self.recommend_ingredients = self.recommend_ingredients + [name]

    @rx.event
    def set_recommend_filter(self, value: str):
        self.recommend_filter = value

    @rx.var
    def filtered_recommendations(self) -> list[dict]:
        if self.recommend_filter == "전체":
            return self.recommendations
        return [r for r in self.recommendations if r.get("nutrition_group") == self.recommend_filter]

    @rx.event
    async def view_recipe(self, recipe_id: int):
        self.is_page_loading = True
        yield
        self.recipe_detail_error = ""
        self.recipe_detail_tab = "recipe"
        try:
            response = requests.get(f"{API_BASE}/recommendation/recipes/{recipe_id}", timeout=10)
        except requests.RequestException as e:
            self.recipe_detail_error = f"서버에 연결할 수 없습니다: {e}"
            self.is_page_loading = False
            return
        if response.status_code == 200:
            recipe = response.json()
            self.selected_recipe = recipe
            try:
                self.recipe_steps = json.loads(recipe["steps_json"]) if recipe["steps_json"] else []
            except (json.JSONDecodeError, TypeError):
                self.recipe_steps = []
            self.review_summary = ""
            self.review_error = ""
            self.review_photo_url = ""
            self.review_photo_error = ""
            self._fetch_reviews(recipe_id)
            self._check_favorited(recipe_id)
            self._fetch_substitution(recipe_id)
            self.price_fetched = False
            self.price_error = ""
            self.nutrition_fetched = False
            self.nutrition_error = ""
            self.shopping_fetched = False
            self.shopping_error = ""
            self._fetch_like_status(recipe_id)
            self._fetch_recipe_ingredients(recipe_id)
        else:
            self.recipe_detail_error = f"조회 실패 ({response.status_code})"
        self.is_page_loading = False

    def _fetch_recipe_ingredients(self, recipe_id: int):
        self.recipe_ingredients_list = []
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/ingredients",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException:
            return
        if response.status_code == 200:
            self.recipe_ingredients_list = response.json()

    def _fetch_like_status(self, recipe_id: int):
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/like",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.like_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            data = response.json()
            self.recipe_liked = data["liked"]
            self.recipe_like_count = data["like_count"]
            self.like_error = ""
        else:
            self.like_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def toggle_recipe_like(self):
        recipe_id = self.selected_recipe["id"]
        try:
            response = requests.post(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/like/toggle",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.like_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            data = response.json()
            self.recipe_liked = data["liked"]
            self.recipe_like_count = data["like_count"]
            self.like_error = ""
        else:
            self.like_error = f"실패 ({response.status_code})"

    @rx.event
    def toggle_ingredient_submission_form(self):
        self.show_ingredient_submission_form = not self.show_ingredient_submission_form
        if self.show_ingredient_submission_form:
            self._fetch_my_ingredient_submissions()

    def _fetch_my_ingredient_submissions(self):
        try:
            response = requests.get(
                f"{API_BASE}/ingredient-submissions",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.my_ingredient_submissions_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.my_ingredient_submissions = response.json()
            self.my_ingredient_submissions_error = ""
        else:
            self.my_ingredient_submissions_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def submit_ingredient_info(self):
        if not self.ingredient_submission_name.strip():
            self.ingredient_submission_error = "재료 이름을 입력해주세요."
            return

        def _to_float(text: str) -> float | None:
            text = text.strip()
            return float(text) if text else None

        try:
            payload = {
                "ingredient_name": self.ingredient_submission_name,
                "calorie": _to_float(self.ingredient_submission_calorie),
                "carbs_g": _to_float(self.ingredient_submission_carbs),
                "protein_g": _to_float(self.ingredient_submission_protein),
                "fat_g": _to_float(self.ingredient_submission_fat),
                "sodium_mg": _to_float(self.ingredient_submission_sodium),
                "price_per_100g": _to_float(self.ingredient_submission_price),
            }
        except ValueError:
            self.ingredient_submission_error = "숫자 항목은 숫자로 입력해주세요."
            return

        self.ingredient_submission_submitting = True
        self.ingredient_submission_error = ""
        try:
            response = requests.post(
                f"{API_BASE}/ingredient-submissions",
                params={"user_id": self.submitted_user_id}, json=payload,
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.ingredient_submission_error = f"서버에 연결할 수 없습니다: {e}"
            self.ingredient_submission_submitting = False
            return
        if response.status_code == 200:
            self.ingredient_submission_name = ""
            self.ingredient_submission_calorie = ""
            self.ingredient_submission_carbs = ""
            self.ingredient_submission_protein = ""
            self.ingredient_submission_fat = ""
            self.ingredient_submission_sodium = ""
            self.ingredient_submission_price = ""
            self._fetch_my_ingredient_submissions()
        else:
            self.ingredient_submission_error = f"등록 실패 ({response.status_code})"
        self.ingredient_submission_submitting = False

    @rx.event
    async def set_main_tab(self, tab: str):
        """탭을 옮기는 동안 데이터를 불러오느라 화면이 멈춘 것처럼 보이지 않도록,
        먼저 로딩 오버레이를 띄우고(yield로 그 상태를 즉시 브라우저에 반영한 뒤)
        실제 데이터 요청을 진행한다."""
        self.is_page_loading = True
        yield
        self.main_tab = tab
        self.selected_recipe = None
        if tab == "community":
            self._fetch_favorites_list()
        elif tab == "home":
            # 인기 레시피 영상 섹션이 홈으로 옮겨왔다 - 로그인 직후 이미 받아왔으면 재요청하지 않는다.
            if not self.popular_categories:
                self._fetch_popular_categories()
        elif tab == "fridge":
            self._fetch_favorite_ingredients()
        elif tab == "mypage":
            self._fetch_my_recipes()
            if self.is_admin:
                self._fetch_admin_pending()
        self.is_page_loading = False

    def _fetch_admin_pending(self):
        self.admin_loading = True
        self.admin_error = ""
        try:
            r1 = requests.get(
                f"{API_BASE}/admin/pending-recipes", params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10
            )
            r2 = requests.get(
                f"{API_BASE}/admin/pending-ingredients", params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10
            )
        except requests.RequestException as e:
            self.admin_error = f"서버에 연결할 수 없습니다: {e}"
            self.admin_loading = False
            return
        if r1.status_code == 200 and r2.status_code == 200:
            self.admin_pending_recipes = r1.json()
            self.admin_pending_ingredients = r2.json()
        else:
            self.admin_error = f"조회 실패 ({r1.status_code}/{r2.status_code})"
        self.admin_loading = False

    @rx.event
    def promote_admin(self):
        if not self.admin_code_input.strip():
            self.admin_promote_error = "관리자 코드를 입력해주세요."
            return
        try:
            response = requests.post(
                f"{API_BASE}/admin/promote",
                params={"user_id": self.submitted_user_id}, json={"code": self.admin_code_input},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.admin_promote_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.is_admin = True
            self.admin_promote_error = ""
            self.admin_code_input = ""
            self._fetch_admin_pending()
        else:
            self.admin_promote_error = "관리자 코드가 올바르지 않습니다."

    @rx.event
    def admin_approve_recipe(self, recipe_id: int):
        try:
            requests.post(
                f"{API_BASE}/admin/recipes/{recipe_id}/approve",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.admin_error = f"서버에 연결할 수 없습니다: {e}"
            return
        self._fetch_admin_pending()

    @rx.event
    def admin_reject_recipe(self, recipe_id: int):
        try:
            requests.post(
                f"{API_BASE}/admin/recipes/{recipe_id}/reject",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.admin_error = f"서버에 연결할 수 없습니다: {e}"
            return
        self._fetch_admin_pending()

    @rx.event
    def admin_approve_ingredient(self, submission_id: int):
        try:
            requests.post(
                f"{API_BASE}/admin/ingredients/{submission_id}/approve",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.admin_error = f"서버에 연결할 수 없습니다: {e}"
            return
        self._fetch_admin_pending()

    @rx.event
    def admin_reject_ingredient(self, submission_id: int):
        try:
            requests.post(
                f"{API_BASE}/admin/ingredients/{submission_id}/reject",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.admin_error = f"서버에 연결할 수 없습니다: {e}"
            return
        self._fetch_admin_pending()

    @rx.event
    def fetch_price(self):
        recipe_id = self.selected_recipe["id"]
        self.price_loading = True
        self.price_error = ""
        try:
            # KAMIS 4개 부류(채소/곡물/축산/수산) API를 순차 호출해서 다소 느리다.
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/price",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(),
                timeout=30,
            )
        except requests.RequestException as e:
            self.price_error = f"서버에 연결할 수 없습니다: {e}"
            self.price_loading = False
            return
        if response.status_code == 200:
            data = response.json()
            self.price_tier = data["tier"]
            self.price_matched = data["matched"]
            self.price_unmatched = data["unmatched"]
            self.price_total_cost = round(data["total_cost"])
            self.price_included = data["included"]
            self.price_fetched = True
        else:
            self.price_error = f"조회 실패 ({response.status_code})"
        self.price_loading = False

    @rx.event
    def fetch_nutrition_fit(self):
        recipe_id = self.selected_recipe["id"]
        self.nutrition_loading = True
        self.nutrition_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/nutrition-fit",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(),
                timeout=15,
            )
        except requests.RequestException as e:
            self.nutrition_error = f"서버에 연결할 수 없습니다: {e}"
            self.nutrition_loading = False
            return
        if response.status_code == 200:
            data = response.json()
            self.nutrition_bracket_label = data["bracket_label"]
            self.nutrition_is_estimated = data["is_estimated"]
            self.nutrition_rows = data["rows"]
            self.nutrition_sodium_row = data["sodium_row"]
            self.nutrition_micro_is_partial = data["micro_is_partial"]
            self.nutrition_condition_notes = data["condition_notes"]
            self.nutrition_fetched = True
        else:
            self.nutrition_error = f"조회 실패 ({response.status_code})"
        self.nutrition_loading = False

    @rx.event
    def fetch_shopping_links(self):
        recipe_id = self.selected_recipe["id"]
        self.shopping_loading = True
        self.shopping_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/shopping-links",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(),
                timeout=15,
            )
        except requests.RequestException as e:
            self.shopping_error = f"서버에 연결할 수 없습니다: {e}"
            self.shopping_loading = False
            return
        if response.status_code == 200:
            self.shopping_links = response.json()["links"]
            self.shopping_fetched = True
        else:
            self.shopping_error = f"조회 실패 ({response.status_code})"
        self.shopping_loading = False

    def _fetch_substitution(self, recipe_id: int):
        self.substitution_detail_index = -1
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/substitution",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(),
                timeout=10,
            )
        except requests.RequestException as e:
            self.substitution_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            data = response.json()
            self.substitution_coverage = data["coverage"]
            self.substitution_missing = data["missing_ingredients"]
            self.substitution_error = ""
        else:
            self.substitution_error = f"조회 실패 ({response.status_code})"

    @rx.var
    def substitution_detail_item(self) -> dict | None:
        if 0 <= self.substitution_detail_index < len(self.substitution_missing):
            return self.substitution_missing[self.substitution_detail_index]
        return None

    @rx.event
    def open_substitution_detail(self, index: int):
        self.substitution_detail_index = index

    @rx.event
    def close_substitution_detail(self):
        self.substitution_detail_index = -1

    @rx.event
    def back_to_recommendations(self):
        self.selected_recipe = None
        self.recipe_steps = []
        self.reviews_list = []
        self.review_summary = ""
        self.review_photo_url = ""
        self.review_photo_error = ""
        self.substitution_coverage = {}
        self.substitution_missing = []

    @rx.event
    def set_recipe_detail_tab(self, tab: str):
        self.recipe_detail_tab = tab

    def _check_favorited(self, recipe_id: int):
        try:
            response = requests.get(
                f"{API_BASE}/favorites/{self.submitted_user_id}",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException:
            return
        if response.status_code == 200:
            self.recipe_favorited = any(f["id"] == recipe_id for f in response.json())

    @rx.event
    def toggle_favorite(self):
        recipe_id = self.selected_recipe["id"]
        try:
            response = requests.post(
                f"{API_BASE}/favorites/{self.submitted_user_id}/{recipe_id}/toggle",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.favorite_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.recipe_favorited = response.json()["favorited"]
            self.favorite_error = ""
        else:
            self.favorite_error = f"실패 ({response.status_code})"

    def _fetch_reviews(self, recipe_id: int):
        try:
            response = requests.get(f"{API_BASE}/reviews/{recipe_id}", timeout=10)
        except requests.RequestException as e:
            self.review_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.reviews_list = response.json()
            self.review_count = len(self.reviews_list)
            if self.review_count > 0:
                self.review_avg_rating = round(
                    sum(r["rating"] for r in self.reviews_list) / self.review_count, 1
                )
            else:
                self.review_avg_rating = 0.0
            # 목업: 후기 3개 이상 쌓이면 버튼 클릭 없이 AI 요약을 자동으로 보여준다
            if self.review_count >= 3:
                self._fetch_review_summary(recipe_id)
        else:
            self.review_error = f"조회 실패 ({response.status_code})"

    @rx.event
    async def handle_review_photo_upload(self, files: list[rx.UploadFile]):
        """후기에 첨부할 사진 1장을 base64 데이터 URI로 인코딩해 image_url에 그대로 저장한다.
        별도 파일 스토리지(S3 등)가 없어 택한 방식 - reviews.image_url은 TEXT라 데이터 URI를
        그대로 담을 수 있고, rx.image(src=...)도 데이터 URI를 바로 렌더링한다."""
        self.review_photo_error = ""
        if not files:
            return
        self.review_photo_uploading = True
        try:
            import base64

            data = await files[0].read()
            b64 = base64.b64encode(data).decode("utf-8")
            self.review_photo_url = f"data:image/jpeg;base64,{b64}"
        except Exception as e:
            self.review_photo_error = f"사진 업로드 실패: {e}"
        self.review_photo_uploading = False

    @rx.event
    def clear_review_photo(self):
        self.review_photo_url = ""
        self.review_photo_error = ""

    @rx.event
    def submit_review(self):
        if not self.review_text_input.strip():
            self.review_error = "후기 내용을 입력해주세요."
            return
        self.submitting_review = True
        self.review_error = ""
        recipe_id = self.selected_recipe["id"]
        payload = {
            "user_id": self.submitted_user_id,
            "rating": int(self.review_rating),
            "review_text": self.review_text_input.strip(),
            "image_url": self.review_photo_url or None,
        }
        try:
            response = requests.post(
                f"{API_BASE}/reviews/{recipe_id}", json=payload,
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.review_error = f"서버에 연결할 수 없습니다: {e}"
            self.submitting_review = False
            return
        if response.status_code == 200:
            self.review_text_input = ""
            self.review_photo_url = ""
            self._fetch_reviews(recipe_id)
        else:
            self.review_error = f"등록 실패 ({response.status_code})"
        self.submitting_review = False

    def _fetch_review_summary(self, recipe_id: int):
        try:
            response = requests.get(f"{API_BASE}/reviews/{recipe_id}/summary", timeout=30)
        except requests.RequestException as e:
            self.review_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.review_summary = response.json()["summary"] or "아직 요약할 후기가 없습니다."
        else:
            self.review_error = f"요약 실패 ({response.status_code})"

    @rx.event
    def get_review_summary(self):
        self.summarizing = True
        recipe_id = self.selected_recipe["id"]
        self._fetch_review_summary(recipe_id)
        self.summarizing = False

    @rx.var
    def review_summary_lines(self) -> list[str]:
        """AI 요약을 불릿 줄 단위로 쪼갠다 - 프롬프트가 "• "로 시작하는 줄만 내놓도록
        요청했지만, 혹시 빈 줄이 섞여 와도 안전하게 걸러낸다."""
        if not self.review_summary:
            return []
        return [line.strip() for line in self.review_summary.split("\n") if line.strip()]

    def _fetch_favorites_list(self):
        self.loading_favorites = True
        self.favorites_error = ""
        try:
            response = requests.get(
                f"{API_BASE}/favorites/{self.submitted_user_id}",
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.favorites_error = f"서버에 연결할 수 없습니다: {e}"
            self.loading_favorites = False
            return
        if response.status_code == 200:
            self.favorites_list = response.json()
        else:
            self.favorites_error = f"조회 실패 ({response.status_code})"
        self.loading_favorites = False

    def _fetch_my_recipes(self):
        try:
            response = requests.get(
                f"{API_BASE}/my-recipes", params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10
            )
        except requests.RequestException as e:
            self.my_recipes_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.my_recipes_list = response.json()
            self.my_recipes_error = ""
        else:
            self.my_recipes_error = f"조회 실패 ({response.status_code})"

    def _reset_my_recipe_form(self):
        self.my_recipe_menu_name = ""
        self.my_recipe_category = ""
        self.my_recipe_calorie = ""
        self.my_recipe_ingredients = ""
        self.my_recipe_steps = ""
        self.my_recipe_editing_id = None
        self.my_recipe_form_error = ""

    @rx.event
    def start_edit_my_recipe(self, recipe_id: int):
        try:
            response = requests.get(
                f"{API_BASE}/my-recipes/{recipe_id}",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.my_recipes_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code != 200:
            self.my_recipes_error = f"조회 실패 ({response.status_code})"
            return
        detail = response.json()
        self.my_recipe_menu_name = detail["menu_name"]
        self.my_recipe_category = detail["category"] or ""
        self.my_recipe_calorie = "" if detail["calorie"] is None else str(detail["calorie"])
        self.my_recipe_ingredients = detail["ingredients_text"]
        self.my_recipe_steps = detail["steps_text"]
        self.my_recipe_editing_id = recipe_id
        self.my_recipe_form_error = ""

    @rx.event
    def cancel_edit_my_recipe(self):
        self._reset_my_recipe_form()

    @rx.event
    def submit_my_recipe(self):
        if not self.my_recipe_menu_name.strip() or not self.my_recipe_ingredients.strip() \
                or not self.my_recipe_steps.strip():
            self.my_recipe_form_error = "메뉴명, 재료, 조리법은 필수입니다."
            return
        calorie_value = None
        if self.my_recipe_calorie.strip():
            try:
                calorie_value = float(self.my_recipe_calorie)
            except ValueError:
                self.my_recipe_form_error = "칼로리는 숫자로 입력해주세요."
                return
        self.my_recipe_submitting = True
        self.my_recipe_form_error = ""
        payload = {
            "menu_name": self.my_recipe_menu_name,
            "category": self.my_recipe_category or "기타",
            "calorie": calorie_value,
            "ingredients_text": self.my_recipe_ingredients,
            "steps_text": self.my_recipe_steps,
        }
        try:
            if self.my_recipe_editing_id is not None:
                response = requests.put(
                    f"{API_BASE}/my-recipes/{self.my_recipe_editing_id}",
                    params={"user_id": self.submitted_user_id}, json=payload,
                headers=self._auth_headers(), timeout=10,
                )
            else:
                response = requests.post(
                    f"{API_BASE}/my-recipes",
                    params={"user_id": self.submitted_user_id}, json=payload,
                headers=self._auth_headers(), timeout=10,
                )
        except requests.RequestException as e:
            self.my_recipe_form_error = f"서버에 연결할 수 없습니다: {e}"
            self.my_recipe_submitting = False
            return
        if response.status_code == 200:
            self._reset_my_recipe_form()
            self._fetch_my_recipes()
        else:
            self.my_recipe_form_error = f"저장 실패 ({response.status_code})"
        self.my_recipe_submitting = False

    @rx.event
    def delete_my_recipe(self, recipe_id: int):
        try:
            response = requests.delete(
                f"{API_BASE}/my-recipes/{recipe_id}",
                params={"user_id": self.submitted_user_id},
                headers=self._auth_headers(), timeout=10,
            )
        except requests.RequestException as e:
            self.my_recipes_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self._fetch_my_recipes()
        else:
            self.my_recipes_error = f"삭제 실패 ({response.status_code})"


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


def chip_input(
    label: str, items, input_field: str, input_value, add_event, remove_event, placeholder: str = ""
) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold"),
        rx.cond(
            items.length() > 0,
            rx.hstack(
                rx.foreach(
                    items,
                    lambda item: rx.badge(
                        rx.hstack(
                            rx.text(item, size="2"),
                            rx.icon("x", size=12, cursor="pointer", on_click=lambda: remove_event(item)),
                            spacing="1", align="center",
                        ),
                        color_scheme="grass", variant="soft", size="2",
                    ),
                ),
                wrap="wrap", width="100%",
            ),
        ),
        rx.hstack(
            rx.input(
                placeholder=placeholder,
                value=input_value,
                on_change=lambda v: State.set_field(input_field, v),
                on_key_down=lambda k: rx.cond(k == "Enter", add_event(), rx.noop()),
                width="100%",
            ),
            rx.button("+ 추가", on_click=add_event, size="2", variant="soft"),
            width="100%",
        ),
        width="100%", spacing="2",
    )


def auth_form() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.image(src="/logo.svg", height="80px"),
            rx.hstack(
                rx.button(
                    "로그인", flex="1",
                    variant=rx.cond(State.auth_mode == "login", "solid", "soft"),
                    on_click=lambda: State.set_auth_mode("login"),
                ),
                rx.button(
                    "회원가입", flex="1",
                    variant=rx.cond(State.auth_mode == "signup", "solid", "soft"),
                    on_click=lambda: State.set_auth_mode("signup"),
                ),
                width="100%",
            ),
            rx.vstack(
                rx.text("아이디", size="2", weight="bold"),
                rx.input(
                    placeholder="아이디",
                    value=State.auth_username,
                    on_change=lambda v: State.set_field("auth_username", v),
                    width="100%",
                ),
                width="100%", spacing="1",
            ),
            rx.vstack(
                rx.text("비밀번호", size="2", weight="bold"),
                rx.input(
                    placeholder="비밀번호",
                    value=State.auth_password,
                    on_change=lambda v: State.set_field("auth_password", v),
                    type="password",
                    width="100%",
                ),
                width="100%", spacing="1",
            ),
            rx.cond(
                State.auth_error != "",
                rx.callout(State.auth_error, color_scheme="red", width="100%"),
            ),
            rx.cond(
                State.auth_mode == "login",
                rx.button(
                    "로그인", on_click=State.login, loading=State.is_authenticating,
                    width="100%", size="3",
                ),
                rx.button(
                    "회원가입", on_click=State.signup, loading=State.is_authenticating,
                    width="100%", size="3",
                ),
            ),
            spacing="4", width="100%", align="center",
        ),
        width="100%", max_width="480px", variant="surface", size="3",
    )


def onboarding_progress_dot(n: int) -> rx.Component:
    return rx.box(
        width="10px", height="10px", border_radius="50%",
        background=rx.cond(State.onboarding_step >= n, rx.color("grass", 9), rx.color("gray", 5)),
    )


def onboarding_progress_dots() -> rx.Component:
    return rx.hstack(
        onboarding_progress_dot(1), onboarding_progress_dot(2), onboarding_progress_dot(3),
        onboarding_progress_dot(4), onboarding_progress_dot(5),
        spacing="2", justify="center", width="100%",
    )


def onboarding_step_1() -> rx.Component:
    return rx.vstack(
        labeled_select("성별", "gender", GENDER_OPTIONS),
        labeled_input("연령대", "age_group", "예: 20대"),
        width="100%", spacing="3",
    )


def onboarding_step_2() -> rx.Component:
    return rx.vstack(
        chip_input(
            "알레르기 (선택)", State.allergy_items, "allergy_chip_input", State.allergy_chip_input,
            State.add_allergy_chip, State.remove_allergy_chip, "예: 새우, 땅콩",
        ),
        chip_input(
            "복용 중인 영양제 (선택)", State.supplement_items, "supplement_chip_input",
            State.supplement_chip_input, State.add_supplement_chip, State.remove_supplement_chip,
            "예: 종합비타민",
        ),
        width="100%", spacing="3",
    )


def onboarding_step_3() -> rx.Component:
    return rx.vstack(
        labeled_input("건강 목표", "health_goal", "예: 체중감량"),
        labeled_input("이용 목적", "purpose", "예: 자취생 식단관리"),
        width="100%", spacing="3",
    )


def onboarding_step_4() -> rx.Component:
    return rx.vstack(
        labeled_select("요리 수준", "cooking_level", COOKING_LEVEL_OPTIONS),
        labeled_input("가구 인원", "household_size", "숫자로 입력"),
        width="100%", spacing="3",
    )


def onboarding_step_5() -> rx.Component:
    return rx.vstack(
        labeled_select("메뉴 선호", "novelty_pref", NOVELTY_OPTIONS),
        labeled_input("보유 조리도구 (콤마로 구분)", "cooking_tools", "예: 가스레인지,전자레인지"),
        labeled_input("병력 정보 (선택)", "medical_conditions", "없으면 비워두세요"),
        width="100%", spacing="3",
    )


def onboarding_form() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("건강 정보를 입력해주세요", size="5"),
            rx.text("추천의 정확도를 높이기 위해 필요해요.", size="2", color="gray"),
            onboarding_progress_dots(),
            rx.match(
                State.onboarding_step,
                (1, onboarding_step_1()),
                (2, onboarding_step_2()),
                (3, onboarding_step_3()),
                (4, onboarding_step_4()),
                onboarding_step_5(),
            ),
            rx.cond(
                State.error_message != "",
                rx.callout(State.error_message, color_scheme="red", width="100%"),
            ),
            rx.hstack(
                rx.cond(
                    State.onboarding_step > 1,
                    rx.button("이전", variant="soft", on_click=State.prev_onboarding_step, flex="1"),
                ),
                rx.cond(
                    State.onboarding_step < 5,
                    rx.button("다음", on_click=State.next_onboarding_step, flex="1"),
                    rx.button(
                        "프로필 저장", on_click=State.submit_profile,
                        loading=State.is_submitting, flex="1",
                    ),
                ),
                width="100%", spacing="2",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        max_width="480px",
        variant="surface",
        size="3",
    )


def pantry_item_row(item: dict) -> rx.Component:
    normal_row = rx.hstack(
        rx.text(item["name"], weight="medium"),
        rx.text(
            rx.cond(item["expiry_date"], item["expiry_date"], "유통기한 미입력"),
            size="2",
            color="gray",
        ),
        rx.spacer(),
        rx.icon_button(
            rx.icon("pencil", size=14),
            size="1", variant="ghost", color_scheme="gray",
            # expiry_date가 None일 수 있어 문자열 인자로 넘기기 전에 ""로 바꿔준다
            on_click=lambda: State.open_expiry_edit(
                item["id"], rx.cond(item["expiry_date"], item["expiry_date"], "")
            ),
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
    edit_row = rx.hstack(
        rx.text(item["name"], weight="medium", flex_shrink="0"),
        rx.input(
            placeholder="YYYY-MM-DD (비우면 삭제)",
            value=State.expiry_edit_value,
            on_change=lambda v: State.set_field("expiry_edit_value", v),
            width="100%", size="1",
        ),
        rx.button("저장", size="1", on_click=State.save_expiry_edit),
        rx.button("취소", size="1", variant="soft", color_scheme="gray", on_click=State.cancel_expiry_edit),
        width="100%", align="center",
    )
    return rx.card(
        rx.cond(State.expiry_edit_id == item["id"], edit_row, normal_row),
        width="100%",
    )


def safety_overview_filter_chip(label: str, count) -> rx.Component:
    return rx.button(
        f"{label}({count})", size="1", radius="full",
        variant=rx.cond(State.safety_overview_filter == label, "solid", "soft"),
        color_scheme=rx.cond(State.safety_overview_filter == label, "grass", "gray"),
        on_click=lambda: State.set_safety_overview_filter(label),
    )


def safety_overview_item_card(item: dict) -> rx.Component:
    is_warning = item["status"] == "주의"
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(item["name"], weight="bold"),
                rx.spacer(),
                rx.cond(
                    is_warning,
                    rx.badge("주의", color_scheme="amber"),
                    rx.badge("정상", color_scheme="green"),
                ),
                width="100%", align="center",
            ),
            rx.cond(
                item["expiry_date"] != None,  # noqa: E711
                rx.text(f"유통기한 {item['expiry_date']}", size="2", color="gray"),
                rx.text("유통기한 미입력", size="2", color="gray"),
            ),
            rx.cond(
                item["expiry_status"] != None,  # noqa: E711
                rx.text(f"유통기한 {item['expiry_status']}. 빠른 섭취를 권장드려요.", size="2", color="amber"),
            ),
            rx.cond(
                item["recall_summary"] != "",
                rx.text(
                    f"회수·판매중지 이력: {item['recall_summary']}",
                    color="red", weight="bold", size="2",
                ),
            ),
            align="start", spacing="1", width="100%",
        ),
        width="100%", variant="surface",
    )


def safety_result_panel() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("보유 재료 안전 정보", size="4"),
        rx.text(
            "식품 회수·판매중지 및 유통기한 정보를 확인하세요.",
            size="2", color="gray",
        ),
        rx.cond(
            State.safety_overview_error != "",
            rx.callout(State.safety_overview_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.safety_overview_fetched,
            rx.vstack(
                rx.hstack(
                    safety_overview_filter_chip("전체", State.safety_overview_total),
                    safety_overview_filter_chip("주의", State.safety_overview_warning),
                    safety_overview_filter_chip("정상", State.safety_overview_normal),
                    wrap="wrap", spacing="2", width="100%",
                ),
                rx.foreach(State.filtered_safety_items, safety_overview_item_card),
                rx.text(
                    "※ 회수/판매중지 정보는 식약처 데이터 기반으로 제공됩니다.",
                    size="1", color="gray",
                ),
                width="100%", spacing="2",
            ),
            rx.button(
                "보유 재료 안전 정보 확인", size="2", variant="soft", width="100%",
                on_click=State.fetch_safety_overview,
                loading=State.safety_overview_loading,
            ),
        ),
        width="100%",
        spacing="2",
    )


def recommendation_reason(item: dict) -> rx.Component:
    return rx.text(
        rx.cond(
            item["has_protein_match"],
            f"{item['nutrition_group']} 식단에 적합하고, 오늘 보유한 재료로 만들 수 있어요.",
            rx.cond(
                item["ingredient_overlap"],
                "오늘 보유한 재료로 충분히 만들 수 있어요.",
                "냉장고에 없는 재료가 많지만 참고해보세요.",
            ),
        ),
        size="1", color="gray",
    )


def recommendation_nutrient_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.cond(
            item["energy_kcal"] != None,  # noqa: E711
            rx.vstack(
                rx.text("열량", size="1", color="gray"),
                rx.text(f"{item['energy_kcal']}kcal", size="2", weight="medium"),
                spacing="0", align="center",
            ),
        ),
        rx.cond(
            item["protein_g"] != None,  # noqa: E711
            rx.vstack(
                rx.text("단백질", size="1", color="gray"),
                rx.text(f"{item['protein_g']}g", size="2", weight="medium"),
                spacing="0", align="center",
            ),
        ),
        rx.cond(
            item["fat_g"] != None,  # noqa: E711
            rx.vstack(
                rx.text("지방", size="1", color="gray"),
                rx.text(f"{item['fat_g']}g", size="2", weight="medium"),
                spacing="0", align="center",
            ),
        ),
        rx.cond(
            item["carbs_g"] != None,  # noqa: E711
            rx.vstack(
                rx.text("탄수화물", size="1", color="gray"),
                rx.text(f"{item['carbs_g']}g", size="2", weight="medium"),
                spacing="0", align="center",
            ),
        ),
        width="100%", justify="between",
    )


def recommendation_card(item: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.cond(
                item["image_url"],
                rx.image(src=item["image_url"], width="100%", height="140px",
                          object_fit="cover", border_radius="12px"),
            ),
            rx.hstack(
                rx.text(item["menu_name"], weight="bold", size="4"),
                rx.spacer(),
                rx.cond(
                    item["qualifies"],
                    rx.badge("보유재료 활용", color_scheme="grass"),
                    rx.badge("참고용", color_scheme="gray"),
                ),
                width="100%",
                align="center",
            ),
            recommendation_reason(item),
            recommendation_nutrient_row(item),
            rx.hstack(
                rx.text(f"{item['category']} · {item['calorie']}kcal", size="2", color="gray"),
                rx.spacer(),
                rx.badge(f"겹치는 재료 {item['ingredient_overlap']}개", color_scheme="grass", variant="soft"),
                width="100%", align="center",
            ),
            rx.button("상세보기 (조리단계)", size="2", width="100%",
                      on_click=lambda: State.view_recipe(item["id"])),
            spacing="2",
            width="100%",
        ),
        width="100%",
        variant="classic",
    )


def recommend_filter_chip(label: str) -> rx.Component:
    return rx.button(
        label, size="1",
        variant=rx.cond(State.recommend_filter == label, "solid", "soft"),
        color_scheme=rx.cond(State.recommend_filter == label, "grass", "gray"),
        radius="full",
        on_click=lambda: State.set_recommend_filter(label),
    )


def recommend_ingredient_chip(name: str) -> rx.Component:
    return rx.badge(
        rx.hstack(
            rx.text(name, size="2"),
            rx.icon("x", size=12, cursor="pointer", on_click=lambda: State.remove_recommend_ingredient(name)),
            spacing="1", align="center",
        ),
        color_scheme="grass", variant="soft", size="2",
    )


def recommend_search_result_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["name"], size="2"),
        rx.spacer(),
        rx.button(
            "추가", size="1", variant="soft",
            on_click=lambda: State.add_recommend_ingredient_from_search(item["name"]),
        ),
        width="100%", align="center",
    )


def recommend_ingredient_picker() -> rx.Component:
    """추천에 쓸 재료를 그때그때 구성하는 섹션 - 기본은 빈 칸에서 수기 입력하고,
    필요하면 냉장고 재료를 통째로 불러오거나 재료를 검색해서 추가할 수 있다."""
    return rx.vstack(
        rx.text("이번 추천에 쓸 재료", size="2", weight="bold", color="gray"),
        rx.cond(
            State.recommend_ingredients.length() > 0,
            rx.hstack(
                rx.foreach(State.recommend_ingredients, recommend_ingredient_chip),
                wrap="wrap", spacing="2", width="100%",
            ),
            rx.text("아직 추가한 재료가 없어요.", size="2", color="gray"),
        ),
        rx.hstack(
            rx.input(
                placeholder="재료 이름 입력 후 Enter (예: 두부)",
                value=State.recommend_manual_input,
                on_change=lambda v: State.set_field("recommend_manual_input", v),
                on_key_down=lambda k: rx.cond(k == "Enter", State.add_recommend_ingredient_manual(), rx.noop()),
                width="100%",
            ),
            rx.button("추가", size="2", variant="soft", on_click=State.add_recommend_ingredient_manual),
            width="100%",
        ),
        rx.button(
            "냉장고에서 불러오기", size="2", variant="soft", width="100%",
            on_click=State.load_pantry_into_recommend_ingredients,
        ),
        rx.hstack(
            rx.input(
                placeholder="재료 찾아서 추가하기",
                value=State.recommend_search_keyword,
                on_change=lambda v: State.set_field("recommend_search_keyword", v),
                on_key_down=lambda k: rx.cond(k == "Enter", State.search_recommend_ingredient(), rx.noop()),
                width="100%",
            ),
            rx.button(
                "검색", size="2", on_click=State.search_recommend_ingredient,
                loading=State.recommend_searching,
            ),
            width="100%",
        ),
        rx.cond(
            State.recommend_search_results.length() > 0,
            rx.vstack(
                rx.foreach(State.recommend_search_results, recommend_search_result_row),
                width="100%", spacing="1",
            ),
        ),
        width="100%", spacing="3",
    )


def recommendation_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("오늘은 어떤 메뉴가 좋을까요?", size="6"),
        rx.text("재료를 구성하고 추천 받기를 눌러보세요.", size="2", color="gray"),
        recommend_ingredient_picker(),
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
            State.recommend_fetched & (State.recommendations.length() == 0),
            rx.text("조건에 맞는 추천 결과가 없어요. 재료를 더 추가해보세요.", size="2", color="gray"),
        ),
        rx.cond(
            State.recommendations.length() > 0,
            rx.vstack(
                rx.hstack(
                    recommend_filter_chip("전체"),
                    recommend_filter_chip("고단백"),
                    recommend_filter_chip("균형"),
                    recommend_filter_chip("고탄수화물"),
                    recommend_filter_chip("고지방"),
                    wrap="wrap", spacing="2", width="100%",
                ),
                rx.foreach(State.filtered_recommendations, recommendation_card),
                width="100%",
                spacing="3",
            ),
        ),
        width="100%",
        spacing="4",
    )


def recipe_ingredient_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.icon("dot", size=14, color=rx.color("grass", 9)),
        rx.text(item["display"], size="2"),
        width="100%", align="center", spacing="2",
    )


def recipe_step_row(step: dict) -> rx.Component:
    return rx.vstack(
        rx.text(step["text"], size="2"),
        width="100%",
        padding_y="2",
    )


def review_row(r: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.avatar(fallback=r["username"], radius="full", size="2"),
            rx.vstack(
                rx.hstack(
                    rx.text(r["username"], weight="bold", size="2"),
                    rx.badge(f"★ {r['rating']}/5", color_scheme="amber"),
                ),
                rx.text(r["review_text"], size="2"),
                rx.cond(
                    r["image_url"],
                    rx.image(src=r["image_url"], width="120px", height="120px",
                              radius="md", object_fit="cover"),
                ),
                spacing="1", align="start",
            ),
            width="100%", align="start",
        ),
        width="100%",
    )


def review_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.hstack(
            rx.heading("유저 후기", size="4"),
            rx.cond(
                State.review_count > 0,
                rx.badge(f"★ {State.review_avg_rating} ({State.review_count})", color_scheme="amber", size="2"),
            ),
            align="center", spacing="2",
        ),
        rx.cond(
            State.review_error != "",
            rx.callout(State.review_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.reviews_list.length() > 0,
            rx.vstack(rx.foreach(State.reviews_list, review_row), width="100%", spacing="2"),
            rx.text("아직 후기가 없습니다.", color="gray", size="2"),
        ),
        rx.cond(
            State.review_summary == "",
            rx.button(
                "AI 후기 요약 보기",
                size="2",
                variant="soft",
                loading=State.summarizing,
                on_click=State.get_review_summary,
            ),
        ),
        rx.cond(
            State.review_summary != "",
            rx.card(
                rx.vstack(
                    rx.text("AI 요약", weight="bold", size="2", color=rx.color("blue", 11)),
                    rx.vstack(
                        rx.foreach(
                            State.review_summary_lines,
                            lambda line: rx.text(line, size="2"),
                        ),
                        align="start", spacing="1",
                    ),
                    align="start", spacing="2",
                ),
                width="100%", variant="surface",
            ),
        ),
        rx.hstack(
            rx.select(
                ["1", "2", "3", "4", "5"],
                value=State.review_rating,
                on_change=lambda v: State.set_field("review_rating", v),
                width="80px",
            ),
            rx.input(
                placeholder="후기를 남겨주세요",
                value=State.review_text_input,
                on_change=lambda v: State.set_field("review_text_input", v),
                width="100%",
            ),
            width="100%",
        ),
        rx.cond(
            State.review_photo_url != "",
            rx.hstack(
                rx.image(src=State.review_photo_url, width="60px", height="60px",
                         radius="md", object_fit="cover"),
                rx.icon_button(
                    rx.icon("x", size=14),
                    on_click=State.clear_review_photo,
                    size="1", variant="soft", color_scheme="gray",
                ),
                align="center", spacing="2",
            ),
            rx.upload(
                rx.hstack(
                    rx.icon("camera", size=16),
                    rx.text("사진 첨부 (선택)", size="2"),
                    align="center", spacing="2",
                ),
                id="review_photo_upload",
                accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"]},
                max_files=1,
                on_drop=State.handle_review_photo_upload(
                    rx.upload_files(upload_id="review_photo_upload")
                ),
                border="1px dashed", border_color=rx.color("gray", 6),
                padding="2", border_radius="8px", width="100%",
            ),
        ),
        rx.cond(
            State.review_photo_uploading,
            rx.spinner(size="1"),
        ),
        rx.cond(
            State.review_photo_error != "",
            rx.callout(State.review_photo_error, color_scheme="red", width="100%", size="1"),
        ),
        rx.button(
            "후기 등록",
            on_click=State.submit_review,
            loading=State.submitting_review,
            width="100%",
        ),
        width="100%",
        spacing="3",
    )


def missing_ingredient_row(m: dict, index: int) -> rx.Component:
    color = rx.cond(
        m["type"] == "omit",
        "gray",
        rx.cond(m["type"] == "substitute", "grass", "amber"),
    )
    return rx.card(
        rx.vstack(
            rx.badge(m["ingredient"], color_scheme=color, size="2"),
            rx.text(m["suggestion"], size="2", color="gray"),
            align="start", spacing="1",
        ),
        width="100%",
        variant="surface",
        cursor="pointer",
        on_click=lambda: State.open_substitution_detail(index),
    )


def substitution_detail_panel() -> rx.Component:
    item = State.substitution_detail_item
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(f"{item['ingredient']}이(가) 없어요", size="5", weight="bold"),
                rx.text("🙁", size="5"),
                spacing="2", align="center",
            ),
            rx.text("다음 재료로 대체하거나 생략할 수 있어요.", size="2", color="gray"),
            rx.card(
                rx.vstack(
                    rx.badge(
                        rx.cond(item["type"] == "omit", "생략 가능", "대체 재료 추천"),
                        color_scheme=rx.cond(item["type"] == "omit", "gray", "grass"),
                    ),
                    rx.text(item["suggestion"], size="2"),
                    align="start", spacing="2", width="100%",
                ),
                width="100%", variant="surface",
            ),
            rx.callout(
                "🙋 " + "재료가 없어도 대체·생략 팁을 참고하면 충분히 맛있게 만들 수 있어요!",
                color_scheme="grass", width="100%", size="1",
            ),
            rx.button("적용하기", size="3", width="100%", on_click=State.close_substitution_detail),
            spacing="3", width="100%",
        ),
        width="100%", variant="surface",
    )


def substitution_section() -> rx.Component:
    return rx.cond(
        State.substitution_coverage,
        rx.vstack(
            rx.heading("부족한 재료 안내", size="4"),
            rx.cond(
                State.substitution_error != "",
                rx.callout(State.substitution_error, color_scheme="red", width="100%"),
            ),
            rx.cond(
                State.substitution_detail_item,
                substitution_detail_panel(),
                rx.cond(
                    State.substitution_missing.length() > 0,
                    rx.vstack(
                        rx.text("부족한 재료 / 대체·생략 안내 (눌러서 자세히 보기)", size="2", weight="bold", color="gray"),
                        rx.foreach(State.substitution_missing, missing_ingredient_row),
                        width="100%",
                        spacing="2",
                    ),
                    rx.text("필요한 재료를 전부 보유하고 있습니다!", color="grass", size="2"),
                ),
            ),
            width="100%",
            spacing="2",
        ),
    )


def price_included_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(f"· {item['ingredient']}", size="2"),
        rx.spacer(),
        rx.text(f"{item['cost']}원", size="2", color="gray"),
        width="100%",
    )


def price_tier_card(label: str, count, color: str) -> rx.Component:
    """3단 비교 카드 한 칸. count는 State.price_*_count 계산 var를 그대로 받는다.
    이 레시피의 실제 등급(State.price_tier)과 일치하는 칸만 강조 테두리+배지로 표시한다."""
    is_current = State.price_tier == label
    return rx.card(
        rx.vstack(
            rx.text(label, weight="bold", size="2"),
            rx.text(f"{count}개 재료", size="1", color="gray"),
            rx.cond(
                is_current,
                rx.badge("이 레시피", color_scheme=color, size="1"),
            ),
            align="center", spacing="1", width="100%",
        ),
        variant=rx.cond(is_current, "surface", "ghost"),
        border=rx.cond(is_current, "2px solid", "1px solid"),
        border_color=rx.cond(is_current, rx.color(color, 8), rx.color("gray", 5)),
        width="100%",
    )


def price_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("가격대별 등급", size="4"),
        rx.cond(
            State.price_fetched,
            rx.vstack(
                rx.hstack(
                    price_tier_card("가성비", State.price_cheap_count, "green"),
                    price_tier_card("기본", State.price_normal_count, "gray"),
                    price_tier_card("프리미엄", State.price_expensive_count, "red"),
                    width="100%", spacing="2",
                ),
                rx.cond(
                    State.price_tier == "정보부족",
                    rx.text(
                        "비교 가능한 재료가 부족해 등급을 매기지 못했습니다 (참고용).",
                        size="1", color="gray",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading(f"약 {State.price_total_cost}원", size="6"),
                        rx.text("1인분 기준 · 포함된 재료만의 부분 합계", size="1", color="gray"),
                        rx.cond(
                            State.price_included.length() > 0,
                            rx.vstack(
                                rx.foreach(State.price_included, price_included_row),
                                width="100%", spacing="1", padding_top="2",
                            ),
                        ),
                        align="start", spacing="2", width="100%",
                    ),
                    width="100%", variant="surface",
                ),
                width="100%", spacing="3",
            ),
            rx.button(
                "예상 재료비 확인", size="2", variant="soft",
                on_click=State.fetch_price, loading=State.price_loading,
            ),
        ),
        rx.cond(
            State.price_error != "",
            rx.callout(State.price_error, color_scheme="red", width="100%"),
        ),
        rx.text(
            "참고용 가격입니다. 최신 가격은 KAMIS 등 공식 채널에서 다시 확인해주세요.",
            size="1", color="gray",
        ),
        width="100%", spacing="2",
    )


def nutrition_row_item(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["label"], size="2", weight="medium"),
        rx.spacer(),
        rx.text(f"{row['provided']}{row['unit']} / {row['target']}{row['unit']}", size="2", color="gray"),
        rx.cond(
            row["pct_of_daily"] != None,  # noqa: E711
            rx.badge(f"{row['pct_of_daily']}%", color_scheme="grass", size="1"),
        ),
        rx.cond(
            row["already_supplemented"],
            rx.badge("영양제로 보충 중", color_scheme="blue", size="1"),
        ),
        width="100%",
        align="center",
    )


def nutrition_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.cond(
            State.nutrition_fetched,
            rx.vstack(
                rx.heading("영양 목표 대비", size="4"),
                rx.text(f"기준: {State.nutrition_bracket_label}", size="2", color="gray"),
                rx.cond(
                    State.nutrition_is_estimated,
                    rx.callout(
                        "프로필에 연령대·성별을 입력하지 않아 성인 평균치로 계산했습니다.",
                        color_scheme="amber", width="100%",
                    ),
                ),
                rx.vstack(rx.foreach(State.nutrition_rows, nutrition_row_item), width="100%", spacing="2"),
                rx.cond(
                    State.nutrition_sodium_row != None,  # noqa: E711
                    rx.hstack(
                        rx.text("나트륨", size="2", weight="medium"),
                        rx.spacer(),
                        rx.text(
                            f"{State.nutrition_sodium_row['provided']}mg / 상한 {State.nutrition_sodium_row['limit']}mg",
                            size="2", color="gray",
                        ),
                        rx.badge(f"{State.nutrition_sodium_row['pct_of_limit']}%", color_scheme="amber", size="1"),
                        width="100%", align="center",
                    ),
                ),
                rx.cond(
                    State.nutrition_micro_is_partial,
                    rx.text(
                        "일부 재료는 단위 환산이 안 되어 부분 합계입니다 (참고용).",
                        size="1", color="gray",
                    ),
                ),
                rx.foreach(
                    State.nutrition_condition_notes,
                    lambda note: rx.callout(note, color_scheme="amber", width="100%", size="1"),
                ),
                width="100%", spacing="2",
            ),
            rx.button(
                "영양 목표 확인", size="2", variant="soft",
                on_click=State.fetch_nutrition_fit, loading=State.nutrition_loading,
            ),
        ),
        rx.cond(
            State.nutrition_error != "",
            rx.callout(State.nutrition_error, color_scheme="red", width="100%"),
        ),
        width="100%", spacing="2",
    )


def shopping_link_row(link: dict) -> rx.Component:
    return rx.hstack(
        rx.text(link["ingredient"], size="2", weight="medium"),
        rx.spacer(),
        rx.link("네이버쇼핑", href=link["naver"], is_external=True, size="2"),
        rx.link("쿠팡", href=link["coupang"], is_external=True, size="2"),
        width="100%",
        align="center",
    )


def shopping_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.cond(
            State.shopping_fetched,
            rx.vstack(
                rx.heading("부족한 재료 구매 링크", size="4"),
                rx.text(
                    "검색 결과 페이지로 연결됩니다 (실제 상품·가격·재고는 보장하지 않습니다).",
                    size="1", color="gray",
                ),
                rx.cond(
                    State.shopping_links.length() > 0,
                    rx.vstack(rx.foreach(State.shopping_links, shopping_link_row), width="100%", spacing="2"),
                    rx.text("구매가 필요한 재료가 없습니다.", size="2", color="gray"),
                ),
                width="100%", spacing="2",
            ),
            rx.button(
                "구매 링크 보기", size="2", variant="soft",
                on_click=State.fetch_shopping_links, loading=State.shopping_loading,
            ),
        ),
        rx.cond(
            State.shopping_error != "",
            rx.callout(State.shopping_error, color_scheme="red", width="100%"),
        ),
        width="100%", spacing="2",
    )


def recipe_detail_tab_button(label: str, tab_key: str) -> rx.Component:
    return rx.button(
        label, size="2", flex="1",
        variant=rx.cond(State.recipe_detail_tab == tab_key, "solid", "soft"),
        on_click=lambda: State.set_recipe_detail_tab(tab_key),
    )


def recipe_detail_tab_bar() -> rx.Component:
    return rx.hstack(
        recipe_detail_tab_button("레시피", "recipe"),
        recipe_detail_tab_button("영양정보", "nutrition"),
        recipe_detail_tab_button("재료정보", "ingredients"),
        recipe_detail_tab_button("영상", "video"),
        width="100%", spacing="2",
    )


def recipe_detail_view() -> rx.Component:
    return rx.vstack(
        rx.button("← 목록으로", size="2", variant="soft", on_click=State.back_to_recommendations),
        rx.cond(
            State.selected_recipe["image_url"],
            rx.image(src=State.selected_recipe["image_url"], width="100%", height="200px",
                      object_fit="cover", border_radius="12px"),
        ),
        rx.hstack(
            rx.heading(State.selected_recipe["menu_name"], size="6"),
            rx.spacer(),
            rx.button(
                f"👍 추천 {State.recipe_like_count}",
                size="2",
                variant=rx.cond(State.recipe_liked, "solid", "soft"),
                on_click=State.toggle_recipe_like,
            ),
            rx.button(
                rx.cond(State.recipe_favorited, "★ 즐겨찾기됨", "☆ 즐겨찾기"),
                size="2",
                variant="soft",
                on_click=State.toggle_favorite,
            ),
            width="100%",
        ),
        rx.cond(
            State.like_error != "",
            rx.callout(State.like_error, color_scheme="red", width="100%"),
        ),
        rx.text(
            f"{State.selected_recipe['category']} · {State.selected_recipe['calorie']}kcal",
            color="gray",
        ),
        rx.cond(
            State.favorite_error != "",
            rx.callout(State.favorite_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.recipe_detail_error != "",
            rx.callout(State.recipe_detail_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.substitution_coverage["coverage_pct"] != None,  # noqa: E711
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.text("보유 재료 사용률", size="2", color="gray"),
                        rx.heading(f"{State.substitution_coverage['coverage_pct']}%", size="7", color=rx.color("grass", 11)),
                        align="start", spacing="0",
                    ),
                    rx.spacer(),
                    rx.cond(
                        State.substitution_missing.length() > 0,
                        rx.badge(f"부족한 재료 {State.substitution_missing.length()}개", color_scheme="amber"),
                    ),
                    width="100%", align="center",
                ),
                width="100%",
            ),
        ),
        recipe_detail_tab_bar(),
        rx.match(
            State.recipe_detail_tab,
            ("nutrition", rx.vstack(price_section(), nutrition_section(), width="100%", padding_top="3")),
            ("ingredients", rx.vstack(substitution_section(), shopping_section(), width="100%", padding_top="3")),
            ("video", rx.vstack(
                rx.cond(
                    State.selected_recipe["youtube_url"],
                    rx.link(
                        "▶ 유튜브에서 조리 영상 보기", href=State.selected_recipe["youtube_url"],
                        is_external=True, color=rx.color("grass", 11), weight="bold",
                    ),
                    rx.text("등록된 영상이 없습니다.", color="gray", size="2"),
                ),
                width="100%", padding_top="3",
            )),
            rx.vstack(
                rx.cond(
                    State.recipe_ingredients_list.length() > 0,
                    rx.vstack(
                        rx.heading("재료 (가구원 수 기준)", size="4"),
                        rx.vstack(
                            rx.foreach(State.recipe_ingredients_list, recipe_ingredient_row),
                            width="100%", spacing="1",
                        ),
                        width="100%", spacing="2",
                    ),
                ),
                rx.heading("조리 단계", size="4"),
                rx.vstack(rx.foreach(State.recipe_steps, recipe_step_row), width="100%", spacing="1"),
                rx.button(
                    "이 레시피로 선택하기", size="3", width="100%",
                    on_click=lambda: State.set_recipe_detail_tab("ingredients"),
                ),
                width="100%", spacing="3", padding_top="3",
            ),
        ),
        review_section(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def favorite_list_item(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.text(item["menu_name"], weight="medium"),
            rx.text(
                rx.cond(
                    item["calorie"] != None,  # noqa: E711
                    f"{item['category']} · {item['calorie']}kcal",
                    item["category"],
                ),
                size="2", color="gray",
            ),
            rx.spacer(),
            rx.button(
                "상세보기",
                size="1",
                on_click=lambda: State.view_recipe(item["id"]),
            ),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def favorites_list_view() -> rx.Component:
    return rx.vstack(
        rx.heading("즐겨찾기한 레시피", size="6"),
        rx.cond(
            State.favorites_error != "",
            rx.callout(State.favorites_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.favorites_list.length() > 0,
            rx.vstack(rx.foreach(State.favorites_list, favorite_list_item), width="100%", spacing="2"),
            rx.text("즐겨찾기한 레시피가 없습니다.", color="gray"),
        ),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def my_recipe_status_badge(status: str) -> rx.Component:
    return rx.cond(
        status == "approved",
        rx.badge("승인됨", color_scheme="green"),
        rx.badge("검토 대기중", color_scheme="orange"),
    )


def my_recipe_list_item(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["menu_name"], weight="medium"),
                rx.text(
                    rx.cond(
                        item["calorie"] != None,  # noqa: E711
                        f"{item['category']} · {item['calorie']}kcal",
                        item["category"],
                    ),
                    size="2", color="gray",
                ),
                my_recipe_status_badge(item["status"]),
                align="start",
                spacing="1",
            ),
            rx.spacer(),
            rx.button("수정", size="1", variant="soft", on_click=lambda: State.start_edit_my_recipe(item["id"])),
            rx.button(
                "삭제", size="1", color_scheme="red", variant="soft",
                on_click=lambda: State.delete_my_recipe(item["id"]),
            ),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def my_recipe_form() -> rx.Component:
    return rx.vstack(
        rx.heading(
            rx.cond(State.my_recipe_editing_id != None, "레시피 수정", "새 레시피 등록"),  # noqa: E711
            size="4",
        ),
        labeled_input("메뉴명", "my_recipe_menu_name", "예: 김치찌개"),
        labeled_input("카테고리", "my_recipe_category", "예: 찌개"),
        labeled_input("칼로리 (kcal)", "my_recipe_calorie", "예: 350"),
        rx.vstack(
            rx.text("재료", size="2", weight="bold"),
            rx.text_area(
                placeholder="예: 김치 200g, 돼지고기 100g, 두부 1/2모",
                value=State.my_recipe_ingredients,
                on_change=lambda v: State.set_field("my_recipe_ingredients", v),
                width="100%",
            ),
            width="100%", spacing="1",
        ),
        rx.vstack(
            rx.text("조리법", size="2", weight="bold"),
            rx.text_area(
                placeholder="예: 1. 김치를 볶는다\n2. 물을 넣고 끓인다",
                value=State.my_recipe_steps,
                on_change=lambda v: State.set_field("my_recipe_steps", v),
                width="100%",
            ),
            width="100%", spacing="1",
        ),
        rx.cond(
            State.my_recipe_form_error != "",
            rx.callout(State.my_recipe_form_error, color_scheme="red", width="100%"),
        ),
        rx.hstack(
            rx.button(
                rx.cond(State.my_recipe_editing_id != None, "수정 완료", "등록하기"),  # noqa: E711
                on_click=State.submit_my_recipe, loading=State.my_recipe_submitting,
            ),
            rx.cond(
                State.my_recipe_editing_id != None,  # noqa: E711
                rx.button("취소", variant="soft", on_click=State.cancel_edit_my_recipe),
            ),
            spacing="2",
        ),
        width="100%", spacing="3",
    )


def my_recipes_view() -> rx.Component:
    return rx.vstack(
        rx.heading("내가 등록한 레시피", size="6"),
        my_recipe_form(),
        rx.divider(),
        rx.cond(
            State.my_recipes_error != "",
            rx.callout(State.my_recipes_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.my_recipes_list.length() > 0,
            rx.vstack(rx.foreach(State.my_recipes_list, my_recipe_list_item), width="100%", spacing="2"),
            rx.text("아직 등록한 레시피가 없습니다.", color="gray"),
        ),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def admin_pending_recipe_row(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["menu_name"], weight="medium"),
                rx.text(
                    rx.cond(
                        item["calorie"] != None,  # noqa: E711
                        f"{item['category']} · {item['calorie']}kcal · by {item['username']}",
                        f"{item['category']} · by {item['username']}",
                    ),
                    size="1", color="gray",
                ),
                align="start", spacing="0",
            ),
            rx.spacer(),
            rx.button("승인", size="1", color_scheme="grass", on_click=lambda: State.admin_approve_recipe(item["id"])),
            rx.button("거절", size="1", color_scheme="red", variant="soft",
                      on_click=lambda: State.admin_reject_recipe(item["id"])),
            width="100%", align="center",
        ),
        width="100%",
    )


def admin_pending_ingredient_row(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["ingredient_name"], weight="medium"),
                rx.text(
                    rx.cond(
                        item["calorie"] != None,  # noqa: E711
                        f"{item['calorie']}kcal · by {item['username']}",
                        f"by {item['username']}",
                    ),
                    size="1", color="gray",
                ),
                align="start", spacing="0",
            ),
            rx.spacer(),
            rx.button("승인", size="1", color_scheme="grass",
                      on_click=lambda: State.admin_approve_ingredient(item["id"])),
            rx.button("거절", size="1", color_scheme="red", variant="soft",
                      on_click=lambda: State.admin_reject_ingredient(item["id"])),
            width="100%", align="center",
        ),
        width="100%",
    )


def admin_view() -> rx.Component:
    return rx.vstack(
        rx.heading("관리자", size="6"),
        rx.cond(
            State.is_admin,
            rx.vstack(
                rx.cond(
                    State.admin_error != "",
                    rx.callout(State.admin_error, color_scheme="red", width="100%"),
                ),
                rx.heading("대기 중인 유저 레시피", size="4"),
                rx.cond(
                    State.admin_pending_recipes.length() > 0,
                    rx.vstack(rx.foreach(State.admin_pending_recipes, admin_pending_recipe_row),
                              width="100%", spacing="2"),
                    rx.text("대기 중인 레시피가 없습니다.", size="2", color="gray"),
                ),
                rx.divider(),
                rx.heading("대기 중인 재료 정보", size="4"),
                rx.cond(
                    State.admin_pending_ingredients.length() > 0,
                    rx.vstack(rx.foreach(State.admin_pending_ingredients, admin_pending_ingredient_row),
                              width="100%", spacing="2"),
                    rx.text("대기 중인 재료 정보가 없습니다.", size="2", color="gray"),
                ),
                width="100%", spacing="3",
            ),
            rx.vstack(
                rx.text("관리자 코드를 입력하면 이 계정이 관리자로 전환됩니다.", size="2", color="gray"),
                rx.input(
                    placeholder="관리자 코드",
                    value=State.admin_code_input,
                    on_change=lambda v: State.set_field("admin_code_input", v),
                    type="password",
                    width="100%",
                ),
                rx.cond(
                    State.admin_promote_error != "",
                    rx.callout(State.admin_promote_error, color_scheme="red", width="100%"),
                ),
                rx.button("관리자 전환", on_click=State.promote_admin),
                width="100%", spacing="3",
            ),
        ),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def popular_video_card(v: dict) -> rx.Component:
    return rx.card(
        rx.link(
            rx.hstack(
                rx.image(src=v["thumbnail_url"], width="100px", height="70px",
                          object_fit="cover", border_radius="8px"),
                rx.vstack(
                    rx.text(v["video_title"], weight="medium", size="2"),
                    rx.text(v["channel_title"], size="1", color="gray"),
                    rx.text(f"조회수 {v['view_count']:,}", size="1", color="gray"),
                    align="start",
                    spacing="1",
                ),
                width="100%",
                align="center",
            ),
            href=v["video_url"],
            is_external=True,
        ),
        width="100%",
    )


def popular_videos_section() -> rx.Component:
    return rx.cond(
        State.popular_categories.length() > 0,
        rx.vstack(
            rx.divider(),
            rx.heading("인기 레시피 영상", size="6"),
            rx.hstack(
                rx.foreach(
                    State.popular_categories,
                    lambda c: rx.button(
                        c, size="1",
                        variant=rx.cond(State.selected_popular_category == c, "solid", "soft"),
                        on_click=lambda: State.select_popular_category(c),
                    ),
                ),
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                State.popular_error != "",
                rx.callout(State.popular_error, color_scheme="red", width="100%"),
            ),
            rx.vstack(
                rx.foreach(State.popular_videos_list, popular_video_card),
                width="100%",
                spacing="2",
            ),
            width="100%",
            spacing="3",
        ),
    )


def catalog_result_row(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["name"], weight="medium"),
                rx.text(
                    f"{item['db_group']} · {item['energy_kcal']}kcal",
                    size="1", color="gray",
                ),
                align="start",
                spacing="0",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.cond(
                    State.favorite_ingredient_codes.contains(item["food_code"]),
                    rx.icon("star", size=16, color=rx.color("amber", 9)),
                    rx.icon("star", size=16),
                ),
                size="1", variant="soft",
                on_click=lambda: State.toggle_ingredient_favorite(item["food_code"]),
            ),
            rx.button(
                "냉장고에 추가",
                size="1",
                on_click=lambda: State.add_ingredient_from_catalog(item["name"]),
            ),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def favorite_ingredient_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.icon("star", size=14, color=rx.color("amber", 9)),
        rx.text(item["name"], size="2"),
        rx.spacer(),
        rx.text(f"{item['energy_kcal']}kcal", size="1", color="gray"),
        rx.icon_button(
            rx.icon("x", size=14),
            size="1", variant="ghost", color_scheme="gray",
            on_click=lambda: State.toggle_ingredient_favorite(item["food_code"]),
        ),
        width="100%", align="center",
    )


def favorite_ingredients_section() -> rx.Component:
    return rx.cond(
        State.favorite_ingredients_list.length() > 0,
        rx.vstack(
            rx.divider(),
            rx.heading("즐겨찾는 재료", size="4"),
            rx.cond(
                State.favorite_ingredients_error != "",
                rx.callout(State.favorite_ingredients_error, color_scheme="red", width="100%"),
            ),
            rx.foreach(State.favorite_ingredients_list, favorite_ingredient_row),
            width="100%", spacing="2",
        ),
    )


def ingredient_submission_status_badge(status: str) -> rx.Component:
    return rx.cond(
        status == "approved",
        rx.badge("승인됨", color_scheme="green", size="1"),
        rx.cond(
            status == "pending",
            rx.badge("검토 대기중", color_scheme="orange", size="1"),
            rx.badge(status, color_scheme="gray", size="1"),
        ),
    )


def my_ingredient_submission_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["ingredient_name"], size="2"),
        rx.cond(
            item["calorie"] != None,  # noqa: E711
            rx.text(f"{item['calorie']}kcal", size="1", color="gray"),
        ),
        rx.spacer(),
        ingredient_submission_status_badge(item["status"]),
        width="100%",
        align="center",
    )


def ingredient_submission_section() -> rx.Component:
    return rx.vstack(
        rx.button(
            rx.cond(State.show_ingredient_submission_form, "재료 정보 등록 닫기", "찾는 재료가 없나요? 직접 등록"),
            size="2", variant="soft", on_click=State.toggle_ingredient_submission_form,
        ),
        rx.cond(
            State.show_ingredient_submission_form,
            rx.vstack(
                rx.text(
                    "공식 DB에 이미 있는 이름이면 검토 대기 상태로 등록됩니다.",
                    size="1", color="gray",
                ),
                labeled_input("재료 이름", "ingredient_submission_name", "예: 수제 두부"),
                labeled_input("칼로리 (kcal/100g)", "ingredient_submission_calorie", "예: 80"),
                labeled_input("탄수화물 (g/100g)", "ingredient_submission_carbs", "예: 2"),
                labeled_input("단백질 (g/100g)", "ingredient_submission_protein", "예: 8"),
                labeled_input("지방 (g/100g)", "ingredient_submission_fat", "예: 4"),
                labeled_input("나트륨 (mg/100g)", "ingredient_submission_sodium", "예: 5"),
                labeled_input("가격 (원/100g)", "ingredient_submission_price", "예: 150"),
                rx.cond(
                    State.ingredient_submission_error != "",
                    rx.callout(State.ingredient_submission_error, color_scheme="red", width="100%"),
                ),
                rx.button(
                    "등록하기", on_click=State.submit_ingredient_info,
                    loading=State.ingredient_submission_submitting,
                ),
                rx.cond(
                    State.my_ingredient_submissions_error != "",
                    rx.callout(State.my_ingredient_submissions_error, color_scheme="red", width="100%"),
                ),
                rx.cond(
                    State.my_ingredient_submissions.length() > 0,
                    rx.vstack(
                        rx.text("내가 등록한 재료", size="2", weight="bold", color="gray"),
                        rx.foreach(State.my_ingredient_submissions, my_ingredient_submission_row),
                        width="100%", spacing="2",
                    ),
                ),
                width="100%", spacing="3",
            ),
        ),
        width="100%", spacing="3",
    )


def seasonal_section() -> rx.Component:
    return rx.cond(
        State.seasonal_ingredients.length() > 0,
        rx.vstack(
            rx.divider(),
            rx.heading("이 달의 제철 재료", size="4"),
            rx.hstack(
                rx.foreach(State.seasonal_ingredients, lambda name: rx.badge(name, color_scheme="orange")),
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                State.seasonal_matches.length() > 0,
                rx.hstack(
                    rx.text("보유 재료 중 제철 품목:", size="2", color="grass"),
                    rx.foreach(State.seasonal_matches, lambda name: rx.badge(name, color_scheme="grass")),
                    wrap="wrap",
                    width="100%",
                ),
            ),
            rx.cond(
                State.seasonal_error != "",
                rx.callout(State.seasonal_error, color_scheme="red", width="100%"),
            ),
            width="100%",
            spacing="2",
        ),
    )


def quick_add_chip(name: str) -> rx.Component:
    """누르면 즉시 냉장고에 추가되는 원탭 칩 - 예전 카테고리 그리드의 "선택 후 확인" 2단계를 없앴다."""
    return rx.badge(
        rx.hstack(rx.icon("plus", size=12), rx.text(name, size="2"), spacing="1", align="center"),
        color_scheme="grass", variant="soft", size="2", cursor="pointer",
        on_click=lambda: State.add_ingredient_from_catalog(name),
    )


def quick_add_chips_section() -> rx.Component:
    return rx.cond(
        State.quick_add_names.length() > 0,
        rx.vstack(
            rx.text("빠른 추가 (누르면 바로 담겨요)", size="2", weight="bold", color="gray"),
            rx.hstack(
                rx.foreach(State.quick_add_names, quick_add_chip),
                wrap="wrap", spacing="2",
            ),
            width="100%", spacing="2", align="start",
        ),
    )


def pantry_photo_ingredient_chip(name: str) -> rx.Component:
    return rx.badge(
        name,
        color_scheme=rx.cond(State.pantry_photo_selected.contains(name), "grass", "gray"),
        variant=rx.cond(State.pantry_photo_selected.contains(name), "solid", "soft"),
        size="2",
        cursor="pointer",
        on_click=lambda: State.toggle_pantry_photo_ingredient(name),
    )


def pantry_photo_upload_section() -> rx.Component:
    return rx.vstack(
        rx.cond(
            State.pantry_photo_detected.length() == 0,
            rx.upload(
                rx.vstack(
                    rx.icon("camera", size=28, color=rx.color("grass", 9)),
                    rx.text("냉장고 사진을 올리면 AI가 재료를 찾아드려요", size="2", color="gray"),
                    rx.text("클릭하거나 파일을 끌어다 놓으세요", size="1", color="gray"),
                    align="center", spacing="2", padding="4",
                ),
                id="pantry_photo_upload",
                accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"]},
                max_files=1,
                border=f"2px dashed {rx.color('grass', 7)}",
                border_radius="12px",
                width="100%",
                on_drop=State.handle_pantry_photo_upload(
                    rx.upload_files(upload_id="pantry_photo_upload")
                ),
            ),
        ),
        rx.cond(
            State.pantry_photo_uploading,
            rx.hstack(rx.spinner(size="2"), rx.text("사진에서 재료를 인식하는 중...", size="2"), align="center"),
        ),
        rx.cond(
            State.pantry_photo_error != "",
            rx.callout(State.pantry_photo_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.pantry_photo_detected.length() > 0,
            rx.vstack(
                rx.text("인식된 재료 - 추가할 것을 선택하세요", size="2", weight="bold", color="gray"),
                rx.hstack(
                    rx.foreach(State.pantry_photo_detected, pantry_photo_ingredient_chip),
                    wrap="wrap", spacing="2",
                ),
                rx.button(
                    f"선택한 재료 추가하기 ({State.pantry_photo_selected.length()}개)",
                    on_click=State.confirm_pantry_photo_ingredients,
                    width="100%", size="3",
                    disabled=State.pantry_photo_selected.length() == 0,
                ),
                width="100%", spacing="3",
            ),
        ),
        width="100%", spacing="3",
    )


def pantry_quick_add_bar() -> rx.Component:
    """검색 겸 추가 입력줄 하나로 통합: 검색하면 카탈로그 결과에서 원탭 추가, 결과에
    없으면 적은 이름 그대로 바로 추가. 사진 인식은 카메라 버튼으로 펼친다."""
    return rx.vstack(
        rx.hstack(
            rx.input(
                placeholder="재료 이름 검색 또는 입력 (예: 두부)",
                value=State.catalog_keyword,
                on_change=lambda v: State.set_field("catalog_keyword", v),
                on_key_down=lambda k: rx.cond(k == "Enter", State.search_catalog(), rx.noop()),
                width="100%",
            ),
            rx.button("검색", on_click=State.search_catalog, loading=State.catalog_searching),
            rx.icon_button(
                rx.icon("camera", size=18),
                variant=rx.cond(State.show_photo_upload, "solid", "soft"),
                on_click=State.toggle_photo_upload,
            ),
            width="100%",
        ),
        rx.cond(
            State.show_photo_upload,
            pantry_photo_upload_section(),
        ),
        rx.cond(
            State.catalog_error != "",
            rx.callout(State.catalog_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.catalog_results.length() > 0,
            rx.vstack(
                rx.text(f"검색 결과 {State.catalog_total}건 중 일부", size="2", color="gray"),
                rx.foreach(State.catalog_results, catalog_result_row),
                width="100%", spacing="2",
            ),
        ),
        rx.cond(
            State.catalog_keyword.strip() != "",
            rx.button(
                f'"{State.catalog_keyword}" 바로 추가',
                size="2", variant="soft", width="100%",
                on_click=State.add_ingredient_by_keyword,
            ),
        ),
        quick_add_chips_section(),
        width="100%", spacing="3",
    )


def profile_summary_row(label: str, value) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", color="gray", width="88px", flex_shrink="0"),
        rx.text(value, size="2"),
        width="100%", align="start",
    )


def home_profile_section() -> rx.Component:
    """홈 화면의 내 프로필 카드. 평소에는 요약을 보여주고, 수정을 누르면 온보딩과 같은
    필드 전체(유저 정보·알레르기·영양제·병력 포함)를 한 화면 폼으로 펼쳐 저장한다."""
    summary = rx.vstack(
        rx.hstack(
            rx.heading("내 프로필", size="4"),
            rx.spacer(),
            rx.button("수정", size="1", variant="soft", on_click=State.toggle_profile_edit),
            width="100%", align="center",
        ),
        profile_summary_row("기본 정보", f"{State.gender} · {State.age_group} · {State.household_size}인 가구"),
        profile_summary_row("건강 목표", rx.cond(State.health_goal != "", State.health_goal, "미입력")),
        profile_summary_row("요리 수준", State.cooking_level),
        rx.hstack(
            rx.text("알레르기", size="2", color="gray", width="88px", flex_shrink="0"),
            rx.cond(
                State.allergy_items.length() > 0,
                rx.hstack(
                    rx.foreach(State.allergy_items, lambda a: rx.badge(a, color_scheme="red", variant="soft")),
                    wrap="wrap",
                ),
                rx.text("없음", size="2"),
            ),
            width="100%", align="start",
        ),
        rx.hstack(
            rx.text("영양제", size="2", color="gray", width="88px", flex_shrink="0"),
            rx.cond(
                State.supplement_items.length() > 0,
                rx.hstack(
                    rx.foreach(State.supplement_items, lambda s: rx.badge(s, color_scheme="blue", variant="soft")),
                    wrap="wrap",
                ),
                rx.text("없음", size="2"),
            ),
            width="100%", align="start",
        ),
        profile_summary_row("병력 정보", rx.cond(State.medical_conditions != "", State.medical_conditions, "없음")),
        align="start", spacing="2", width="100%",
    )

    edit_form = rx.vstack(
        rx.hstack(
            rx.heading("프로필 수정", size="4"),
            rx.spacer(),
            rx.button("취소", size="1", variant="soft", color_scheme="gray", on_click=State.toggle_profile_edit),
            width="100%", align="center",
        ),
        labeled_select("성별", "gender", GENDER_OPTIONS),
        labeled_input("연령대", "age_group", "예: 20대"),
        chip_input(
            "알레르기 (선택)", State.allergy_items, "allergy_chip_input", State.allergy_chip_input,
            State.add_allergy_chip, State.remove_allergy_chip, "예: 새우, 땅콩",
        ),
        chip_input(
            "복용 중인 영양제 (선택)", State.supplement_items, "supplement_chip_input",
            State.supplement_chip_input, State.add_supplement_chip, State.remove_supplement_chip,
            "예: 종합비타민",
        ),
        labeled_input("건강 목표", "health_goal", "예: 체중감량"),
        labeled_input("이용 목적", "purpose", "예: 자취생 식단관리"),
        labeled_select("요리 수준", "cooking_level", COOKING_LEVEL_OPTIONS),
        labeled_input("가구 인원", "household_size", "숫자로 입력"),
        labeled_select("메뉴 선호", "novelty_pref", NOVELTY_OPTIONS),
        labeled_input("보유 조리도구 (콤마로 구분)", "cooking_tools", "예: 가스레인지,전자레인지"),
        labeled_input("병력 정보 (선택)", "medical_conditions", "없으면 비워두세요"),
        rx.cond(
            State.error_message != "",
            rx.callout(State.error_message, color_scheme="red", width="100%"),
        ),
        rx.button(
            "저장", on_click=State.save_profile_edits, loading=State.is_submitting,
            width="100%",
        ),
        align="start", spacing="3", width="100%",
    )

    return rx.card(
        rx.cond(State.profile_edit_mode, edit_form, summary),
        width="100%", variant="surface",
    )


def home_view() -> rx.Component:
    return rx.vstack(
        rx.heading("안녕하세요!", size="6"),
        rx.text("오늘 뭐 먹을지 고민되시나요? 냉장고 속 재료로 추천해드릴게요.", size="2", color="gray"),
        home_profile_section(),
        seasonal_section(),
        popular_videos_section(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def fridge_view() -> rx.Component:
    return rx.vstack(
        rx.heading("내 냉장고", size="6"),
        pantry_quick_add_bar(),
        rx.cond(
            State.pantry_error != "",
            rx.callout(State.pantry_error, color_scheme="red", width="100%"),
        ),
        rx.divider(),
        rx.heading(f"보유 재료 ({State.pantry_items.length()}개)", size="4"),
        rx.cond(
            State.pantry_items.length() > 0,
            rx.vstack(
                rx.foreach(State.pantry_items, pantry_item_row),
                width="100%",
                spacing="2",
            ),
            rx.text("아직 등록된 재료가 없습니다. 위에서 검색하거나 칩을 눌러 담아보세요.", color="gray", size="2"),
        ),
        ingredient_submission_section(),
        favorite_ingredients_section(),
        safety_result_panel(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def recommend_view() -> rx.Component:
    return rx.vstack(
        recommendation_section(),
        width="100%",
        max_width="480px",
    )


def community_view() -> rx.Component:
    # 인기 레시피 영상은 홈 화면으로 이동했다(2026-07-19 사용자 요청) - 여기는 즐겨찾기만 남긴다.
    return rx.vstack(
        favorites_list_view(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def mypage_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("마이페이지", size="6"),
            rx.spacer(),
            rx.button("로그아웃", on_click=State.logout, variant="soft", color_scheme="red", size="2"),
            width="100%",
            align="center",
        ),
        rx.text(f"user_id = {State.submitted_user_id}", color="gray", size="2"),
        my_recipes_view(),
        rx.divider(),
        admin_view(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def main_area() -> rx.Component:
    return rx.cond(
        State.submitted_user_id != None,  # noqa: E711
        rx.cond(
            State.profile_complete,
            rx.cond(
                State.selected_recipe != None,  # noqa: E711
                recipe_detail_view(),
                rx.match(
                    State.main_tab,
                    ("fridge", fridge_view()),
                    ("recommend", recommend_view()),
                    ("community", community_view()),
                    ("mypage", mypage_view()),
                    home_view(),
                ),
            ),
            onboarding_form(),
        ),
        auth_form(),
    )


def bottom_nav_button(label: str, icon_name: str, tab_key: str, extra_events: list | None = None) -> rx.Component:
    events = [State.set_main_tab(tab_key)] + (extra_events or [])
    return rx.button(
        rx.vstack(rx.icon(icon_name, size=18), rx.text(label, size="1"), spacing="0"),
        variant=rx.cond(State.main_tab == tab_key, "solid", "ghost"),
        on_click=events, flex="1",
    )


def bottom_nav() -> rx.Component:
    return rx.cond(
        (State.submitted_user_id != None) & (State.profile_complete) & (State.selected_recipe == None),  # noqa: E711
        rx.hstack(
            bottom_nav_button("홈", "house", "home"),
            bottom_nav_button("냉장고", "refrigerator", "fridge"),
            bottom_nav_button("추천", "sparkles", "recommend"),
            bottom_nav_button("커뮤니티", "users", "community"),
            bottom_nav_button("마이페이지", "user", "mypage"),
            width="100%",
            max_width="480px",
            position="fixed",
            bottom="0",
            left="50%",
            transform="translateX(-50%)",
            background="var(--color-panel-solid)",
            border_top="1px solid var(--gray-5)",
            padding_y="2",
            justify="center",
        ),
    )


def app_header() -> rx.Component:
    return rx.hstack(
        rx.image(src="/logo.svg", height="64px"),
        rx.spacer(),
        rx.color_mode.button(),
        width="100%",
        max_width="480px",
        align="center",
        padding_y="2",
    )


def loading_overlay() -> rx.Component:
    """탭 전환·레시피 상세 진입처럼 데이터를 새로 불러오는 동안 화면이 멈춘 것처럼
    보이지 않도록 잠깐 띄우는 전체 화면 오버레이(2026-07-19 추가)."""
    return rx.cond(
        State.is_page_loading,
        rx.center(
            rx.vstack(
                rx.spinner(size="3"),
                rx.text("불러오는 중...", size="2", color="gray"),
                spacing="3", align="center",
            ),
            position="fixed", inset="0",
            background=rx.color("gray", 3, alpha=True),
            z_index="1000",
        ),
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            app_header(),
            main_area(),
            spacing="5",
            justify="center",
            align="center",
            min_height="85vh",
            padding_bottom="8em",
        ),
        bottom_nav(),
        loading_overlay(),
    )


app = rx.App(
    html_lang="ko",
    head_components=[
        rx.el.link(rel="manifest", href="/manifest.json"),
        rx.el.meta(name="theme-color", content="#3f7d55"),
        rx.el.link(rel="apple-touch-icon", href="/icon.svg"),
    ],
)
app.add_page(index, on_load=State.register_service_worker)
