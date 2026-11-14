# Bases del hackathon — lo que evalúa el jurado

Fuente: bases finales «AI Financial Life» (14–15 nov 2026). Resumen operativo; si hay duda, mandan las bases originales.

> **Principio rector:** la mejor solución no es la más compleja, sino la que convierte datos e IA en una decisión financiera más clara, segura y demostrablemente útil.

## Pesos de evaluación

| Criterio | Peso | Cómo lo atacamos |
|---|---|---|
| IA y analítica | 25 % | Cada modelo frente a su baseline; bandas con cobertura medida; verificador de cifras |
| Calidad técnica | 25 % | Tests, `make` reproducible, arquitectura en 3 capas, validación Pydantic, fallback |
| Valor | 15 % | Un problema (liquidez a 30 días), una población, una decisión concreta |
| Producto y UX | 15 % | 5 pantallas, tiempo hasta insight < 60 s, accesibilidad AA |
| Innovación | 10 % | Verificador de cifras, banda según tipo de ingreso, calendario peruano |
| Demo | 10 % | Guion ensayado 3 veces, video de respaldo, funciona sin red |

Rigor + baseline + tests ≈ 50 % de la nota. La escalabilidad ya no tiene peso propio.

## Exigencias explícitas

- Elegir **un problema principal** y **una población usuaria** definida.
- **No hay puntos extra** por usar más agentes, modelos o servicios. Cada técnica se compara con una alternativa sencilla.
- Separar **ingesta/preparación**, **lógica analítica/IA** e **interacción**.
- Datos legales y reproducibles (semilla, controles de calidad, particiones sin fuga).
- El trabajo del evento debe distinguirse: commits desde el sábado y atribución de código reutilizado.

## Prohibido o penalizado

- Usar marcas, logos, colores o interfaces bancarias como si fuera producto oficial.
- Datos confidenciales o personales. La privacidad se penaliza si hay riesgo.
- Enviar datos personales a un LLM externo. BBVA **no da** API keys, créditos cloud ni GPU.

## Prueba de evolución (sorpresa)

Cambios probables: ingresos variables, movimientos duplicados, exigir explicabilidad.
Protocolo: (1) leer el cambio → (2) agregar escenario al generador → (3) test que falla → (4) arreglar → (5) mostrar antes/después en el panel Evidencia.

## Checklist de salida (sección 09 de las bases)

- [ ] Problema y usuario definidos
- [ ] Datos legales y reproducibles (`make data`, semilla, QUALITY.md)
- [ ] MVP ejecutable (`make run`, también offline)
- [ ] IA/ML aporta valor medido (EVALUATION.md)
- [ ] Baseline y casos adversos
- [ ] Seguridad y explicabilidad
- [ ] README y arquitectura
- [ ] Demo ensayada (3 veces + video de respaldo)
- [ ] Entrega completa (repo accesible al jurado)

## Preguntas pendientes a la organización

1. ¿Se autoriza un LLM externo con clave propia (sin datos personales)?
2. ¿Hay dataset común o lo generamos nosotros?
3. ¿Se pueden usar APIs públicas (BCRP) en la demo?
4. Formato de entrega (repo público/privado, hora de cierre); confirmar 10 + 3 min.
5. ¿Se activa la prueba de evolución? ¿Cuándo y con qué peso?
6. ¿Se pueden traer modelos y dependencias descargados?

Anotar las respuestas en [../planes/estado.md](../planes/estado.md).
