# Flujo de trabajo: investigador, codificador y jueces

Cada tarea pasa por tres roles. Así se verifica lo que avanza y no solo se acumula código.

```
Investigador ──► Codificador ──► Tester ──► Jueces ──► merge a develop
   (qué y cómo)    (rama feature)   (casos ISTQB)  (aprueban o devuelven)
```

## 1. Investigador (`investigador`)

- Entra cuando la tarea tiene dudas: qué técnica usar, qué librería, qué cifra pública, qué dice la documentación.
- Entrega un informe corto en `.claude/investigacion/<tema>.md`: opción recomendada, alternativa sencilla (baseline), fuentes con enlace y riesgos.
- No escribe código del producto.
- Si la tarea es obvia, se salta este paso.

## 2. Codificador (`codificador` o el agente de su área)

- Agentes de área: `datos`, `ml-analitica`, `ia-chat`, `backend`, `frontend-ux`, `pitch-docs`.
- Trabaja en su rama `feature/<rol>-<tema>` ([gitflow.md](gitflow.md)).
- Primero el test o el baseline, luego la implementación.
- Cumple [calidad-codigo.md](calidad-codigo.md).
- Al terminar: `make test`, commit y aviso a los jueces con la lista de archivos tocados.

## 2b. Tester (`tester`)

- Diseña casos con técnicas ISTQB y ejecuta los ciclos de pruebas del sistema ([pruebas-istqb.md](pruebas-istqb.md)).
- Registra resultados en [../planes/pruebas.md](../planes/pruebas.md) y abre defectos.

## 3. Jueces

Revisan **el código y los resultados**, no el resumen del codificador. Cada uno es independiente.

| Juez | Revisa | Cuándo |
|---|---|---|
| `juez-tecnico` | Tests, baseline, anti-slop, gitflow, seguridad del código | Antes de cada merge a `develop` |
| `juez-producto` | Valor real, compañero frente a chatbot, fidelización y atracción, innovación, UX | Al cerrar cada módulo visible y antes de cada ensayo |
| `juez-cumplimiento` | Bases del hackathon, marca, privacidad, secretos, checklist de entrega | Antes de `release/entrega` y antes de entregar |

Veredicto posible: **APRUEBA**, **CAMBIOS** (lista concreta) o **RECHAZA** (motivo).
Con CAMBIOS o RECHAZA, la tarea vuelve al codificador. Solo con APRUEBA se une a `develop`.

Cada veredicto se anota en [../planes/verificaciones.md](../planes/verificaciones.md).

## Cómo pedirlo a Claude

- «Usa el investigador para comparar ETS y regresión para el pronóstico.»
- «Usa el agente ml-analitica para implementar la banda en la rama feature/ml-pronostico-banda.»
- «Pasa la rama feature/ml-pronostico-banda por el juez técnico.»
