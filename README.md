# 냉장고 한끼 (naengjango-hankki-v2)

냉장고 속 재료와 사용자 정보(나이, 성별, 식단 목적, 섭취 영양제, 병력)를 입력하면
영양성분을 고려해 맞춤 레시피를 추천하는 AI 에이전트 서비스입니다.

## 주요 기능
- 보유 재료 기반 레시피 추천
- 사용자 프로필(나이/성별/식단 목적/영양제/병력) 반영한 영양 맞춤 추천
- LangGraph 기반 에이전트 파이프라인으로 추천 로직 처리

## 기술 스택
- Backend: Python, FastAPI, Reflex
- AI/Agent: LangGraph, OpenAI API (+ Claude, 확인 중)
- DB: PostgreSQL
- Infra: GitHub Actions(CI), Render(배포)
- Test: pytest

## 실행 방법
\`\`\`bash
git clone https://github.com/ASYNCGUY-dot/naengjango-hankki-v2.git
cd naengjango-hankki-v2
pip install -r requirements.txt
# .env 파일에 API 키 설정 (예: OPENAI_API_KEY=...)
reflex run
\`\`\`

## 폴더 구조
- `src/agents/` : AI 에이전트 로직
- `api/` : API 엔드포인트
- `migration/` : DB 마이그레이션
- `tests/` : 테스트 코드
