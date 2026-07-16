import reflex as rx

config = rx.Config(
    app_name="naengjango_v2",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)