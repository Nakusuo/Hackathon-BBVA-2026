import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.agente import obtener_agente
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
    recommendations,
)


log = logging.getLogger("lucas.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El agente se carga al arrancar para que la primera pregunta del chat no pague esa espera.
    # Si falla (sin base o sin modelos) la API igual levanta: las demás rutas no dependen de él.
    try:
        await asyncio.to_thread(obtener_agente)
    except Exception:
        log.exception("El agente no cargó; /chat lo reintentará en el primer pedido")
    yield


app = FastAPI(
    title="Lucas API",
    description="API REST del asistente financiero Lucas",
    version="0.1.0",
    lifespan=lifespan,
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
