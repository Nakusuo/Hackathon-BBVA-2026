-- =============================================================================
-- db/init.sql  ·  Lucas (AI Financial Life)  ·  PostgreSQL 16 + pgvector
-- Implementa ARCHITECTURE.md §5: esquemas seguro / app / rag, roles, RLS, pgcrypto.
-- Se ejecuta UNA vez como superusuario (docker-entrypoint-initdb.d). Idempotente
-- en roles/extensiones; las tablas se crean nuevas (usa un volumen limpio para rehacer).
--
-- CONTRASEÑAS: los valores 'CAMBIAR_...' son marcadores. Cámbialos con
--   ALTER ROLE lucas_app PASSWORD '<valor de .env>';   (no las subas al repo)
-- =============================================================================

-- 1. EXTENSIONES (requieren superusuario) -------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. ROLES (un rol por componente) --------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lucas_admin') THEN
    CREATE ROLE lucas_admin  LOGIN PASSWORD 'CAMBIAR_ADMIN'  NOSUPERUSER CREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lucas_batch') THEN
    -- make train / make eval: ve a todos los clientes
    CREATE ROLE lucas_batch  LOGIN PASSWORD 'CAMBIAR_BATCH'  NOSUPERUSER BYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lucas_app') THEN
    CREATE ROLE lucas_app    LOGIN PASSWORD 'CAMBIAR_APP'    NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lucas_agente') THEN
    CREATE ROLE lucas_agente LOGIN PASSWORD 'CAMBIAR_AGENTE' NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;

-- 3. ESQUEMAS ------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS seguro AUTHORIZATION lucas_admin;  -- sensible
CREATE SCHEMA IF NOT EXISTS app    AUTHORIZATION lucas_admin;  -- interno (RLS)
CREATE SCHEMA IF NOT EXISTS rag    AUTHORIZATION lucas_admin;  -- público (pgvector)

REVOKE ALL ON SCHEMA seguro, app, rag FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- A partir de aquí, todo lo que se crea queda a nombre de lucas_admin
SET ROLE lucas_admin;

