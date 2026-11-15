# Registro de Actividades y Arquitectura de Datos — Dixon Smith Zarzosa Toribio (Rol DX)

**Hackathon BBVA 2026 · Equipo 2 · Copiloto «Lucas»**  
**Rol:** Arquitectura de Datos, Diagramas UML, QA Funcional (ISTQB) y Ciberseguridad (ISO/IEC 27001)  
**Persona:** Dixon Smith Zarzosa Toribio (DX)

---

## 1. Resumen Ejecutivo de la Responsabilidad

Como **Auditor Técnico Principal y Arquitecto de Datos (Rol DX)** del equipo, he liderado el diseño de la persistencia relacional en PostgreSQL, la definición de diagramas de arquitectura de datos y casos de uso UML, el desarrollo de herramientas de carga con baja latencia para modelos analíticos (`.pkl`), la creación de la base de datos oficial del sistema y la supervisión estricta de calidad y seguridad bajo los estándares **ISTQB CTFL v4.0** e **ISO/IEC 27001:2022**.

---

## 2. Entregables Principales Desarrollados

### A. Diccionario de Datos y Arquitectura Relacional (`docs/arquitectura-datos.md` y `data/dictionary.md`)
- **Qué se hizo:** Se diseñó la estructura de base de datos dividida en dos esquemas bien delimitados:
  1. `seguro`: Contiene la tabla `seguro.clientes` con información demográfica, crediticia y de perfilamiento sensible (cifrada con `pgcrypto` y aislada).
  2. `app`: Contiene `app.transacciones`, `app.metas`, `app.memoria` (vectorial para RAG/LangGraph) y `app.respuestas_reco` (retroalimentación de recomendaciones).
- **Por qué:** Cumplimiento del principio de mínimo privilegio e ISO 27001 (Control 5.12 - Clasificación de la Información), impidiendo que roles no autorizados o el LLM lean datos sensibles crudos.
- **Diagramas:** Incluye el esquema Entidad-Relación (ERD) en Mermaid.js y el diagrama de flujo del pipeline sintético e ingesta reproducible (`data/generator.py --seed`).

### B. Inicialización Oficial de Base de Datos (`db/init.sql`)
- **Qué se hizo:** Creación del script SQL idempotente de inicialización para PostgreSQL 16 + `pgvector`.
- **Por qué:** Establece la infraestructura real del proyecto, creando roles segregados (`lucas_app`, `lucas_agente`, `lucas_admin`), habilitando la extensión de vectores, configurando Row Level Security (RLS) por `customer_id` y cifrado `pgcrypto`.

### C. Cargador de Modelos Analíticos `.pkl` para FastAPI (`src/api/loader_pkl.py`)
- **Qué se hizo:** Se construyó una utilidad de carga asíncrona de artefactos de Machine Learning (`.pkl`) optimizada con `joblib` utilizando el evento `lifespan` de FastAPI.
- **Por qué:** Leer archivos `.pkl` del disco en cada solicitud de API destruye el rendimiento. Con `loader_pkl.py`, los modelos (`segmentacion`, `pronostico`, `glosa`, `pronostico_mensual`, `sentimiento`) se cargan en memoria RAM **una sola vez al iniciar el servidor**, garantizando inferencias con latencia ultrabaja (`< 8 segundos` en respuesta final del sistema).

### D. Registro de Auditoría de Ciberseguridad y QA (`data/audit-log.md`)
- **Qué se hizo:** Creación e implementación del log de auditorías continuas (Auditorías #01 a #04).
- **Por qué:** Para registrar de manera transparente las pruebas sobre cada PR y merge a `develop`, auditando enmascaramiento de datos, ausencia de datos reales, aislamiento por cliente y cumplimiento de los contratos REST (`docs/api.md`).

### E. Diagramas de Casos de Uso UML y Trazabilidad (`docs/casos-uso.md`)
- **Qué se hizo:** Modelado UML de los 12 casos de uso principales (`CU-01` a `CU-12`) en PlantUML (`docs/diagramas/casos-uso.puml` y SVG), definiendo actores (dependientes, independientes, sin historial, banco), flujos principales, alternativos y excepciones.
- **Por qué:** Proporcionar la matriz de trazabilidad entre Historias de Usuario (`HU`), Casos de Uso (`CU`) y Casos de Prueba del Sistema (`CP-SIS`), asegurando 100 % de cobertura según ISTQB.

---

## 3. Bitácora de Auditorías Técnicas (Rol DX)

| Auditoría | Objeto de Auditoría | Estándares Evaluados | Resultado |
|---|---|---|---|
| **Auditoría #01** | Contrato API (`docs/api.md`) y Mocks iniciales | Datos sintéticos, moneda PEN, Pydantic | ✅ APRUEBA |
| **Auditoría #02** | Diagrama ERD y Pipeline (`docs/arquitectura-datos.md`) | ISO 27001 (5.12), RLS, reproducible `--seed` | ✅ APRUEBA |
| **Auditoría #03** | Casos de Uso UML (`docs/casos-uso.md`) | ISTQB CTFL v4.0, Control de accesos (5.15) | ✅ APRUEBA |
| **Auditoría #04** | Base de Datos (`db/init.sql`) y Loader PKL (`src/api/loader_pkl.py`) | ISO 27001 (8.24 Criptografía, 8.26 App Security) | ✅ APRUEBA |

---

## 4. Estado del Trabajo y Sincronización en Git

- **Rama de Trabajo:** `smith` y `feature/datos-diagramas-v2`
- **Rama de Integración Principal:** `develop`
- **Archivos Entregados e Integrados en `develop`:**
  - `docs/arquitectura-datos.md`
  - `db/init.sql`
  - `src/api/loader_pkl.py`
  - `data/audit-log.md`
  - `.claude/equipo/smith/registro.md`

---
*Documento elaborado y firmado por Dixon Smith Zarzosa Toribio (Rol DX).*
