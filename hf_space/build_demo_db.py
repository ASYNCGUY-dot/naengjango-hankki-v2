"""
허깅페이스 Space 데모용 경량 SQLite를 프로덕션 Postgres에서 뽑아 만든다.

왜 별도 DB를 만드나:
- 데모 Space에 프로덕션 DB 접속 정보(POSTGRES_URL)를 넘기고 싶지 않다. 외부 호스팅에
  실서비스 자격증명을 두지 않는 게 원칙이고, 데모는 읽기 전용이라 애초에 필요가 없다.
- Render 무료 백엔드는 15분 무응답이면 잠들어 첫 요청이 1분씩 걸린다. 데모가 그걸
  거치게 하면 "링크 눌러서 3초 안에 결과를 본다"는 목적 자체가 깨진다.
- 유저 개인정보(users/auth_tokens/reviews 등)는 아예 담지 않는다. 공개 레시피 데이터만.

실행: python hf_space/build_demo_db.py
(프로젝트 루트의 .env에 있는 POSTGRES_URL을 읽는다. 읽기 전용 SELECT만 수행한다.)
"""

import os
import sqlite3
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = Path(__file__).resolve().parent / "data" / "demo.db"

# 추천 로직(recommendation_agent)이 실제로 SELECT하는 4개 테이블만 담는다.
# 스키마는 tests/fixtures/seed.sql과 동일한 SQLite 정의를 그대로 쓴다.
SCHEMA = """
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    menu_name TEXT,
    cook_method TEXT,
    category TEXT,
    calorie REAL,
    nutrients_json TEXT,
    image_url TEXT,
    youtube_url TEXT,
    source_api TEXT,
    steps_json TEXT,
    submitted_by INTEGER,
    status TEXT DEFAULT 'approved'
);
CREATE TABLE recipe_tags (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER,
    tag_type TEXT,
    tag_value TEXT
);
CREATE TABLE recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER,
    name TEXT,
    amount REAL,
    unit TEXT,
    raw_text TEXT,
    base_servings INTEGER
);
-- 유저 등록 레시피의 좋아요 문턱 판정에만 쓰인다. 데모는 승인된 공개 레시피만
-- 담으므로 실제로는 비어 있지만, 쿼리가 참조하므로 테이블 자체는 만들어 둔다.
CREATE TABLE recipe_likes (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER,
    user_id INTEGER,
    created_at TEXT
);
CREATE INDEX idx_tags_recipe ON recipe_tags(recipe_id);
CREATE INDEX idx_ings_recipe ON recipe_ingredients(recipe_id);
"""

COPY_PLAN = [
    (
        "recipes",
        """SELECT id, menu_name, cook_method, category, calorie, nutrients_json,
                  image_url, youtube_url, source_api, steps_json, submitted_by, status
           FROM recipes WHERE status = 'approved'""",
        12,
    ),
    (
        "recipe_tags",
        """SELECT t.id, t.recipe_id, t.tag_type, t.tag_value FROM recipe_tags t
           JOIN recipes r ON r.id = t.recipe_id WHERE r.status = 'approved'""",
        4,
    ),
    (
        "recipe_ingredients",
        """SELECT i.id, i.recipe_id, i.name, i.amount, i.unit, i.raw_text, i.base_servings
           FROM recipe_ingredients i
           JOIN recipes r ON r.id = i.recipe_id WHERE r.status = 'approved'""",
        7,
    ),
]


def main():
    load_dotenv(ROOT / ".env")
    dsn = os.getenv("POSTGRES_URL")
    if not dsn:
        raise SystemExit("POSTGRES_URL이 없습니다. 프로젝트 루트 .env를 확인하세요.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        OUT_PATH.unlink()

    out = sqlite3.connect(OUT_PATH)
    out.executescript(SCHEMA)

    pg = psycopg2.connect(dsn)
    cur = pg.cursor()
    for table, query, ncols in COPY_PLAN:
        cur.execute(query)
        rows = cur.fetchall()
        placeholders = ",".join("?" * ncols)
        out.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        print(f"{table:22s} {len(rows):>7,}행 복사")
    cur.close()
    pg.close()

    out.commit()
    out.execute("VACUUM")
    out.close()

    size_mb = OUT_PATH.stat().st_size / (1024 * 1024)
    print(f"\n생성 완료: {OUT_PATH}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
