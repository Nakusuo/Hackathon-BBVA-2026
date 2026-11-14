# Lucas — copiloto de plata (Hackathon BBVA 2026, Equipo 2)

Instrucciones del proyecto para Claude Code. Se cargan solas en cada sesión.

## Qué es

App que responde una sola pregunta para trabajadores del sector privado en Perú:

> «¿Cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?»

Problema principal: **liquidez a 30 días**. Todo lo demás (categorías, recurrentes, salud, recomendaciones, chat) existe para servir a ese problema.

Indicación del juez: Lucas debe ser **el compañero bancario** del cliente. Se adelanta a los problemas, propone acciones con monto y sirve tanto para **fidelizar** clientes actuales como para **atraer** futuros. No vale una demo cosmética ni un chatbot genérico. Ver [reglas/vision-companero.md](reglas/vision-companero.md).

## Dónde está cada cosa

| Carpeta / archivo | Contenido | Cuándo leerlo |
|---|---|---|
| [planes/plan-maestro.md](planes/plan-maestro.md) | Plan completo: alcance, arquitectura, cronograma, pitch | Antes de decidir alcance o arquitectura |
| [planes/tareas.md](planes/tareas.md) | Microtareas por persona, dependencias y formato de avisos | Al empezar y terminar cada tarea |
| [planes/comandos.md](planes/comandos.md) | Comandos fijos: Git, PR, revisión, make, Docker | Siempre que haya que tocar el repo |
| [planes/estado.md](planes/estado.md) | Equipo, decisiones, checkpoints y bloqueos | En cada checkpoint |
| [planes/verificaciones.md](planes/verificaciones.md) | Veredictos de los jueces | Antes de unir una rama; anotar cada veredicto |
| [reglas/vision-companero.md](reglas/vision-companero.md) | Lucas como compañero bancario: fidelización, atracción e ideas priorizadas | Antes de decidir qué construir o cómo presentarlo |
| [reglas/rentabilidad-impacto.md](reglas/rentabilidad-impacto.md) | Cómo gana plata el banco, impacto en S/, innovación, costo y modelo B2B2C | Antes de priorizar, del pitch o de cualquier cifra de negocio |
| [reglas/bases-hackathon.md](reglas/bases-hackathon.md) | Criterios del jurado, pesos y prohibiciones | Antes de cualquier decisión que afecte la evaluación |
| [reglas/negocio.md](reglas/negocio.md) | Reglas de producto, seguridad del recomendador y privacidad | Al tocar recomendador, chat, datos o UI |
| [reglas/gitflow.md](reglas/gitflow.md) | Ramas, commits y merges | Antes de empezar cualquier tarea |
| [reglas/calidad-codigo.md](reglas/calidad-codigo.md) | Anti AI-slop: comentarios, limpieza, textos y UI | Al escribir código, docs o pantallas |
| [reglas/flujo-trabajo.md](reglas/flujo-trabajo.md) | Investigador, codificador, tester y jueces | Para organizar y verificar cada tarea |
| [reglas/seguridad-iso27001.md](reglas/seguridad-iso27001.md) | Declaración de aplicabilidad ISO/IEC 27001:2022 | Al tocar datos, accesos, logs o dependencias |
| [reglas/pruebas-istqb.md](reglas/pruebas-istqb.md) | Estrategia de pruebas ISTQB | Al escribir tests o ejecutar un ciclo |
| [planes/pruebas.md](planes/pruebas.md) | Catálogo de casos, trazabilidad y resultados por ciclo | En cada ciclo de pruebas |
| [investigacion/](investigacion/) | Informes del investigador | Antes de codificar algo con dudas |
| [estadisticas/metricas.md](estadisticas/metricas.md) | Criterios de éxito, baselines y métricas por módulo | Al tocar modelos o evaluación |
| [estadisticas/cifras-publicas.md](estadisticas/cifras-publicas.md) | Cifras de calibración y su estado de verificación | Al calibrar el generador o escribir el pitch/README |
| [agents/](agents/) | Subagentes por rol del equipo | Delegar trabajo de un rol concreto |

## Reglas que no se rompen

1. **El LLM explica, no calcula.** Toda cifra sale de una herramienta (tool) y pasa por el verificador.
2. **Cada técnica tiene su baseline sencillo** y se mide contra él. Sin baseline no entra.
3. **Datos 100 % sintéticos**, con semilla fija. Nunca nombres, DNI, teléfonos, cuentas ni marcas reales.
4. **Sin marca ni colores de BBVA.** Lucas es marca propia. Decimos «podría integrarse», nunca «es de BBVA».
5. **Funciona offline**: Ollama local o plantillas, Postgres en Docker local. Gemini en nivel gratuito es solo respaldo con red, apagado por defecto y sin datos personales. El BCRP tiene serie grabada de respaldo.
6. **No es asesoría**: nunca «compra dólares», nunca prometer rentabilidad, nunca ejecutar operaciones. «Tú decides».
7. **MoSCoW estricto**: primero el flujo de punta a punta; los «Debería» se recortan si el núcleo no funciona.
8. **Compañero, no chatbot**: cada pantalla o idea debe mejorar una decisión real. Si es solo decoración, fuera.
9. **Gitflow**: nunca trabajar directo en `main` ni `develop`; cada tarea en `feature/<rol>-<tema>`.
10. **Anti AI-slop**: comentarios solo para explicar el porqué, sin código muerto ni textos de plantilla.
11. **Nada se une sin juez**: cada rama pasa por `juez-tecnico` y, si se ve en la demo, por `juez-producto`.
12. **Seguridad ISO 27001 y pruebas ISTQB**: decimos «alineado con», nunca «certificado»; nada se entrega sin cumplir los criterios de salida de pruebas.
13. **Gana el banco cuando gana el cliente**: cada función se ata a una palanca de [reglas/rentabilidad-impacto.md](reglas/rentabilidad-impacto.md) y a un impacto en S/. Nunca cifras de retención o mora inventadas; solo supuestos visibles.
14. **Núcleo rentable primero**: la ola 1 del plan maestro se termina antes de empezar la ola 2.

## Agentes

| Rol | Agentes |
|---|---|
| Investigador | `investigador` |
| Codificadores | `codificador` (general) y por área: `datos`, `ml-analitica`, `ia-chat`, `backend`, `frontend-ux`, `pitch-docs` |
| Tester (ISTQB) | `tester` |
| Jueces | `juez-tecnico`, `juez-producto`, `juez-cumplimiento` |

## Forma de trabajar

- Idioma: español, explicaciones simples.
- Commits pequeños y frecuentes, en español, sin coautor ni atribución a IA. No hacer push sin preguntar.
- Secretos solo en `.env` (está en `.gitignore`); `.env.example` con valores ficticios.
- Cuando se decida algo importante, anotarlo en [planes/estado.md](planes/estado.md) (sección «Decisiones»).
- Comandos del equipo: [planes/comandos.md](planes/comandos.md). Microtareas: [planes/tareas.md](planes/tareas.md).
