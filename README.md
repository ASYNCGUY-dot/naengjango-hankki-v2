# 냉장고 한끼 V2
- DONGA KDT AI AGENT 2nd persnal project-v2

냉장고 속 재료와 사용자 건강정보(나이·성별·식단 목적·복용 영양제·병력)를 입력하면
영양성분을 고려한 맞춤 레시피를 추천하고, 가격·안전 정보까지 함께 제공하는 서비스입니다.

## V1과의 관계

[naengjango-hankki-v1](https://github.com/ASYNCGUY-dot/naengjango-hankki-v1)에서 검증한 에이전트 로직을 이어받아,
Streamlit 프로토타입의 UI 구조적 한계(모바일 UI 자유도, 동시접속 성능, 상태관리)를 벗어나기 위해
FastAPI + Reflex 기반 프로덕션 아키텍처로 재구축한 버전입니다.

## 핵심 기능 — 공공데이터 6종 연동 (전부 실동작 확인)

| 데이터소스 | 처리 모듈 | 연결 라우터 | 용도 |
|---|---|---|---|
| 식약처 조리식품 레시피DB | `recommendation_agent.py`, `user_recipe_agent.py` | `api/routers/recommendation.py` | 레시피 추천 |
| 식약처 식품영양성분DB | `ingredient_catalog_agent.py`, `ingredient_agent.py` | `api/routers/ingredient_catalog.py` | 재료 검색·영양정보 |
| 농림수산식품교육문화정보원 재료정보 | `portion_agent.py` (`recipe_ingredients` 테이블) | - | 레시피 상세 재료 수량 |
| 식약처 회수·판매중지 정보 | `safety_agent.py` | `api/routers/safety.py` | 안전정보 확인 대시보드 |
| KAMIS 가격정보 | `price_agent.py` | `api/routers/price.py` | 가격 등급 카드 |
| YouTube Data API | `youtube_agent.py` → `popular_recipe_agent.py`(캐시) | `api/routers/popular_videos.py` | 인기 조리영상 (캐시는 `scripts/refresh_popular_videos.py`로 주기 갱신, 할당량 관리를 위한 의도된 설계) |

## 추천 이유 생성 방식

V1에서 실험했던 LangGraph 기반 LLM 추천이유 생성(`recommendation_graph.py`)은 현재 어떤 라우터에도 연결되어 있지 않습니다.
V2의 추천 이유는 영양군·수치 기반 규칙 로직으로 동작합니다.

## 아직 연결되지 않은 기능 (의도적 보류)

- **이메일 알림**(`notify_agent.py`): 개발 환경(Cowork 샌드박스)의 SMTP 제한으로 보류
- **tagging_agent.py**: 레시피DB 최초 적재용 일회성 배치 스크립트로, 라이브 서비스에 연결될 필요가 없는 종류

## 아키텍처

- `src/agents/` : 27개 파일 (이 중 `_agent.py` 접미사가 붙은 실제 에이전트 모듈 23개, 나머지는 `crypto_utils.py`·`clean_recipe_tags.py` 등 유틸리티/일회성 스크립트)
- `api/` : FastAPI 라우터
- `migration/` : SQLite → PostgreSQL 마이그레이션
- `tests/` : pytest
- `.github/workflows/` : CI

## 기술 스택

- **Backend**: Python, FastAPI, Reflex
- **AI**: OpenAI API
- **DB**: PostgreSQL (psycopg2)
- **Infra**: GitHub Actions(CI), Render(배포)
- **Test**: pytest

## 실행 방법

\`\`\`bash
git clone https://github.com/ASYNCGUY-dot/naengjango-hankki-v2.git
cd naengjango-hankki-v2
pip install -r requirements.txt
# .env 파일에 API 키 설정 (예: OPENAI_API_KEY, DATABASE_URL 등)
reflex run
\`\`\`
