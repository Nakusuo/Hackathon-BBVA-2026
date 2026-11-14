# Diseño: casos de uso de Lucas

Fecha: 2026-11-14 · Rama: `feature/arq-casos-uso` · Autor: Michael (arquitectura)

## Intención

Convertir las 25 historias de [historias.md](../../../.claude/planes/historias.md) en un modelo de casos de uso formal, estilo UML. Sirve para dos cosas:

1. **Entregable** para el jurado: muestra que el alcance está modelado con método, no improvisado.
2. **Referencia del equipo**: backend, front, IA y tester ven el mismo flujo, con sus alternos y excepciones, antes de programar.

## Objetivos, no objetivos y antiobjetivos

- **Objetivos:** diagrama UML de casos de uso, 11 casos de objetivo de usuario más 1 incluido, ficha completa por caso y matriz HU → CU → CP-SIS sin huecos.
- **No objetivos:** diagramas de secuencia, de clases o de actividad; rediseñar historias; definir rutas de API nuevas.
- **Antiobjetivos:** casos que contradigan las historias o las reglas de [negocio.md](../../../.claude/reglas/negocio.md); cifras inventadas; flujos donde Lucas mueva dinero o asesore («compra dólares»); marca o colores de BBVA en el diagrama.

## Restricciones

- Si un caso y una historia chocan, manda la historia (y sobre ella, el plan maestro).
- Español, sin AI-slop ([calidad-codigo.md](../../../.claude/reglas/calidad-codigo.md)).
- El diagrama se genera offline, sin servidores externos.
- Las rutas citadas siguen [ARCHITECTURE.md](../../../ARCHITECTURE.md) §5–6 (`POST /sesion`, `/yo/...`, el cliente sale del token). `docs/api.md` propone `/customers/{customer_id}/...`, que choca con HU-12; no se cita como fuente.

## Enfoques considerados

| Enfoque | A favor | En contra | Elegido |
|---|---|---|---|
| Un caso por historia (25) | Trazabilidad 1:1 trivial | No es UML correcto: varias historias son el mismo objetivo; diagrama ilegible | No |
| **Agrupado por objetivo (11 + 1 «include»)** | UML correcto, diagrama legible, matriz conserva la trazabilidad | Requiere matriz HU→CU | **Sí** |

| Forma del entregable | A favor | En contra | Elegido |
|---|---|---|---|
| **Un solo documento** | Se revisa, imprime o pasa a PDF de una vez | Largo (600–800 líneas) | **Sí** |
| Un archivo por caso | Diffs separados por dueño | 13 archivos; armar el entregable cuesta | No |

## Lo decidido

### Archivos

```
docs/casos-uso.md               índice, actores, diagrama, 12 fichas, matriz
docs/diagramas/casos-uso.puml   fuente PlantUML
docs/diagramas/casos-uso.svg    exportado, se ve en GitHub sin herramientas
```

El SVG se genera con `plantuml.jar` en una carpeta temporal (Java 17 local, layout `smetana`, sin Graphviz). El jar no se sube ni se vuelve dependencia. El comando para regenerarlo va en un comentario al inicio del `.puml`.

### Actores

| Actor | Tipo | Notas |
|---|---|---|
| Cliente | Principal, abstracto | Independiente, Formal y Comisionista/mixto heredan de él (generalización) |
| Persona sin historial | Principal | No tiene sesión ni toca la base |
| Banco que integra a Lucas | Principal | Lo representa el jurado |
| Motor LLM | Secundario | Ollama por defecto; Gemini apagado; plantillas como respaldo |
| BCRP | Secundario | Tipo de cambio; serie grabada sin red |

Postgres no es actor: es parte de Lucas.

### Casos de uso

