# Guion de la demo de 60 s

Flujo: banca → tarjeta «Lucas lo ve venir» → «Lo hago» → el rojo desaparece → apartar al cobrar.
Persona: independiente con recibo por honorarios, hoy 14 de noviembre, cobra S/ 2,000 el 30 nov. El rojo cae en 14 días, así que la banca muestra «Lucas lo ve venir» (la regla de avisos reserva «Lucas te avisa» para 7 días o menos); dentro de Lucas, el aviso sí dice «Lucas te avisa».

Las cifras de este guion son las que da el motor del front (`frontend/src/motor/motor.js` y `cliente.js`), no se escribieron a mano. La prueba `frontend/e2e/guion-demo.spec.js` revisa que cada cifra de abajo siga saliendo igual en la pantalla. Si alguien cambia el motor y la prueba falla, se actualiza este guion antes de ensayar.

## Antes de empezar (no cuenta en los 60 s)

1. Desde la raíz del repo, levantar la API: `uvicorn --app-dir backend src.api.main:app --host 127.0.0.1 --port 8000`. En otra terminal, `cd frontend` y `npm run dev`, con `VITE_CHAT_AGENTE=si` en `frontend/.env` (copiar `frontend/.env.example`) para que el chat pregunte al agente: medido en esta laptop, las preguntas del chat responden en menos de 1 s con cifras verificadas. Abrir `http://localhost:5173` en el navegador, a pantalla completa. Si al pie de Lucas aparece «No llegaron tus datos del servidor», la API no está levantada (ver plan B).
2. Ingresar una vez con la persona independiente (la que viene elegida), aceptar el permiso con «Acepto, activar Lucas», entrar a Lucas, pulsar «Saltar» en la guía y volver a la banca. Así ni el permiso ni la guía aparecen durante la demo.
3. Si en un ensayo quedaron tips activos, quitarlos con «Lo hago» otra vez (se recuerdan entre visitas). El aviso de Lucas tiene que decir −S/ 60 y los tips, «Días en rojo 2 → 0».
4. Dejar la pantalla en la banca, con los montos visibles.

## Paso a paso

| Tiempo | Pantalla | Qué se toca | Qué se dice |
|---|---|---|---|
| 0:00–0:10 | Banca de Banco Vértice | Nada; señalar la tarjeta «Lucas lo ve venir» | «Una independiente cobra el 30. Esta es su banca, de un banco ficticio: Lucas podría integrarse en la app de cualquier banco.» |
| 0:10–0:20 | Banca → Resumen de Lucas | La tarjeta «Lucas lo ve venir» | «Lucas se adelanta dos semanas: entre el sábado 28 y el domingo 29 podría quedar en rojo. En el peor caso, −S/ 60.» |
| 0:20–0:27 | Resumen, tip 1 | Bajar hasta los tips y «Lo hago» en «Pide RapiFood una vez por semana hasta el 30» | «Le propone cambios con monto. Pedir delivery una vez por semana: +S/ 31 para su día más justo.» |
| 0:27–0:32 | Resumen, tip 2 | Deslizar a la izquierda y «Lo hago» en «Pausa MusiKa Plus hasta tu próximo cobro» | «Pausar una suscripción que no usa: +S/ 22.» |
| 0:32–0:38 | Resumen, tip 3 | Deslizar y «Lo hago» en «Toma café fuera 3 veces por semana»; señalar «Días en rojo 0» | «Menos café fuera: +S/ 19. Ya no queda en rojo.» |
| 0:38–0:46 | Qué viene | La pestaña «Qué viene» y subir hasta arriba | «En su pronóstico, el peor caso pasa a +S/ 12.» |
| 0:46–1:00 | Resumen, tarjeta «Después de cobrar» | La pestaña «Resumen» y deslizar los tips hasta el final | «Y el 30, al cobrar, podría apartar S/ 150 sin volver al rojo; si lo repite en sus próximos 3 cobros, juntaría S/ 450. Lucas gana cuando ella ahorra. No mueve su plata ni es asesoría: ella decide.» |

Son unas 110 palabras: a 2,5 por segundo, unos 45 s de voz y el resto para tocar. Cada cifra que se dice está a la vista en ese momento.

Variante de unos 75 s, si el pitch da más tiempo: abrir «Qué viene» también antes de los tips, para que el jurado vea la línea bajo cero y luego sin rojo. Si sobra tiempo, cerrar con: «Lo que vieron sale de datos sintéticos; en un banco se conectaría a sus movimientos reales.»

## Frases sobre integración

Se pueden decir:

- «Lucas podría integrarse en la app de cualquier banco.»
- «Banco Vértice es un banco ficticio que armamos para mostrar a Lucas dentro de una banca.»
- «Lucas es marca propia; el banco lo pondría con su catálogo y su marca.»
- «No lo encontramos en fuentes públicas» (si preguntan si alguien más lo hace).

No se dicen nunca:

- «Es de BBVA», «producto oficial de BBVA», «la app de BBVA» ni nada que lo sugiera.
- «Nadie lo hace.»
- «Compra dólares», «sin riesgo», «te garantizo», ni ninguna promesa de rentabilidad.
- Porcentajes de retención o mora «de Lucas»: con datos sintéticos no se pueden probar.

## Plan B

El recorrido de 60 s no depende de la API ni del LLM: las cifras de pantalla salen del motor local del front, que funciona sin internet. El front sí pide los datos a la API; si no responde en 4 s, Lucas muestra al pie «No llegaron tus datos del servidor; sigo con los datos de la demo.» y las cifras no cambian.

| Falla | Qué se hace | Qué se dice |
|---|---|---|
| La API (FastAPI) no responde | Seguir: las cifras son las mismas y aparece el aviso de datos al pie de Lucas | «Si el servidor no responde, Lucas lo dice y sigue con los datos de la demo: nunca se queda en blanco.» |
| El LLM (Ollama o Gemini) no responde | Nada: este flujo no usa el chat. El chat solo llama al agente si el front se levantó con `VITE_CHAT_AGENTE=si`; si el agente falla, tarda más de 12 s o no comprueba sus cifras, el chat lo dice («No pude hablar con el agente de Lucas. Te respondo con mis cálculos de siempre.») y responde con plantillas | «Si el agente no responde, Lucas lo dice y sigue con sus cálculos. Un texto del LLM sin cifras comprobadas nunca llega al usuario.» |
| `npm run dev` no levanta o el navegador se cuelga | Abrir la otra laptop con el front ya levantado; si tampoco, pasar las capturas de `docs/demo/capturas/` en orden (`laptop-01-banca.png` … `laptop-05-apartar.png`) | Mismo guion, señalando cada captura |
| Todo lo anterior | Video de respaldo | — |

Pendiente: grabar el video de respaldo y ensayar el guion 3 veces con cronómetro (bases del hackathon).

## Capturas

Las saca la prueba de Playwright en `docs/demo/capturas/`, una serie por tamaño de pantalla (`laptop-` 1366×768 y `celular-` 390 px):

```
cd frontend
npx playwright test e2e/guion-demo.spec.js
```

Con un navegador ya instalado, sin descargar Chromium: `$env:PW_CHROMIUM = "C:\Program Files\Google\Chrome\Application\chrome.exe"` antes del comando. La prueba levanta el front sola con `npm run dev`.
