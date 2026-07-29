import reflex as rx

config = rx.Config(
    app_name="naengjango_v2",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        # 디자인 진단 2차(2026-07-26): Radix 기본 "grass"(밝은 라임그린)는 다른 Radix
        # 앱과 시각적으로 구분이 안 됐다. 로고의 짙은 초록(#2f5d40) 브랜드에 더 가깝고
        # 채도가 차분한 "green"으로 바꿔 전체 화면 강조색을 한 번에 교체한다.
        rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="green", radius="large")),
    ]
)