| CU | Nombre | Actor principal | Historias | Ruta |
|---|---|---|---|---|
| CU-01 | Consultar mi estado financiero | Cliente | HU-01, 02, 15 | `GET /yo/estado` |
| CU-02 | Consultar pronóstico a 30 días | Cliente | HU-03 | `GET /yo/estado` |
| CU-03 | Recibir avisos anticipados | Cliente | HU-04, 05, 24 | `GET /yo/estado` |
| CU-04 | Obtener recomendaciones | Cliente | HU-06, 07, 13, 17 | `GET /yo/estado` |
| CU-05 | Simular un cambio | Cliente | HU-08 | `POST /yo/simular` |
| CU-06 | Registrar un movimiento | Cliente | HU-09 | `POST /yo/movimientos` |
| CU-07 | Conversar con Lucas | Cliente (+ Motor LLM) | HU-10, 11, 19 | `POST /yo/chat` |
| CU-08 | Gestionar meta de ahorro | Cliente | HU-16 | por definir en ARCHITECTURE.md |
| CU-09 | Controlar mis datos | Cliente | HU-18, 23 | por definir |
| CU-10 | Probar Lucas sin ser cliente | Persona sin historial | HU-21 | por definir (sin token) |
| CU-11 | Evaluar impacto y evidencia | Banco | HU-14, 20 | por definir |
| CU-12 | Validar sesión («include») | — | HU-12 | `POST /sesion` + dependencia de token |

Relaciones:

- CU-01 a CU-09 incluyen («include») CU-12. CU-10 y CU-11 no.
- CU-07 incluye CU-05 cuando la pregunta es «¿me alcanza?» (HU-10).
- CU-03 se relaciona con BCRP (HU-24) y CU-07 con Motor LLM.
- Las «Debería» se marcan en el diagrama con el estereotipo `<<debería>>`: HU-22 entra como extensión («extend») de CU-01 (resumen de quincena) y HU-25 como extensión de CU-01 (negocio vs casa). HU-23 queda dentro de CU-09 y HU-24 dentro de CU-03, con la marca en su flujo.
- HU-11 no es un caso propio: son los flujos de excepción y las reglas de CU-07.
- HU-12 también aporta una excepción a CU-07 («muéstrame al cliente C0002») y HU-17 un alterno a CU-07 («no me hables de inversión»).
- Un caso que mezcla olas (CU-01 tiene HU-15 de ola 2; CU-04 tiene HU-17) marca la ola en cada paso o alterno que no es de ola 1. Así el equipo sabe qué recortar sin romper el caso.

### Ficha de cada caso (plantilla Cockburn completa)

```
### CU-XX · Nombre
| Campo | Valor |
| Actor principal / secundarios |
| Historias | HU-..
| Módulos y palanca | D.., P..
| Ola y prioridad | Ola 1 · DEBE
| Ruta | ...
| Precondiciones |
| Disparador |
| Postcondición de éxito |
| Garantía mínima | lo que se cumple aunque falle (p. ej., «no se guarda nada»)

Flujo principal: pasos numerados actor ↔ Lucas
Flujos alternos: 3a, 5a... (numerados contra el paso principal)
Flujos de excepción: 2e...
Reglas de negocio: con referencia a negocio.md o config/supuestos.yaml
Casos de prueba: CP-SIS-..
```

Cada criterio «Dado/cuando/entonces» de las historias tiene que aparecer como paso, alterno, excepción o regla en algún caso. La matriz final lo comprueba fila por fila.

### Secciones del documento

1. Propósito y alcance (2 párrafos)
2. Actores (tabla de arriba)
3. Diagrama (SVG + enlace al `.puml`)
4. Fichas CU-01 a CU-12
5. Matriz de trazabilidad HU → CU → CP-SIS, con huecos declarados (HU-22, 23 y 25 sin CP-SIS, como en historias.md)
6. Rutas por definir (lista para que backend las cierre en ARCHITECTURE.md)

## Lo que queda al constructor

- La redacción de cada paso, siempre fiel a las historias.
- Agrupar alternos parecidos si quedan repetidos.
- La disposición del diagrama (izquierda/derecha, paquetes) mientras sea legible en A4.

## Verificación

- Cada HU-01…HU-25 aparece en la matriz y en al menos una ficha.
- Cada CP-SIS que citan las historias aparece en alguna ficha.
- El `.puml` regenera el `.svg` sin errores.
- `juez-tecnico` (calidad y trazabilidad) y `juez-producto` (entregable visible) antes de unir a `develop`; anotar veredictos en [verificaciones.md](../../../.claude/planes/verificaciones.md).
