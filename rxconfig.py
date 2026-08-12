import os

import reflex as rx

config = rx.Config(
    app_name="naengjango_v2",
    # 프론트(Vercel 정적 호스팅)가 접속할 Reflex 백엔드 주소(2026-08-12).
    # Reflex Cloud 배포가 막혀서 백엔드를 Render로 옮겼고, 프론트를 빌드할 때
    # 이 값이 번들에 박힌다. 환경변수로 넘기는 것만으로는 빌드에 반영되지 않아
    # (localhost:8000이 그대로 들어갔다) 여기서 명시적으로 읽는다.
    # 로컬 개발에서는 환경변수가 없으므로 기존 기본값 그대로 동작한다.
    api_url=os.getenv("API_URL", "http://localhost:8000"),
    # 상태 락 만료 상향(2026-08-11). 프로덕션 로그(2026-08-07)에서 로그인이
    # LockExpiredError로 실패하는 게 확인됐다. 원인은 login 이벤트 하나가 백엔드 API를
    # 순차로 여러 번 부르기 때문이다 - 로그인 자체(10초) 뒤에 프로필·냉장고·인기영상·
    # 제철재료·재료즐겨찾기를 이어서 불러오는데, 각 요청 타임아웃이 10초라 최악의 경우
    # 50초를 넘긴다. 백엔드(Render 무료 티어)가 유휴 상태에서 깨어날 때 첫 요청만
    # 50초 가까이 걸리므로 실제로 이 한계를 넘겼다.
    # 기본값 10초로는 부족해서, 가장 오래 걸리는 이벤트(추천: 타임아웃 60초)까지
    # 감안해 120초로 잡는다.
    redis_lock_expiration=120000,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        # 디자인 진단 2차(2026-07-26): Radix 기본 "grass"(밝은 라임그린)는 다른 Radix
        # 앱과 시각적으로 구분이 안 됐다. 로고의 짙은 초록(#2f5d40) 브랜드에 더 가깝고
        # 채도가 차분한 "green"으로 바꿔 전체 화면 강조색을 한 번에 교체한다.
        rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="green", radius="large")),
    ]
)