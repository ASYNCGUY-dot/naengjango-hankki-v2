"""
냉장고 한끼 - 허깅페이스 Spaces 데모 (로그인 없이 추천 로직만 체험)

실제 서비스는 회원가입 + 5단계 온보딩을 거쳐야 추천 화면에 도달한다. 포트폴리오
링크를 받은 사람 입장에서는 그 과정이 진입 장벽이라, 핵심 가치인 "재료를 넣으면
추천이 나온다"만 떼어내 로그인 없이 바로 보여주는 데모다.

추천 로직은 실제 서비스와 같은 코드(agents/recommendation_agent.py)를 그대로 쓴다.
다만 프로필은 DB에서 읽지 않고 화면 입력값으로 즉석에서 만든다 - 원본 로직이
프로필에서 실제로 참조하는 값은 알레르기 하나뿐이다(recommendation_agent.py 참고).
"""

import json
import sqlite3
import sys
from pathlib import Path

import gradio as gr

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "agents"))

import recommendation_agent  # noqa: E402  (sys.path 설정 후 import해야 한다)

DB_PATH = BASE / "data" / "demo.db"
LIVE_APP_URL = "https://naengjango-hankki-v2-silver-star.reflex.run"
REPO_URL = "https://github.com/ASYNCGUY-dot/naengjango-hankki-v2"

EXAMPLES = [
    ["두부, 양파, 대파", ""],
    ["닭가슴살, 브로콜리, 현미", ""],
    ["돼지고기, 김치, 두부", ""],
    ["계란, 우유, 치즈", "우유"],
]


def _parse_nutrients(nutrients_json):
    """4대 영양소만 뽑아낸다(실제 서비스 api/routers/recommendation.py와 동일한 방식)."""
    if not nutrients_json:
        return {}
    try:
        raw = json.loads(nutrients_json)
    except (ValueError, TypeError):
        return {}
    out = {}
    for key in ("energy_kcal", "protein_g", "fat_g", "carbs_g"):
        value = raw.get(key)
        try:
            out[key] = float(value) if value is not None else None
        except (ValueError, TypeError):
            out[key] = None
    return out


def _nutrition_reason(group, n):
    """실제 서비스의 추천 이유 문구를 그대로 재현한다."""
    protein, carbs, fat = n.get("protein_g"), n.get("carbs_g"), n.get("fat_g")
    if group == "고단백":
        return f"단백질 {protein}g으로 비중이 높아 포만감과 근육 유지에 좋아요." if protein else "단백질 비중이 높은 메뉴예요."
    if group == "고탄수화물":
        return f"탄수화물 {carbs}g으로 활동 에너지원이 풍부해요." if carbs else "탄수화물 비중이 높은 메뉴예요."
    if group == "고지방":
        return f"지방 {fat}g으로 적은 양에도 든든해요." if fat else "지방 비중이 높은 메뉴예요."
    if group == "균형":
        return "탄수화물·단백질·지방이 고르게 갖춰진 균형 잡힌 메뉴예요."
    return f"{group}으로 분류된 메뉴예요."


def _card(item):
    n = _parse_nutrients(item.get("nutrients_json"))
    badge = "✅ 선택 재료 활용" if item.get("qualifies") else "참고용"
    reason = _nutrition_reason(item.get("nutrition_group", "미분류"), n)

    facts = []
    if n.get("energy_kcal") is not None:
        facts.append(f"열량 {n['energy_kcal']}kcal")
    if n.get("protein_g") is not None:
        facts.append(f"단백질 {n['protein_g']}g")
    if n.get("fat_g") is not None:
        facts.append(f"지방 {n['fat_g']}g")
    if n.get("carbs_g") is not None:
        facts.append(f"탄수화물 {n['carbs_g']}g")

    lines = [
        f"### {item['menu_name']}",
        f"**{badge}** · {item.get('category') or '분류 없음'} · 겹치는 재료 {item.get('ingredient_overlap', 0)}개",
        "",
        reason,
    ]
    if facts:
        lines += ["", " · ".join(facts)]
    if item.get("youtube_url"):
        lines += ["", f"[조리 영상 보기]({item['youtube_url']})"]
    return "\n".join(lines)


def recommend(ingredients_text, allergy_text):
    names = [n.strip() for n in (ingredients_text or "").replace("\n", ",").split(",") if n.strip()]
    if not names:
        return "재료를 한 개 이상 입력해주세요. 예: `두부, 양파, 대파`"

    # 프로필은 DB가 아니라 입력값으로 즉석에서 만든다. 원본 로직이 참조하는 건 알레르기뿐이다.
    profile = {"allergy": (allergy_text or "").strip()}

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        candidates = recommendation_agent.get_candidate_recipes(cur, profile)
        scored = recommendation_agent.score_by_ingredients(cur, candidates, names)
    finally:
        conn.close()

    top = scored[:5]
    if not top:
        return "조건에 맞는 추천 결과가 없어요. 재료를 바꾸거나 더 넣어보세요."

    header = f"입력한 재료 **{', '.join(names)}** 기준 상위 {len(top)}개입니다.\n\n---\n"
    return header + "\n\n---\n\n".join(_card(i) for i in top)


with gr.Blocks(title="냉장고 한끼 - 추천 데모") as demo:
    gr.Markdown(
        f"""
# 냉장고 한끼 · AI 메뉴 추천 데모

냉장고에 있는 재료를 넣으면, 공공데이터 기반 레시피 **1,148개** 중에서 그 재료를 가장 잘
활용하는 메뉴를 골라줍니다. 알레르기 재료가 들어간 레시피는 후보에서 아예 제외합니다.

이 데모는 **로그인 없이** 추천 로직만 체험하도록 떼어낸 버전입니다.
냉장고 관리·안전정보·가격비교·즐겨찾기까지 포함된 전체 서비스는 [여기서 볼 수 있습니다]({LIVE_APP_URL}).
"""
    )

    with gr.Row():
        with gr.Column(scale=2):
            ing = gr.Textbox(
                label="가지고 있는 재료",
                placeholder="쉼표로 구분해서 입력하세요. 예: 두부, 양파, 대파",
                lines=2,
            )
        with gr.Column(scale=1):
            allergy = gr.Textbox(
                label="알레르기 재료 (선택)",
                placeholder="예: 우유, 새우",
                lines=2,
            )

    btn = gr.Button("추천 받기", variant="primary")
    out = gr.Markdown()

    gr.Examples(examples=EXAMPLES, inputs=[ing, allergy], label="예시로 바로 해보기")

    btn.click(recommend, inputs=[ing, allergy], outputs=out)
    ing.submit(recommend, inputs=[ing, allergy], outputs=out)

    gr.Markdown(
        f"""
---
**데이터 출처**: 식품의약품안전처 조리식품 레시피DB / 식품영양성분DB,
농림수산식품교육문화정보원 레시피 재료정보.
영양 안내는 일반 정보 제공 목적이며 의료적 진단·처방이 아닙니다.

[전체 서비스]({LIVE_APP_URL}) · [소스 코드]({REPO_URL})
"""
    )

if __name__ == "__main__":
    # Gradio 6부터 theme은 Blocks 생성자가 아니라 launch()에서 받는다.
    demo.launch(theme=gr.themes.Soft(primary_hue="green"))
