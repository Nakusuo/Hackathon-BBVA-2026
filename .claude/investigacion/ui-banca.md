# UI de banca móvil y dónde va Lucas

Consulta: 14/11/2026. Marcas: **[V]** verificado en la fuente enlazada · **[I]** inferencia nuestra (no hay fuente que lo diga).

## 1. Pregunta

¿Cómo se ordenan las apps de banca y sus funciones de finanzas personales, y cómo encajamos Lucas (banca anfitriona → botón → espacio Lucas → chat → guía) sin parecer copia de un banco real?

## 2. Patrones comunes

| Patrón | Ejemplos | Estado |
|---|---|---|
| **Ocultar saldo** es estándar | BCP: icono o deslizar el dedo [1]. Interbank: «ocultar tus saldos para mayor privacidad» [2]. BBVA Perú: «modo discreto», con la mano o con la cámara (oct. 2023) [3] | [V] |
| **Inicio = saldo + operaciones frecuentes** | Interbank: pagos rápidos y operaciones más usadas en el inicio [2]. BBVA España 2025: tarjetas y contactos frecuentes al entrar; la app reordena según hábitos [4] | [V] |
| Orden típico: saludo → saldo (ocultable) → accesos rápidos → movimientos → barra inferior | Es lo que se repite en las capturas de las tiendas; ninguna fuente oficial lo describe así | [I] |
| **Gastos por categoría, automáticos y corregibles** | BBVA Perú «Mi día a día» agrupa por categoría y deja recategorizar [5]. Revolut: recategorizar «solo esta» o «todas del comercio», ciclo que empieza el día de pago [6]. Monzo Trends: categorías estándar, con Ingresos, Ahorro y Transferencias separados del gasto [7] | [V] |
| **Comparar con tu promedio** | Interbank (servicio Smart): mes actual frente al promedio de 3 meses por categoría [8] | [V] (función antigua) |
| **«Te queda por gastar» tras pagos próximos** | Monzo Trends > Balance: estima lo que queda después de los pagos programados [7]. BBVA España prevé recibos «con semanas e incluso meses» de anticipación y propone apartar [9] | [V] |
| **Coach que diagnostica y propone por categoría** | BBVA España 2025: diagnóstico de ingresos, gastos, ahorro y préstamos; el usuario elige una meta [4] | [V] |
| **Sugerencias en el chat** | Erica: «Hi, I'm Erica. How can I help?» abre temas sugeridos [10]. Cleo: chat como interfaz principal y tono informal [11] | [V] Erica · Cleo solo reseñas (apoyo) |
| Recomendaciones personalizadas arriba del inicio | Nubank, 2023 [12] | [V] |

No encontré fuente pública sobre categorías de gasto en BCP Banca Móvil (lo hace su otra app, Warda), Scotiabank Perú ni Yape. No lo afirmamos.

## 3. Cómo se entra al asistente

| Entrada | Quién | Pros / contras |
|---|---|---|
| Icono flotante | Erica: icono en el borde, se puede arrastrar y se vuelve translúcido a los 5 s [13] | [V] Siempre a mano, pero tapa contenido y se ignora |
| Barra tipo buscador arriba | Bank of America, mar. 2024 [14] | [V] Invita a preguntar; requiere que el chat sea bueno |
| Icono en la cabecera | Blue (BBVA España): icono «?» arriba a la derecha [15] | Fuente de prensa; queda escondido |
| Tarjeta en el inicio con un dato | Nubank (recomendaciones arriba) [12] | [V] |

**Recomendación [I]:** una **tarjeta proactiva en el inicio** con un dato real («El jueves 27 podrías quedar en rojo · Ver plan») y un **acceso fijo en la barra inferior** («Lucas»). Nada de burbuja flotante. ¿Por qué? Lucas es «compañero, no chatbot»: el valor tiene que verse antes de abrir el chat (regla 8 y F1). Además, la burbuja flotante tapa contenido en 1366×768.

## 4. Buenas prácticas con fuente

- Botones de al menos **24×24 px** (WCAG 2.2, criterio 2.5.8, nivel AA); 44×44 es AAA [16]. Para el dedo usamos 44 px.
- Contraste: **4,5:1** para texto normal y **3:1** para texto grande, es decir 24 px o 18,5 px en negrita (criterio 1.4.3) [17].
- **Tutoriales:** el estudio de NN/g (70 personas) no encontró más tareas logradas con tutorial (91 % frente a 94 % sin él), y quienes lo vieron las calificaron más difíciles (4,92 frente a 5,49) [18]. Recomienda ayuda en contexto [V].
- **Revisión de nuestra paleta** (calculé las razones de contraste con la fórmula WCAG; no están verificadas con una herramienta):
  - Azul profundo #16587B sobre crema #F5EEDD: **6,7:1**. Sirve para texto.
  - Blanco sobre #16587B: **7,7:1**. Sirve para botones.
  - #16587B sobre azul claro #84B3CE: **3,4:1**. Solo texto grande o iconos.
  - **#84B3CE sobre crema: 1,9:1**. No sirve ni para texto ni para bordes de controles. Usarlo solo de fondo o decoración.

## 5. Estructura recomendada para el prototipo [I]

1. **Banca anfitriona (genérica, nombre ficticio):**
   - Saludo.
   - Saldo con ojo para ocultarlo.
   - Cuentas.
   - 4 accesos rápidos.
   - **Tarjeta Lucas con el aviso del día.**
   - Últimos movimientos.
   - Barra inferior: Inicio · Operaciones · **Lucas** · Más.
