# Arquitectura de Datos y Flujos (Lucas)

Este documento describe la arquitectura de datos del copiloto **Lucas**, incluyendo el diagrama entidad-relación (ERD) para los esquemas `seguro`, `app` y `rag`, y el diagrama de flujo del pipeline de generación de datos sintéticos.

---

## 1. Diagrama Entidad-Relación (ERD)

A continuación se muestra el esquema relacional en PostgreSQL, estructurado en los esquemas `seguro` (datos protegidos de clientes), `app` (datos derivados y de uso, con Row Level Security por `customer_id`) y `rag` (fuentes públicas del RAG). Sigue la sección 5 de [ARCHITECTURE.md](../ARCHITECTURE.md); si cambian, manda ARCHITECTURE.md.

```mermaid
erDiagram
    seguro_clientes {
        VARCHAR customer_id PK
        VARCHAR rango_edad
        VARCHAR region
        VARCHAR tipo_trabajo
        VARCHAR frecuencia_ingreso
        INT personas_a_cargo
        BYTEA deuda_total "cifrado con pgcrypto"
        INT n_creditos
        BYTEA cuota_mensual "cifrado con pgcrypto"
        BYTEA tcea_promedio "cifrado con pgcrypto"
        DECIMAL colchon_meses
        INT antiguedad_cliente_meses
        DECIMAL meta_ahorro
        BOOLEAN paga_en_usd
        VARCHAR arquetipo
        VARCHAR necesidad_oculta "etiqueta, solo eval"
        VARCHAR perfil_ahorro_real "etiqueta, solo eval"
        VARCHAR perfil_gasto_real "etiqueta, solo eval"
        DECIMAL prob_acepta_reco "etiqueta, solo eval"
    }

    app_perfil {
        VARCHAR customer_id PK
        VARCHAR tipo_trabajo
        VARCHAR frecuencia_ingreso
        DECIMAL colchon_meses
        DECIMAL cuota_ingreso
        VARCHAR nivel_deuda "bajo, medio o alto"
        BOOLEAN deuda_cara
        VARCHAR deuda_cara_tramo "rango, nunca el monto"
        INT personas_a_cargo
        VARCHAR region
        BOOLEAN paga_en_usd
    }

    app_transacciones {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        DATE fecha
        DECIMAL monto
        VARCHAR categoria
        VARCHAR tipo_gasto
        VARCHAR glosa
        VARCHAR comercio
        VARCHAR canal
        BOOLEAN es_recurrente
        BOOLEAN es_atipico
    }

    app_movimientos_usuario {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        DATE fecha "pasada o planificada a 30 dias"
        DECIMAL monto
        VARCHAR categoria
        VARCHAR descripcion
    }

    app_segmentos {
        VARCHAR customer_id PK
        INT cluster
        VARCHAR cuadrante
        VARCHAR descripcion
    }

    app_metas {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        VARCHAR titulo
        DECIMAL monto_objetivo
        DECIMAL monto_actual
        DATE fecha_limite
        BOOLEAN activo
    }

    app_memoria {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        VARCHAR tipo "preferencia o resumen, lista cerrada"
        VARCHAR clave
        VARCHAR valor
        TIMESTAMP actualizado_en
    }

    app_respuestas_reco {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        VARCHAR recomendacion_id
        BOOLEAN util
        TIMESTAMP respondido_en
    }

    app_avisos {
        VARCHAR id PK
        VARCHAR customer_id FK
        VARCHAR tipo
        VARCHAR urgencia
        DATE fecha_evento
        TEXT mensaje
    }

    app_mensajes {
        BIGSERIAL id PK
        VARCHAR customer_id FK
        TEXT texto
        VARCHAR sentimiento
    }

    rag_fuentes {
        VARCHAR id PK
        VARCHAR titulo
        VARCHAR enlace
        VARCHAR licencia
    }

    rag_fragmentos {
        BIGSERIAL id PK
        VARCHAR fuente_id FK
        VARCHAR modulo
        TEXT texto
        VECTOR embedding
    }

    seguro_clientes ||--|| app_perfil : "la ingesta deriva"
    app_perfil ||--o{ app_transacciones : "tiene"
    app_perfil ||--o{ app_movimientos_usuario : "agrega en vivo"
    app_perfil ||--o| app_segmentos : "pertenece a"
    app_perfil ||--o{ app_metas : "define"
    app_perfil ||--o{ app_memoria : "registra"
    app_perfil ||--o{ app_respuestas_reco : "valora"
    app_perfil ||--o{ app_avisos : "recibe"
    app_perfil ||--o{ app_mensajes : "escribe"
    rag_fuentes ||--o{ rag_fragmentos : "se divide en"
```

`app.perfil` es la frontera de privacidad (ARCHITECTURE.md, sección 5.1): la ingesta es la única que lee `seguro.clientes` y escribe en `app.perfil` solo valores derivados. Las tablas de `app` cuelgan de `app.perfil`, nunca de `seguro.clientes`. `app.memoria` guarda pares `clave`/`valor` de listas cerradas, nunca texto libre del usuario. El `customer_id` es un código sintético (`C00001`), no un UUID.

---

## 2. Flujo del Pipeline de Datos Sintéticos e Ingesta

El siguiente diagrama muestra el flujo desde la generación de datos estratificados con semilla fija hasta la carga validada en PostgreSQL con Pydantic y reglas de seguridad ISO 27001.

```mermaid
graph TD
    A["Inicio: python data/generator.py --semilla 2026"] --> B["Arquetipos y distribuciones calibradas"]
    B --> C["Bootstrap estratificado (500 clientes x 12 meses)"]
    C --> D["Calendario peruano y escenarios difíciles"]
    D --> E["Movimientos, glosas y mensajes con sentimiento"]
    E --> F["Parquet en data/generado/ con _manifiesto.json (hashes)"]
    F --> G["Ingesta: validación Pydantic y deduplicación"]
    G --> H["Carga a PostgreSQL: seguro.clientes cifrado y app.perfil derivado"]
    H --> I["RLS por customer_id y roles lucas_app, lucas_agente, lucas_batch"]
    I --> J["Fin: make data completo y verificado"]
```

Los pasos A a F existen hoy (`src/generador/`). La ingesta y la carga a PostgreSQL (G a I) están planificadas en MG-02 y MI-03 y todavía no tienen código. `data/generado/` está en `.gitignore`: los datos se regeneran con la semilla y no se suben al repo.

---

## 3. Clasificación de Información (ISO/IEC 27001 - 5.12)

| Nivel | Esquema / Tabla | Descripción |
|---|---|---|
| **Sensible** | `seguro.clientes` | Datos demográficos y de deuda; montos cifrados con pgcrypto. Ni `lucas_app` ni `lucas_agente` tienen permiso: solo la ingesta (`lucas_admin`) y `eval/` (`lucas_batch`). |
| **Interna** | `app.perfil`, `app.transacciones`, `app.movimientos_usuario`, `app.segmentos`, `app.metas`, `app.memoria`, `app.respuestas_reco`, `app.avisos`, `app.mensajes` | Datos derivados y de uso, con RLS por `customer_id`. `app.perfil` no guarda montos de deuda. |
| **Pública** | `rag.fuentes`, `rag.fragmentos` y `docs/rag/` | PDFs educativos y metadatos con licencia verificada. |
