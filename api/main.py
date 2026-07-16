from fastapi import FastAPI

from api.routers import (
    auth,
    favorite,
    ingredient_catalog,
    pantry,
    popular_videos,
    profile,
    recommendation,
    review,
    safety,
    substitution,
)

app = FastAPI(title="냉장고 한끼 V2 API")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(pantry.router)
app.include_router(safety.router)
app.include_router(recommendation.router)
app.include_router(favorite.router)
app.include_router(review.router)
app.include_router(substitution.router)
app.include_router(popular_videos.router)
app.include_router(ingredient_catalog.router)


@app.get("/health")
def health():
    return {"status": "ok"}
