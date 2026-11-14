# Calidad y anti AI-slop

Si algo rompe una regla, se quita. Lo revisa el juez técnico antes de cada merge.

## Código

1. **Comentarios justos y necesarios.** Solo explican el *porqué* (una decisión, un supuesto, una trampa). Nunca narran lo que el código ya dice (`# suma los montos`).
2. Sin comentarios de relleno: nada de `# ===== SECCIÓN =====`, `# Paso 1:`, emojis ni banners.
3. Docstring de una línea en funciones públicas; más solo si hay supuestos o unidades que aclarar (por ejemplo, «montos en S/, positivos»).
4. Sin código muerto, sin código comentado, sin `print` de depuración. Usar `logging`.
5. Sin `TODO` huérfanos: o se hace, o va a [../planes/estado.md](../planes/estado.md) con dueño.
6. Sin `try/except` que se trague errores. Capturar lo concreto y decidir qué pasa (fallback, mensaje claro).
7. Sin abstracciones por si acaso: nada de fábricas, clases base ni capas que hoy tienen un solo uso. Excepción acordada: `LLMProvider`.
8. Sin dependencias nuevas sin motivo. Si se agrega una, va con versión fija en `requirements.txt`.
9. Nombres claros. Términos del dominio en español y consistentes con el esquema (`fecha_hora`, `monto`, `colchon_meses`).
10. Funciones cortas. Si un archivo pasa de ~300 líneas, partirlo.
11. Cada cambio de lógica trae su test. Cada modelo trae su baseline.
12. Formato y lint antes de commitear: `ruff format` y `ruff check`.

## Textos (README, docs, UI, pitch)

13. **Nada inventado.** Cifras, anécdotas o logros solo si salen de `make eval`, del código o de [../estadisticas/cifras-publicas.md](../estadisticas/cifras-publicas.md) con fuente verificada.
14. Sin frases de plantilla: «revoluciona», «lleva tus finanzas al siguiente nivel», «potenciado por IA», «en 30 segundos».
15. Sin «·» ni «—» de relleno. Comas y puntos.
16. Los botones dicen qué pasa («Ver mi pronóstico», «Simular»), no adornan.
17. Frases cortas, tono cercano peruano, sin jerga financiera sin explicar.

## Diseño de la UI

18. Nada inclinado, sin notas a mano, cinta adhesiva, sellos ni post-its de adorno.
19. Sin filas de números gigantes ni cajitas de «impacto» con borde de color e icono.
20. Máximo 4 tipografías. Colores como variables con nombre, una familia y un solo acento. Contraste ≥ 4.5:1.
21. Sin degradados morado/azul genéricos, sin vidrio esmerilado por defecto, sin emojis como iconos.
22. Cada pantalla cabe en 1366×768 y tiene un motivo claro. Si no aporta, fuera.
23. Antes de dar la UI por terminada: verla en claro y oscuro, en 1366×768 y en celular, y repasar esta lista.

## Limpieza del repo

- Sin archivos sueltos de prueba (`test2.py`, `nuevo.ipynb`, `copia_final.py`).
- Notebooks solo en `eval/` o `notebooks/`, sin salidas pesadas.
- `.gitignore` al día: entornos, cachés, `.env`, volcados de la base, datos generados grandes.