2. **Espacio Lucas, en este orden:**
   1. «Tu quincena»: cuánto puedes gastar hasta el próximo ingreso, banda y día de riesgo. Responde la pregunta central en menos de 60 s.
   2. Aviso y acción con monto («aparta S/ 380»), con botón al simulador.
   3. «Lo que aprendí de ti»: 3 a 4 hechos con su fuente («Cobras los 15 y 30», «Netflix y Spotify cada mes»), cada uno con «¿Es correcto?» para corregir, como Revolut y BBVA.
   4. Gastos por categoría frente a tu promedio de 3 meses (comida, salidas, entretenimiento, suscripciones, gasto hormiga).
   5. Tips: máximo 2, cada uno con monto en S/.
   6. Entrada al chat.
3. **Chat:**
   - 3 a 4 preguntas sugeridas, como Erica.
   - Cada cifra con su ✓ de verificación.
   - Aviso fijo «Tú decides».
4. **Guía de primera vez:**
   - Máximo 3 marcas en contexto (saldo de la quincena, «lo que aprendí», chat).
   - Botón «Saltar» visible.
   - Se puede reabrir desde «?».
   - Nada de carrusel de bienvenida (NN/g [18]).

**Baseline de UX:** la misma información en una lista plana sin tarjeta proactiva ni guía. **Cómo medimos:** el tiempo hasta ver el día de riesgo (< 60 s, métrica 3) con 3 personas del equipo que no hicieron el front.

## 6. Qué evitar para no parecer un banco real

- Nombres, logos, colores insignia o tipografías de BBVA, BCP, Interbank, Scotiabank, Mibanco, Yape o Plin. «Mi Banca» se descartó por parecerse a Mibanco; el banco ficticio es «Banco Vértice» (sin coincidencias en una búsqueda web del 14/11/2026; falta revisar el registro de la SBS). Tampoco el azul marino con aqua de BBVA ni el morado de Yape [I]. Nuestra paleta crema y azules está bien, pero sin degradados que imiten a ningún banco.
- Nombres de funciones reales: «Mi día a día», «Mis finanzas», «modo discreto», «Trends», «Blue», «Plin», «Yapear». Usar nombres propios: «Tu quincena», «Ocultar montos».
- Copiar la distribución exacta de una pantalla real a partir de capturas.
- La banca anfitriona se rotula como «Banca de ejemplo», con datos sintéticos. El pie dice «Lucas podría integrarse en cualquier banca».

## 7. Riesgos

- Que la banca anfitriona robe tiempo. Hacerla estática, con una sola pantalla.
- Que el azul claro se use en texto y falle el AA.
- Que la guía tape la demo. Saltarla en el guion.

## 8. Fuentes (consultadas el 14/11/2026)

1. BCP, ocultar saldos: https://www.viabcp.com/ayuda-bcp/banca-movil/como-ocultar-saldos-app-banca-movil-bcp (403 al abrirla; contenido tomado del resultado del buscador)
2. Interbank APP, App Store: https://apps.apple.com/pe/app/interbank-app/id378649517
3. BBVA, modo discreto Perú (12/10/2023): https://www.bbva.com/es/pe/innovacion/bbva-incorpora-modo-discreto-en-su-app-para-fortalecer-la-seguridad/
4. BBVA, nueva app España (20/05/2025): https://www.bbva.com/es/es/innovacion/bbva-se-reinventa-con-una-nueva-app-en-espana-con-mas-ia-personalizable-y-que-incentiva-el-ahorro/
5. BBVA Perú, Mi día a día: https://www.bbva.pe/blog/mis-finanzas/ahorro/ahorrar-es-mas-simple-usando-mi-dia-a-dia-del-app-bbva.html
6. Revolut, categorías: https://help.revolut.com/help/app-features/budgeting-and-analytics/managing-analytics-categories/
7. Monzo, Trends: https://monzo.com/ie/help/managing-money/help-trends
8. Interbank, blog: https://dxp.dev.interbank.pe/blog/interbank-para-mi/interbank-app-el-tiempo-en-tus-manos
9. BBVA, evitar descubiertos (08/07/2025): https://www.bbva.com/es/innovacion/adelantate-a-los-imprevistos-asi-te-ayuda-la-app-de-bbva-a-evitar-descubiertos/
10. Bank of America, Erica: https://promotions.bankofamerica.com/digitalbanking/instructions/erica
11. Cleo, blog (apoyo): https://web.meetcleo.com/blog/meet-cleo-your-very-own-ai-budgeting-assistant
12. Nubank, recomendaciones en el inicio: https://nu.com/en/newsroom/consumers/nubank-launches-personalized-recommendations-in-the-app-homescreen
13. Bank of America, guía de Erica (PDF): https://message.bankofamerica.com/onlinebanking_demo/mobileApp_Simulator/erica_qrg/Virtual_Financial_Assistant_Erica_QRG_PDF.pdf
14. American Banker (14/03/2024): https://americanbanker.com/news/bank-of-america-gives-erica-a-search-bar-look-as-it-tests-gen-ai
15. Blue, BBVA (prensa, apoyo): https://roams.es/actualidad/finanzas/bbva-revoluciona-la-atencion-al-cliente-asi-usara-la-inteligencia-artificial-con-su-asistente-blue/
16. W3C, criterio 2.5.8: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
17. W3C, criterio 1.4.3: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
18. NN/g, tutoriales móviles: https://www.nngroup.com/articles/mobile-tutorials/

No hay cifras nuevas para `cifras-publicas.md`: este tema es de diseño, no de calibración.
