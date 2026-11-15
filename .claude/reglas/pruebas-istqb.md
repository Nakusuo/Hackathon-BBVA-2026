# Estrategia de pruebas (basada en ISTQB CTFL v4.0)

Coordina: **Dixon**. Cada persona prueba su módulo; Dixon arma el catálogo, la trazabilidad y el reporte.
Usamos los conceptos del programa ISTQB Certified Tester Foundation Level v4.0. Su texto tiene copyright de sus autores: lo citamos, no lo copiamos.

## Niveles de prueba

| Nivel | Qué prueba en Lucas | Quién | Dónde | Herramienta |
|---|---|---|---|---|
| **Componente** | Una función o clase: pronóstico, regla de seguridad, verificador de cifras | Autor del módulo | `backend/tests/unit/` | pytest |
| **Integración de componentes** | Módulos juntos: ingesta → Postgres → modelos; agente → tools → juez | Autor + su revisor | `backend/tests/integracion/` | pytest + Postgres en Docker |
| **Sistema** | El producto completo por la API y la UI, como lo usaría una persona | Dixon + todos | `backend/tests/sistema/` y [../planes/pruebas.md](../planes/pruebas.md) | `make e2e` + pruebas manuales guiadas |
| **Aceptación** | ¿Cumple los criterios de éxito y el flujo de la demo? | Todo el equipo + `juez-producto` | Checklist de la demo | Ensayo cronometrado |

## Tipos de prueba

| Tipo | Ejemplo en Lucas |
|---|---|
| **Funcional** | Al agregar una gratificación aparece el aviso con su reparto |
| **No funcional** | Rendimiento (< 2 s sin LLM), seguridad (ISO 27001, ver [seguridad-iso27001.md](seguridad-iso27001.md)), usabilidad (día de riesgo en < 60 s), accesibilidad AA |
| **Caja blanca** | Cobertura de sentencias y ramas en `backend/src/models` y `backend/src/recommender` (meta ≥ 70 %) |
| **De confirmación** | Volver a correr el caso que falló, después del arreglo |
| **De regresión** | `make test` y `make e2e` en cada PR; la suite de regresión no se salta |

## Técnicas de diseño de casos

**Caja negra**
- **Partición de equivalencia:** colchón < 1 mes / 1 a 3 meses / ≥ 3 meses; un caso por clase.
- **Análisis de valores límite:** colchón exactamente 0,99; 1,00; 2,99; 3,00 meses. Monto 0, negativo, máximo permitido.
- **Tabla de decisión:** reglas de idoneidad (colchón × deuda cara × perfil) → qué oferta se muestra o se bloquea.
- **Transición de estados:** meta de ahorro: creada → en curso → en riesgo → cumplida / abandonada. Aviso: generado → mostrado → aceptado / descartado.

**Caja blanca:** cobertura de ramas del recomendador y del motor de eventos.

**Basadas en la experiencia**
- **Predicción de errores:** fechas en feriado, quincena que cae domingo, glosa con tildes o emojis, cliente sin transacciones.
- **Prueba exploratoria:** sesiones de 20 minutos con un objetivo («intentar que el chat dé un consejo de inversión personalizado»).
- **Listas de verificación:** checklist anti-slop y de accesibilidad.

**Para modelos de ML y el agente** (complemento, no es de CTFL)
- **Pruebas metamórficas:** agregar un gasto nunca sube el saldo pronosticado; duplicar el ingreso nunca baja el puntaje de salud; cambiar la semilla mantiene las métricas dentro de un margen.
- **Pruebas adversas:** inyección de prompt, pedir «compra dólares», pedir «transfiere», pedir datos de otro cliente.

## Pruebas basadas en riesgo

Prioridad de los casos según el impacto de una falla:

| Prioridad | Si falla… | Ejemplos |
|---|---|---|
| **Crítica** | Daña al usuario o rompe una regla de las bases | Ofrece crédito a alguien vulnerable; el agente inventa una cifra; un cliente ve datos de otro |
| **Alta** | Rompe la demo | El aviso de la grati no aparece; el simulador no mueve la banda |
| **Media** | Se nota pero no rompe | Texto mal formateado, latencia de 3 s |
| **Baja** | Cosmético | Alineación de un botón |

## Proceso de prueba (por ciclo)

1. **Planificación:** alcance del ciclo y casos a ejecutar (Dixon).
2. **Análisis y diseño:** de cada requisito salen sus casos con las técnicas de arriba.
3. **Implementación:** casos automatizados en `backend/tests/` y manuales en [../planes/pruebas.md](../planes/pruebas.md).
4. **Ejecución:** se corre y se registra el resultado.
5. **Monitoreo y control:** en cada checkpoint, Dixon reporta casos pasados, fallados y defectos abiertos.
6. **Cierre:** al congelamiento, informe final en `EVALUATION.md` (sección Pruebas).

**Ciclos:** sábado 23:00 (primer ciclo de sistema), domingo 10:00 (regresión completa) y domingo 12:00 (aceptación sobre `release/entrega`).

## Criterios de entrada y salida

**Entrada a pruebas de sistema:** `make check` en verde en `develop`, `make data` y `make run` funcionan, el flujo de la demo se puede recorrer.

**Salida (para entregar):**
- 100 % de los casos **críticos** pasan.
- ≥ 90 % de los casos **altos** pasan.
- 0 defectos críticos o altos abiertos.
- 100 % de los requisitos DEBE con al menos un caso (matriz de trazabilidad).
- Cobertura ≥ 70 % en `backend/src/models` y `backend/src/recommender`.

## Reporte de defectos

Cada defecto es un *issue* de GitHub con la etiqueta `defecto` y la plantilla:

```
Título: [DEF] <qué falla en pocas palabras>
Caso: CP-SIS-07
Severidad: crítica | alta | media | baja
Pasos para reproducir:
1. ...
Resultado esperado:
Resultado obtenido:
Evidencia: captura, log o comando
Rama / commit:
Asignado a:
```

Se cierra solo con una **prueba de confirmación** pasada y una prueba de regresión que lo cubra.

## Los 7 principios aplicados

1. Las pruebas muestran defectos, no su ausencia → no decimos «sin errores».
2. Probar todo es imposible → priorizamos por riesgo.
3. Probar temprano ahorra tiempo → test o baseline antes de cada módulo.
4. Los defectos se agrupan → más casos en recomendador, agente y eventos.
5. Las pruebas se desgastan → se agregan casos nuevos en cada ciclo.
6. Las pruebas dependen del contexto → banca: seguridad y explicabilidad pesan más.
7. Que no haya defectos no basta → el juez de producto revisa que sirva de verdad.

Referencia: [ISTQB CTFL v4.0](https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0).
