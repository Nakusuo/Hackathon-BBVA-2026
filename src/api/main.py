
from fastapi import FastAPI
from src.api.routers import recommendations
from src.api.routers.events import router as events_router
from src.api.routers.simulations import router as simulations_router
from src.api.routers.fx import router as fx_router

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