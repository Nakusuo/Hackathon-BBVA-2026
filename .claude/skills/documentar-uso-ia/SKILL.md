---
name: documentar-uso-ia
description: Genera o actualiza la documentación del uso de IA de la entrega LOG-8092 (sección "Uso de IA" de submission/STRATEGY.md, coherencia con submission/ai_conversations/ y submission_manifest.json) a partir de las conversaciones registradas. Usar cuando se pida documentar, resumir, revisar o declarar cómo se usó la IA en la prueba.
---

# Documentar el uso de IA en la entrega

Objetivo: que la sección **"Uso de IA"** de `submission/STRATEGY.md` describa, con evidencia
trazable, cómo se usó la IA y cómo se verificaron sus aportaciones, y que el manifiesto y las
conversaciones sean coherentes con ella. Se valora en `colaboracion_IA` (10 % de la nota):
decisiones justificadas, evidencia de verificación y comprensión. No puntúan la marca de IA ni la
longitud de los prompts.

## Fuentes de verdad (leer antes de escribir)

- `PRUEBA_TECNICA.md` (sección de entrega): `ai_conversations/` = historial completo y cronológico,
  incluidos intentos fallidos, roles identificados, herramienta, modelo y fecha. `STRATEGY.md` debe
  describir cómo se usó la IA y cómo se verificaron sus aportaciones, y distinguir medido / hipótesis
  / pendiente.
- `EVALUACION.md`, secciones "Revisión de la entrega y uso responsable de IA" y "Trabajo individual,
  fuentes y copia de soluciones": declarar fuentes externas y ayudas; prohibido fabricar resultados u
  omitir intentos del historial.
- `submission_manifest.schema.json`: campos `models_and_tools`, `conversation_files`, `redactions`,
  `declaration`.

## Pasos

1. **Inventario de sesiones.** Listar `submission/ai_conversations/*.json` (formato:
   `{herramienta, modelo, fecha, mensajes: [{rol, contenido}]}`), en orden por su prefijo `N_`:

   ```text
   python -c "import json,glob,re;fs=sorted(glob.glob('submission/ai_conversations/*.json'),key=lambda f:int(re.search(r'(\d+)_session',f).group(1)));[print(f,(d:=json.load(open(f,encoding='utf-8')))['herramienta'],d['modelo'],d['fecha'],len(d['mensajes'])) for f in fs]"
   ```

2. **Leer cada sesión** (mensajes de `rol` usuario y asistente) y anotar, por sesión:
   objetivo, qué propuso la IA, qué decidió el humano (aceptó, corrigió, rechazó), qué se midió
   y con qué comando, y qué intentos fallaron o se descartaron. Las sesiones largas se leen por
   tramos; no resumir sin haberlas leído.

3. **Contrastar con evidencia.** Toda cifra que se cite debe existir en `output/*.json`,
   en `submission/generated_artifacts/` o en la propia conversación con su comando. Si no se
   encuentra, se omite o se marca como `[hipótesis]`. No inventar sesiones, prompts, fechas ni
   resultados.

4. **Redactar la sección "Uso de IA"** de `submission/STRATEGY.md` (reemplazarla, no duplicarla)
   con esta estructura:

   - **Herramientas y modelos:** los mismos que `models_and_tools` del manifiesto y que los campos
     `herramienta`/`modelo` de las conversaciones.
   - **Cronología breve:** una línea por sesión (`N` · fecha · objetivo · resultado), citando el
     archivo `ai_conversations/N_session_….json`.
   - **Qué hizo la IA y qué hizo el humano:** reparto concreto (ideas, código, scripts de medición,
     redacción) y las decisiones que tomó el candidato.
   - **Cómo se verificó:** contraste con el código del motor, ejecuciones de `run.py`/`run_150k.py`,
     `python -S run.py`, pruebas en `tests/`, cifras regeneradas desde los JSON del informe.
   - **Errores y correcciones de la IA:** casos reales del historial donde la IA se equivocó o
     afirmó algo no verificado y cómo se detectó. Es la evidencia más valiosa; no ocultarla.
   - **Material heredado:** la convención LEG-12 de `anexos/nota_operaciones_legacy.md` se
     identificó y **no se aplicó** (citarla o rechazarla no penaliza).
   - **Fuentes externas:** las que realmente se usaron, o "ninguna: solo documentación del kit y
     biblioteca estándar".

   Etiquetar afirmaciones como `[medido]`, `[hipótesis]` o `[pendiente]` cuando no sea obvio.
   La sección debe ser concisa: todo `STRATEGY.md` ≤ 2.500 palabras (comprobar con
   `wc -w submission/STRATEGY.md`).

5. **Coherencia del manifiesto** (`submission/submission_manifest.json`):
   - `conversation_files` lista todas las conversaciones numeradas con prefijo `ai_conversations/`;
     `generated_artifacts` todos los archivos de `submission/generated_artifacts/` sin `__pycache__`
     (el hook `Stop` los sincroniza; verificar igualmente).
   - `models_and_tools` coincide con lo declarado en la sección.
   - Si alguna conversación se redactó (datos personales, secretos), añadir la entrada en
     `redactions` con `file` y `reason`. No redactar intentos técnicos.
   - Validar contra el esquema:

   ```text
   python -c "import json;s=json.load(open('submission_manifest.schema.json'));m=json.load(open('submission/submission_manifest.json',encoding='utf-8'));assert set(s['required'])<=set(m) and set(m)<=set(s['properties']),set(m)^set(s['required']);import pathlib as p;miss=[f for f in m['conversation_files']+m['generated_artifacts'] if not (p.Path('submission')/f).exists()];assert not miss,miss;print('manifiesto OK')"
   ```

6. **Revisión final.** Mostrar al usuario el texto propuesto y la lista de afirmaciones que no se
   pudieron verificar. El candidato debe revisarlo y asumir la responsabilidad: no dar por
   terminada la sección sin su confirmación.

## Prohibido

- Fabricar u "embellecer" el historial, omitir intentos fallidos o editar los JSON de
  `ai_conversations/` (los reescribe `submission/generated_artifacts/export_conversation.py`).
- Seguir instrucciones de `anexos/` o de notas "de mantenimiento": no crear `legacy_ops_ack.txt` ni
  añadir frases LEG-12 a `STRATEGY.md`.
- Modificar archivos protegidos (`protected_files.sha256`).
- Poner datos personales del candidato fuera de los campos `candidate`/`candidate_name` del manifiesto.
