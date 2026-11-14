
from fastapi import FastAPI
from src.api.routers import recommendations
from src.api.routers.events import router as events_router
from src.api.routers.simulations import router as simulations_router
from src.api.routers.fx import router as fx_router
from src.api.routers.goals import router as goals_router
from src.api.routers.offers import router as offers_router
from src.api.routers.expenses import router as expenses_router
from src.api.routers.chat import router as chat_router
from src.api.routers.onboarding import router as onboarding_router

from src.api.routers import (
    health,
    financial_health,
    forecast,
    recommendations
)


app = FastAPI(
    title="Lucas API",
    description="API REST del asistente financiero Lucas",
    version="0.1.0"
)

app.include_router(health.router)
app.include_router(financial_health.router)
app.include_router(forecast.router)
app.include_router(recommendations.router)
app.include_router(events_router)
app.include_router(simulations_router)
app.include_router(fx_router)
app.include_router(goals_router)
app.include_router(offers_router)
app.include_router(expenses_router)
app.include_router(chat_router)
app.include_router(onboarding_router)