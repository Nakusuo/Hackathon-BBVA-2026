"""
Módulo de Carga y Repositorio de Modelos (.pkl) para FastAPI.
Implementa el patrón lifespan para cargar los modelos analíticos en memoria al iniciar,
asegurando baja latencia y acceso seguro desde los endpoints.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
import joblib
from fastapi import FastAPI, HTTPException

# Diccionario global de modelos en memoria RAM
ml_models = {}

# Ruta por defecto donde Diego y el equipo guardan los modelos entrenados
MODELS_DIR = Path("models")

def cargar_modelo(nombre: str):
    """Carga un artefacto .pkl usando joblib de forma segura."""
    ruta = MODELS_DIR / f"{nombre}.pkl"
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el artefacto del modelo en: {ruta}")
    return joblib.load(ruta)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Evento de ciclo de vida (Lifespan) de FastAPI.
    Carga todos los .pkl críticos de la carpeta models/ al iniciar el servidor.
    """
    print("[INFO DX] Iniciando carga de modelos analíticos (.pkl) en memoria...")
    
    modelos_requeridos = ["segmentacion", "pronostico", "glosa", "pronostico_mensual", "sentimiento"]
    
    for mod in modelos_requeridos:
        try:
            if (MODELS_DIR / f"{mod}.pkl").exists():
                ml_models[mod] = cargar_modelo(mod)
                print(f"[OK DX] Modelo cargado exitosamente: {mod}.pkl")
            else:
                print(f"[WARN DX] Modelo no encontrado en disco (pendiente de entrenamiento): {mod}.pkl")
        except Exception as e:
            print(f"[ERROR DX] Falló la carga del modelo {mod}.pkl: {e}")
            
    yield
    
    # Limpieza de memoria al apagar la aplicación
    print("[INFO DX] Liberando modelos analíticos de la memoria RAM...")
    ml_models.clear()


def obtener_modelo(nombre: str):
    """Obtiene un modelo cargado en memoria desde los routers de FastAPI."""
    if nombre not in ml_models:
        raise HTTPException(
            status_code=503, 
            detail=f"El modelo '{nombre}' no está disponible o no se ha cargado en memoria."
        )
    return ml_models[nombre]