-- =============================================================================
-- 4. ESQUEMA seguro  (SENSIBLE: ni lucas_app ni lucas_agente tienen permiso)
-- =============================================================================
-- Columnas sensibles cifradas con pgp_sym_encrypt (clave = CLAVE_DATOS, solo admin y batch).
CREATE TABLE seguro.clientes (
  customer_id         text PRIMARY KEY,
  ingreso_mensual_enc bytea,   -- supuesto: hace falta para derivar app.perfil.cuota_ingreso
  deuda_total_enc     bytea,
  tcea_promedio_enc   bytea,
  cuota_mensual_enc   bytea,
  etiquetas_enc       bytea,   -- etiquetas de referencia (p. ej. arquetipo) para evaluar
  creado_en           timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE seguro.clientes IS 'Sensible. Solo lucas_admin y lucas_batch. Valores cifrados con pgcrypto.';

CREATE FUNCTION seguro.cifrar(valor text, clave text) RETURNS bytea
  LANGUAGE sql IMMUTABLE AS $$ SELECT pgp_sym_encrypt(valor, clave) $$;
CREATE FUNCTION seguro.descifrar(valor bytea, clave text) RETURNS text
  LANGUAGE sql IMMUTABLE AS $$ SELECT pgp_sym_decrypt(valor, clave) $$;

-- =============================================================================
-- 5. ESQUEMA app  (INTERNO, RLS por customer_id)
-- =============================================================================

-- app.perfil: frontera de privacidad. Solo valores DERIVADOS, nunca montos de deuda.
CREATE TABLE app.perfil (
  customer_id        text PRIMARY KEY,
  tipo_trabajo       text NOT NULL,                       -- dependiente / independiente / comisionista ...
  frecuencia_ingreso text NOT NULL,                       -- quincenal / mensual / irregular ...
  colchon_meses      numeric(6,2) NOT NULL DEFAULT 0 CHECK (colchon_meses >= 0),
  cuota_ingreso      numeric(6,4) CHECK (cuota_ingreso >= 0),   -- cuota mensual / ingreso
  nivel_deuda        text NOT NULL CHECK (nivel_deuda IN ('bajo','medio','alto')),
  deuda_cara         boolean NOT NULL DEFAULT false,
  deuda_cara_tramo   text NOT NULL DEFAULT 'ninguno'
                       CHECK (deuda_cara_tramo IN ('ninguno','bajo','medio','alto')),
  personas_a_cargo   smallint NOT NULL DEFAULT 0 CHECK (personas_a_cargo >= 0),
  region             text NOT NULL,
  paga_en_usd        boolean NOT NULL DEFAULT false
);

-- app.transacciones: historia. La regenera `make data`.
-- monto SIEMPRE positivo; el signo lo da `tipo`. Si tu generador emite montos con signo, la ingesta usa abs().
CREATE TABLE app.transacciones (
  transaction_id text PRIMARY KEY,
  customer_id    text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  fecha_hora     timestamptz NOT NULL,                    -- se interpreta en America/Lima
  monto          numeric(12,2) NOT NULL CHECK (monto > 0),
  moneda         char(3) NOT NULL DEFAULT 'PEN' CHECK (moneda IN ('PEN','USD')),
  tipo           text NOT NULL CHECK (tipo IN ('ingreso','gasto')),
  categoria      text,                                    -- puede ser NULL (dato faltante); engine.categorizar la completa
  comercio       text,                                    -- comercio ficticio, puede ser NULL
  metodo         text,                                    -- yape, plin, tarjeta, efectivo, transferencia, debito_automatico
  saldo          numeric(12,2)                            -- opcional
);
CREATE INDEX idx_tx_cliente_fecha ON app.transacciones (customer_id, fecha_hora);

-- app.movimientos_usuario: gastos/ingresos agregados en vivo (sobreviven a `make data`; eval/ los excluye).
-- Los de fecha entre hoy y hoy+30 son PLANIFICADOS (flujo conocido), no historia.
CREATE TABLE app.movimientos_usuario (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  fecha       date NOT NULL,                              -- validación de la API: hasta hoy + 30
  monto       numeric(12,2) NOT NULL CHECK (monto > 0),
  tipo        text NOT NULL CHECK (tipo IN ('ingreso','gasto')),
  categoria   text,
  comercio    text,
  creado_en   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_mov_cliente_fecha ON app.movimientos_usuario (customer_id, fecha);

-- app.segmentos: la escribe `make train` (lucas_batch).
CREATE TABLE app.segmentos (
  customer_id        text PRIMARY KEY REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  cluster            integer NOT NULL,
  cuadrante          text NOT NULL
                       CHECK (cuadrante IN ('ahorrador firme','se le escapa','ingreso justo','gastador')),
  descripcion        text,
  version_artefacto  text,
  calculado_en       timestamptz NOT NULL DEFAULT now()
);

-- app.metas: metas de ahorro (plan_meta).
CREATE TABLE app.metas (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id     text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  nombre          text NOT NULL,
  monto_objetivo  numeric(12,2) NOT NULL CHECK (monto_objetivo > 0),
  fecha_objetivo  date,
  creado_en       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_metas_cliente ON app.metas (customer_id);

-- app.memoria: la escribe el agente. SIN texto libre del usuario: solo claves/valores de listas
-- cerradas (Literal en src/tipos.py). Así una inyección de prompt no queda persistida.
CREATE TABLE app.memoria (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id  text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  tipo         text NOT NULL CHECK (tipo IN ('preferencia','resumen')),
  clave        text NOT NULL,         -- preferencia: p. ej. 'excluir_tipo_reco' · resumen: 'tema'
  valor        text NOT NULL,         -- valor de lista cerrada
  fecha        date NOT NULL DEFAULT current_date,
  UNIQUE (customer_id, tipo, clave, valor)
);
CREATE INDEX idx_memoria_cliente ON app.memoria (customer_id, tipo);

-- app.respuestas_reco: «útil / no me sirve», la escribe la API.
CREATE TABLE app.respuestas_reco (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id  text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  reco_id      text NOT NULL,
  tipo_reco    text NOT NULL,
  respuesta    text NOT NULL CHECK (respuesta IN ('util','no_me_sirve')),
  creado_en    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_respuestas_cliente ON app.respuestas_reco (customer_id, creado_en);

-- app.avisos: solo la API los persiste. id determinista (tipo + fecha_evento) => es único POR CLIENTE,
-- por eso la PK es (customer_id, id) y el upsert es ON CONFLICT (customer_id, id).
CREATE TABLE app.avisos (
  customer_id    text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  id             text NOT NULL,
  tipo           text NOT NULL,
  urgencia       text NOT NULL CHECK (urgencia IN ('normal','urgente')),
  fecha_evento   date NOT NULL,
  mensaje        text NOT NULL,
  prob           numeric(5,4) CHECK (prob BETWEEN 0 AND 1),
  impacto_soles  numeric(12,2),
  creado_en      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (customer_id, id)
);
CREATE INDEX idx_avisos_cliente_creado ON app.avisos (customer_id, creado_en);

-- app.mensajes: historial del chat (lo escribe la API).
CREATE TABLE app.mensajes (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id  text NOT NULL REFERENCES app.perfil(customer_id) ON DELETE CASCADE,
  rol          text NOT NULL CHECK (rol IN ('usuario','asistente')),
  contenido    text NOT NULL,
  creado_en    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_mensajes_cliente ON app.mensajes (customer_id, creado_en);

-- =============================================================================
-- 6. ESQUEMA rag  (PÚBLICO, pgvector, sin RLS)
-- =============================================================================
CREATE TABLE rag.fuentes (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  modulo    text NOT NULL,
  titulo    text NOT NULL,
  url       text,
  licencia  text,
  fecha     date
);

-- DIMENSIÓN DEL EMBEDDING: 768 es un supuesto (p. ej. nomic-embed-text en Ollama).
-- Debe coincidir con OLLAMA_EMBED_MODEL (decisión de Jeffrey, JF-01) ANTES de cargar datos.
CREATE TABLE rag.fragmentos (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  fuente_id  bigint NOT NULL REFERENCES rag.fuentes(id) ON DELETE CASCADE,
  modulo     text NOT NULL,
  texto      text NOT NULL,
  embedding  vector(768)
);
CREATE INDEX idx_fragmentos_modulo ON rag.fragmentos (modulo);
CREATE INDEX idx_fragmentos_embedding ON rag.fragmentos USING hnsw (embedding vector_cosine_ops);

-- =============================================================================
-- 7. RLS por customer_id (falla cerrada: sin SET LOCAL app.customer_id no hay filas)
--    Se activa con:  SET LOCAL app.customer_id = '<id>'   (src/db/conexion.py: como_cliente)
--    lucas_admin (dueño) y lucas_batch (BYPASSRLS) no quedan sujetos a estas políticas.
-- =============================================================================
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['perfil','transacciones','movimientos_usuario','segmentos',
                           'metas','memoria','respuestas_reco','avisos','mensajes']
  LOOP
    EXECUTE format('ALTER TABLE app.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY por_cliente ON app.%I
         FOR ALL TO lucas_app, lucas_agente
         USING      (customer_id = nullif(current_setting(''app.customer_id'', true), ''''))
         WITH CHECK (customer_id = nullif(current_setting(''app.customer_id'', true), ''''))', t);
  END LOOP;
END $$;

-- =============================================================================
-- 8. PERMISOS (mínimo privilegio)
-- =============================================================================
-- lucas_batch: SELECT en app y seguro; escribe app.segmentos
GRANT USAGE ON SCHEMA app, seguro TO lucas_batch;
GRANT SELECT ON ALL TABLES IN SCHEMA app, seguro TO lucas_batch;
GRANT INSERT, UPDATE, DELETE ON app.segmentos TO lucas_batch;
GRANT EXECUTE ON FUNCTION seguro.cifrar(text, text), seguro.descifrar(bytea, text) TO lucas_batch;

-- lucas_app: SELECT en app y rag; escribe movimientos_usuario, metas, respuestas_reco, avisos
--            (+ mensajes: supuesto, el chat pasa por la API). NADA en seguro.
GRANT USAGE ON SCHEMA app, rag TO lucas_app;
GRANT SELECT ON ALL TABLES IN SCHEMA app, rag TO lucas_app;
GRANT INSERT, UPDATE, DELETE ON app.movimientos_usuario, app.metas TO lucas_app;
GRANT INSERT ON app.respuestas_reco, app.mensajes TO lucas_app;
GRANT INSERT, UPDATE ON app.avisos TO lucas_app;

-- lucas_agente: SELECT en app y rag; escribe y borra SOLO app.memoria. NADA en seguro.
GRANT USAGE ON SCHEMA app, rag TO lucas_agente;
GRANT SELECT ON ALL TABLES IN SCHEMA app, rag TO lucas_agente;
GRANT INSERT, UPDATE, DELETE ON app.memoria TO lucas_agente;

-- Tablas futuras en app/rag: lectura para los tres roles (sin escritura)
ALTER DEFAULT PRIVILEGES FOR ROLE lucas_admin IN SCHEMA app
  GRANT SELECT ON TABLES TO lucas_batch, lucas_app, lucas_agente;
ALTER DEFAULT PRIVILEGES FOR ROLE lucas_admin IN SCHEMA rag
  GRANT SELECT ON TABLES TO lucas_app, lucas_agente;

RESET ROLE;
