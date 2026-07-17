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

    recipe_favorited: bool = False
    favorite_error: str = ""

    substitution_coverage: dict = {}
    substitution_missing: list[dict] = []
    substitution_error: str = ""

    review_rating: str = "5"
    review_text_input: str = ""
    reviews_list: list[dict] = []
    review_summary: str = ""
    review_error: str = ""
    submitting_review: bool = False
    summarizing: bool = False

    favorites_list: list[dict] = []
    favorites_error: str = ""
    loading_favorites: bool = False
    showing_favorites: bool = False

    popular_categories: list[str] = []
    popular_videos_list: list[dict] = []
    selected_popular_category: str = ""
    popular_error: str = ""

    catalog_keyword: str = ""
    catalog_results: list[dict] = []
    catalog_total: int = 0
    catalog_error: str = ""
    catalog_searching: bool = False

    my_recipes_list: list[dict] = []
    my_recipes_error: str = ""
    loading_my_recipes: bool = False
    showing_my_recipes: bool = False
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
    showing_admin: bool = False
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
            self._fetch_popular_categories()
            self._fetch_seasonal()
        else:
            self.error_message = f"저장 실패 ({response.status_code}): {response.text}"
        self.is_submitting = False

    def _fetch_seasonal(self):
        try:
            response = requests.get(f"{API_BASE}/seasonal/{self.submitted_user_id}/matches", timeout=10)
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
            self._fetch_seasonal()
        else:
            self.pantry_error = f"추가 실패 ({response.status_code})"

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
                f"{API_BASE}/pantry/{self.submitted_user_id}", json=payload, timeout=10
            )
        except requests.RequestException as e:
            self.pantry_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self._fetch_pantry()
            self._fetch_seasonal()
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
            self._fetch_seasonal()
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
            self.review_summary = ""
            self.review_error = ""
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
        else:
            self.recipe_detail_error = f"조회 실패 ({response.status_code})"

    def _fetch_like_status(self, recipe_id: int):
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/like",
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, json=payload, timeout=10,
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
    def open_admin(self):
        self.showing_admin = True
        self.showing_favorites = False
        self.showing_my_recipes = False
        if self.is_admin:
            self._fetch_admin_pending()

    @rx.event
    def close_admin(self):
        self.showing_admin = False

    def _fetch_admin_pending(self):
        self.admin_loading = True
        self.admin_error = ""
        try:
            r1 = requests.get(
                f"{API_BASE}/admin/pending-recipes", params={"user_id": self.submitted_user_id}, timeout=10
            )
            r2 = requests.get(
                f"{API_BASE}/admin/pending-ingredients", params={"user_id": self.submitted_user_id}, timeout=10
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
                params={"user_id": self.submitted_user_id}, json={"code": self.admin_code_input}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
        try:
            response = requests.get(
                f"{API_BASE}/recommendation/recipes/{recipe_id}/substitution",
                params={"user_id": self.submitted_user_id},
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

    @rx.event
    def back_to_recommendations(self):
        self.selected_recipe = None
        self.recipe_steps = []
        self.reviews_list = []
        self.review_summary = ""
        self.substitution_coverage = {}
        self.substitution_missing = []

    def _check_favorited(self, recipe_id: int):
        try:
            response = requests.get(f"{API_BASE}/favorites/{self.submitted_user_id}", timeout=10)
        except requests.RequestException:
            return
        if response.status_code == 200:
            self.recipe_favorited = any(f["id"] == recipe_id for f in response.json())

    @rx.event
    def toggle_favorite(self):
        recipe_id = self.selected_recipe["id"]
        try:
            response = requests.post(
                f"{API_BASE}/favorites/{self.submitted_user_id}/{recipe_id}/toggle", timeout=10
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
        else:
            self.review_error = f"조회 실패 ({response.status_code})"

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
        }
        try:
            response = requests.post(f"{API_BASE}/reviews/{recipe_id}", json=payload, timeout=10)
        except requests.RequestException as e:
            self.review_error = f"서버에 연결할 수 없습니다: {e}"
            self.submitting_review = False
            return
        if response.status_code == 200:
            self.review_text_input = ""
            self._fetch_reviews(recipe_id)
        else:
            self.review_error = f"등록 실패 ({response.status_code})"
        self.submitting_review = False

    @rx.event
    def get_review_summary(self):
        self.summarizing = True
        recipe_id = self.selected_recipe["id"]
        try:
            response = requests.get(f"{API_BASE}/reviews/{recipe_id}/summary", timeout=30)
        except requests.RequestException as e:
            self.review_error = f"서버에 연결할 수 없습니다: {e}"
            self.summarizing = False
            return
        if response.status_code == 200:
            self.review_summary = response.json()["summary"] or "아직 요약할 후기가 없습니다."
        else:
            self.review_error = f"요약 실패 ({response.status_code})"
        self.summarizing = False

    @rx.event
    def load_favorites(self):
        self.loading_favorites = True
        self.favorites_error = ""
        try:
            response = requests.get(f"{API_BASE}/favorites/{self.submitted_user_id}", timeout=10)
        except requests.RequestException as e:
            self.favorites_error = f"서버에 연결할 수 없습니다: {e}"
            self.loading_favorites = False
            return
        if response.status_code == 200:
            self.favorites_list = response.json()
            self.showing_favorites = True
            self.showing_my_recipes = False
            self.showing_admin = False
        else:
            self.favorites_error = f"조회 실패 ({response.status_code})"
        self.loading_favorites = False

    @rx.event
    def close_favorites(self):
        self.showing_favorites = False
        self.showing_my_recipes = False
        self.showing_admin = False

    def _fetch_my_recipes(self):
        try:
            response = requests.get(
                f"{API_BASE}/my-recipes", params={"user_id": self.submitted_user_id}, timeout=10
            )
        except requests.RequestException as e:
            self.my_recipes_error = f"서버에 연결할 수 없습니다: {e}"
            return
        if response.status_code == 200:
            self.my_recipes_list = response.json()
            self.my_recipes_error = ""
        else:
            self.my_recipes_error = f"조회 실패 ({response.status_code})"

    @rx.event
    def load_my_recipes(self):
        self.loading_my_recipes = True
        self._fetch_my_recipes()
        self.showing_favorites = False
        self.showing_my_recipes = True
        self.showing_admin = False
        self.loading_my_recipes = False

    def _reset_my_recipe_form(self):
        self.my_recipe_menu_name = ""
        self.my_recipe_category = ""
        self.my_recipe_calorie = ""
        self.my_recipe_ingredients = ""
        self.my_recipe_steps = ""
        self.my_recipe_editing_id = None
        self.my_recipe_form_error = ""

    @rx.event
    def close_my_recipes(self):
        self.showing_my_recipes = False
        self._reset_my_recipe_form()

    @rx.event
    def start_edit_my_recipe(self, recipe_id: int):
        try:
            response = requests.get(
                f"{API_BASE}/my-recipes/{recipe_id}",
                params={"user_id": self.submitted_user_id}, timeout=10,
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
                    params={"user_id": self.submitted_user_id}, json=payload, timeout=10,
                )
            else:
                response = requests.post(
                    f"{API_BASE}/my-recipes",
                    params={"user_id": self.submitted_user_id}, json=payload, timeout=10,
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
                params={"user_id": self.submitted_user_id}, timeout=10,
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
    return rx.card(
        rx.hstack(
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
        ),
        width="100%",
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
            rx.text(
                f"{item['category']} · {item['calorie']}kcal · 겹치는 재료 {item['ingredient_overlap']}개",
                size="2",
                color="gray",
            ),
            rx.button("상세보기 (조리단계)", size="2", width="100%",
                      on_click=lambda: State.view_recipe(item["id"])),
            spacing="2",
            width="100%",
        ),
        width="100%",
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


def review_row(r: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(r["username"], weight="bold", size="2"),
                rx.badge(f"★ {r['rating']}/5", color_scheme="amber"),
            ),
            rx.text(r["review_text"], size="2"),
            width="100%",
            spacing="1",
        ),
        width="100%",
    )


def review_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("후기", size="4"),
        rx.cond(
            State.review_error != "",
            rx.callout(State.review_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.reviews_list.length() > 0,
            rx.vstack(rx.foreach(State.reviews_list, review_row), width="100%"),
            rx.text("아직 후기가 없습니다.", color="gray", size="2"),
        ),
        rx.button(
            "AI 후기 요약 보기",
            size="2",
            variant="soft",
            loading=State.summarizing,
            on_click=State.get_review_summary,
        ),
        rx.cond(
            State.review_summary != "",
            rx.callout(State.review_summary, color_scheme="blue", width="100%"),
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
        rx.button(
            "후기 등록",
            on_click=State.submit_review,
            loading=State.submitting_review,
            width="100%",
        ),
        width="100%",
        spacing="3",
    )


def missing_ingredient_row(m: dict) -> rx.Component:
    color = rx.cond(
        m["type"] == "omit",
        "gray",
        rx.cond(m["type"] == "substitute", "grass", "amber"),
    )
    return rx.hstack(
        rx.badge(m["ingredient"], color_scheme=color),
        rx.text(m["suggestion"], size="2", color="gray"),
        width="100%",
        align="center",
    )


def substitution_section() -> rx.Component:
    return rx.cond(
        State.substitution_coverage,
        rx.vstack(
            rx.divider(),
            rx.hstack(
                rx.heading("재료 정보", size="4"),
                rx.spacer(),
                rx.cond(
                    State.substitution_coverage["coverage_pct"] != None,  # noqa: E711
                    rx.badge(
                        f"보유 재료 사용률 {State.substitution_coverage['coverage_pct']}%",
                        color_scheme="grass",
                        size="2",
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                State.substitution_error != "",
                rx.callout(State.substitution_error, color_scheme="red", width="100%"),
            ),
            rx.cond(
                State.substitution_missing.length() > 0,
                rx.vstack(
                    rx.text("부족한 재료 / 대체·생략 안내", size="2", weight="bold", color="gray"),
                    rx.foreach(State.substitution_missing, missing_ingredient_row),
                    width="100%",
                    spacing="2",
                ),
                rx.text("필요한 재료를 전부 보유하고 있습니다!", color="grass", size="2"),
            ),
            width="100%",
            spacing="2",
        ),
    )


def price_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.cond(
            State.price_fetched,
            rx.vstack(
                rx.hstack(
                    rx.heading("예상 재료비", size="4"),
                    rx.spacer(),
                    rx.badge(
                        State.price_tier,
                        color_scheme=rx.cond(
                            State.price_tier == "프리미엄", "red",
                            rx.cond(State.price_tier == "가성비", "green", "gray"),
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.text(
                    f"포함된 재료 기준 약 {State.price_total_cost}원 · 참고용, 최신 가격은 KAMIS 등에서 재확인 권장",
                    size="2", color="gray",
                ),
                width="100%", spacing="2",
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


def recipe_detail_view() -> rx.Component:
    return rx.vstack(
        rx.button("← 추천 목록으로", size="2", variant="soft", on_click=State.back_to_recommendations),
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
            State.selected_recipe["youtube_url"],
            rx.link("▶ 유튜브에서 조리 영상 보기", href=State.selected_recipe["youtube_url"],
                     is_external=True, color=rx.color("grass", 11), weight="bold"),
        ),
        rx.cond(
            State.favorite_error != "",
            rx.callout(State.favorite_error, color_scheme="red", width="100%"),
        ),
        rx.cond(
            State.recipe_detail_error != "",
            rx.callout(State.recipe_detail_error, color_scheme="red", width="100%"),
        ),
        substitution_section(),
        price_section(),
        nutrition_section(),
        shopping_section(),
        rx.heading("조리 단계", size="4"),
        rx.vstack(
            rx.foreach(State.recipe_steps, recipe_step_row),
            width="100%",
            spacing="1",
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
            rx.text(f"{item['category']} · {item['calorie']}kcal", size="2", color="gray"),
            rx.spacer(),
            rx.button(
                "상세보기",
                size="1",
                on_click=lambda: [State.close_favorites(), State.view_recipe(item["id"])],
            ),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def favorites_list_view() -> rx.Component:
    return rx.vstack(
        rx.button("← 돌아가기", size="2", variant="soft", on_click=State.close_favorites),
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
                rx.text(f"{item['category']} · {item['calorie']}kcal", size="2", color="gray"),
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
        rx.button("← 돌아가기", size="2", variant="soft", on_click=State.close_my_recipes),
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
                rx.text(f"{item['category']} · {item['calorie']}kcal · by {item['username']}", size="1", color="gray"),
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
                rx.text(f"{item['calorie']}kcal · by {item['username']}", size="1", color="gray"),
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
        rx.button("← 돌아가기", size="2", variant="soft", on_click=State.close_admin),
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


def catalog_search_section() -> rx.Component:
    return rx.vstack(
        rx.divider(),
        rx.heading("재료 찾아보기", size="6"),
        rx.hstack(
            rx.input(
                placeholder="재료 이름으로 검색 (예: 두부)",
                value=State.catalog_keyword,
                on_change=lambda v: State.set_field("catalog_keyword", v),
                width="100%",
            ),
            rx.button("검색", on_click=State.search_catalog, loading=State.catalog_searching),
            width="100%",
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
                width="100%",
                spacing="2",
            ),
        ),
        width="100%",
        spacing="3",
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
        rx.text(f"{item['calorie']}kcal", size="1", color="gray"),
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


def pantry_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("내 냉장고", size="6"),
            rx.spacer(),
            rx.button(
                "즐겨찾기 보기",
                size="2",
                variant="soft",
                loading=State.loading_favorites,
                on_click=State.load_favorites,
            ),
            width="100%",
        ),
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
        seasonal_section(),
        catalog_search_section(),
        ingredient_submission_section(),
        rx.cond(
            State.safety_error != "",
            rx.callout(State.safety_error, color_scheme="red", width="100%"),
        ),
        safety_result_panel(),
        recommendation_section(),
        popular_videos_section(),
        spacing="4",
        width="100%",
        max_width="480px",
    )


def main_area() -> rx.Component:
    return rx.cond(
        State.submitted_user_id != None,  # noqa: E711
        rx.cond(
            State.showing_favorites,
            favorites_list_view(),
            rx.cond(
                State.showing_my_recipes,
                my_recipes_view(),
                rx.cond(
                    State.showing_admin,
                    admin_view(),
                    rx.cond(State.selected_recipe != None, recipe_detail_view(), pantry_section()),  # noqa: E711
                ),
            ),
        ),
        onboarding_form(),
    )


def bottom_nav() -> rx.Component:
    return rx.cond(
        (State.submitted_user_id != None) & (State.selected_recipe == None),  # noqa: E711
        rx.hstack(
            rx.button(
                rx.vstack(rx.icon("refrigerator", size=18), rx.text("냉장고", size="1"), spacing="0"),
                variant="ghost", on_click=State.close_favorites, flex="1",
            ),
            rx.button(
                rx.vstack(rx.icon("sparkles", size=18), rx.text("추천", size="1"), spacing="0"),
                variant="ghost", on_click=State.get_recommendations, flex="1",
            ),
            rx.button(
                rx.vstack(rx.icon("heart", size=18), rx.text("즐겨찾기", size="1"), spacing="0"),
                variant="ghost", on_click=State.load_favorites, flex="1",
            ),
            rx.button(
                rx.vstack(rx.icon("book-open", size=18), rx.text("내레시피", size="1"), spacing="0"),
                variant="ghost", on_click=State.load_my_recipes, flex="1",
            ),
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
        rx.cond(
            State.submitted_user_id != None,  # noqa: E711
            rx.icon_button("shield", variant="ghost", size="2", on_click=State.open_admin),
        ),
        rx.color_mode.button(),
        width="100%",
        max_width="480px",
        align="center",
        padding_y="2",
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
