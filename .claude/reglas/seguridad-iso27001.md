# Seguridad alineada con ISO/IEC 27001:2022

Responsable: **Michael**. Revisa: `juez-cumplimiento`.

## Qué decimos y qué no

- Lucas está **alineado con controles seleccionados del Anexo A de ISO/IEC 27001:2022**. **No** está certificado. Una certificación exige un SGSI (sistema de gestión) auditado; en 2 días no corresponde decir otra cosa.
- El texto de la norma tiene copyright de ISO: **no entra al RAG** ni se copia. Solo citamos el número y el título de cada control.
- El Anexo A tiene 93 controles en 4 temas (organizacionales, de personas, físicos y tecnológicos). El detalle de cada uno está en ISO/IEC 27002:2022.

## Declaración de aplicabilidad (versión hackathon)

Controles que aplicamos, cómo y dónde está la evidencia. Lo que no aplica se dice y se explica.

| Control | Título | Cómo lo cumple Lucas | Evidencia | Tarea |
|---|---|---|---|---|
| 5.9 | Inventario de información y activos | Lista de datos, modelos, servicios y secretos | `ARCHITECTURE.md`, sección Activos | MI-10 |
| 5.12 | Clasificación de la información | Tres niveles: sensible (`seguro`), interna (`app`), pública (RAG) | `data/dictionary.md` con columna de clasificación | DX-01 |
| 5.15 | Control de acceso | Un rol de Postgres por componente; mínimo privilegio | `db/init.sql` | MI-03 |
| 5.34 | Privacidad y protección de datos personales | Datos 100 % sintéticos, consentimiento, borrar memoria; alineado con Ley 29733 | Pantalla de consentimiento, endpoint «olvidar» | MC-01, JF-09 |
| 8.2 | Derechos de acceso privilegiado | `lucas_admin` solo para migraciones; la app y el agente nunca lo usan | `db/init.sql`, `.env.example` | MI-03 |
| 8.3 | Restricción de acceso a la información | RLS por `customer_id`; el agente no ve columnas sensibles | Test «cliente no ve datos de otro» | MI-03 |
| 8.4 | Acceso al código fuente | Repo privado del equipo; ramas protegidas `main` y `develop` | Configuración de GitHub | MI-10 |
| 8.8 | Gestión de vulnerabilidades técnicas | `pip-audit` sobre dependencias con versión fija | Salida en `make check` | MI-11 |
| 8.9 | Gestión de la configuración | Todo por código: `docker-compose.yml`, `Makefile`, `requirements.txt` | Repo | MI-01, MI-02 |
| 8.10 | Eliminación de información | «Olvidar lo que sabes de mí» borra memoria y respuestas | Test de borrado | JF-09 |
| 8.11 | Enmascaramiento de datos | Logs y respuestas del agente sin montos de deuda exactos ni IDs completos | Test de logs | MI-11 |
| 8.12 | Prevención de fuga de datos | Ningún dato de usuario va a un LLM externo; Ollama local por defecto | `PROMPTS.md`, test del proveedor | JF-01 |
| 8.13 | Copias de respaldo | Los datos se regeneran con `make data` (semilla fija); el RAG desde `docs/rag/` | README | DX-02 |
| 8.15 | Registro de eventos (logging) | Log de accesos a la API y de cada llamada a tools del agente, sin datos sensibles | `src/api` middleware | MI-05 |
| 8.16 | Monitoreo | Latencia y errores por endpoint en el panel Evidencia | Panel | MI-05, MC-07 |
| 8.24 | Uso de criptografía | Columnas sensibles cifradas con pgcrypto; clave solo en `.env` | `db/init.sql` | MI-03 |
| 8.25 | Ciclo de vida de desarrollo seguro | Gitflow, revisión cruzada, jueces antes del merge | `reglas/gitflow.md`, `planes/verificaciones.md` | Todos |
| 8.26 | Requisitos de seguridad de la aplicación | Validación Pydantic, tools de solo lectura, sin operaciones con dinero | `src/api`, `src/agent` | MG-03, JF-03 |
| 8.28 | Codificación segura | `ruff`, sin secretos en el código, consultas parametrizadas, sin `eval` | `make check`, `juez-tecnico` | Todos |
| 8.29 | Pruebas de seguridad en desarrollo y aceptación | Casos adversos (inyección de prompt, SQL, acceso indebido) en el ciclo de pruebas | `tests/seguridad/`, [pruebas-istqb.md](pruebas-istqb.md) | MI-11, JF-06 |
| 8.31 | Separación de entornos | `.env` de desarrollo distinto del de demo; la base de demo se crea desde cero | README | MI-07 |
| 8.32 | Gestión de cambios | Todo cambio entra por PR a `develop` con revisión | GitHub | Todos |
| 8.33 | Información de prueba | Solo datos sintéticos; nunca datos reales en pruebas | `data/QUALITY.md` | DX-02 |

**No aplican en el hackathon** (se dice en `ARCHITECTURE.md`): controles físicos (tema 7), gestión de proveedores y nube (5.19 a 5.23), continuidad del negocio (5.29, 5.30), gestión de personal (tema 6). Con datos reales serían obligatorios.

## Para la demo y el pitch

- Michael muestra en 30 segundos: el agente intenta leer `seguro.clientes.deuda_total` y Postgres lo bloquea (controles 8.3 y 5.15).
- Frase para el pitch: «Diseñamos Lucas alineado con 23 controles de ISO/IEC 27001:2022. No estamos certificados; con datos reales, el siguiente paso es el SGSI completo».
