# Fuentes para el RAG: licencias y validez en Perú

Consulta: 2026-11-14. Responsable de cargarlas: Jeffrey (JF-01, JF-05). Apoyo: Dixon.

## Pregunta

¿Qué PDFs de educación financiera y de regulación bancaria podemos usar en el RAG con una licencia libre o un uso permitido, que sirvan para la banca en Perú y tengan respaldo legal peruano e internacional?

## Regla para el equipo

Solo entra al RAG lo que esté en **nivel A** o **nivel B**. Nivel C queda fuera hasta que se confirme la licencia. Cada documento lleva su fila en `docs/rag/fuentes.csv` y cada respuesta del agente cita la fuente.

| Nivel | Significa | Se puede |
|---|---|---|
| **A** | Dominio público, licencia abierta o reproducción permitida citando la fuente | Cargar al RAG y citar |
| **B** | Creative Commons con restricciones (no comercial, sin derivadas) | Cargar fragmentos **textuales** con cita; no reescribir ni redistribuir el PDF |
| **C** | Licencia no confirmada o con copyright | Solo enlazar. No entra al RAG |

## Por qué la regulación peruana es nivel A

El **Decreto Legislativo 822 (Ley sobre el Derecho de Autor), artículo 9**, excluye de la protección a los textos oficiales de carácter legislativo, administrativo o judicial, con la obligación de respetar el texto y citar la fuente. Indecopi lo ha aplicado en sus resoluciones. Leyes, reglamentos y resoluciones de la SBS y la SMV se pueden cargar, siempre citando.
Fuentes: [WIPO Lex, DL 822](https://www.wipo.int/wipolex/es/legislation/details/18762), [versión actualizada en LP Derecho](https://lpderecho.pe/ley-sobre-derecho-autor-decreto-legislativo-822-actualizada/), [jurisprudencia Indecopi (Cerlalc)](https://cerlalc.org/wp-content/uploads/dar/jurisprudencia/1850.pdf).

Ojo: las **guías educativas** de la SBS no son textos legislativos ni administrativos, así que el artículo 9 no las cubre con seguridad (ver nivel C).

## Fuentes por módulo

### Regulación peruana (nivel A, textos oficiales)

| Documento | Módulo | Para qué sirve en Lucas | Enlace |
|---|---|---|---|
| Res. SBS 3274-2017, Reglamento de Gestión de Conducta de Mercado (con modificatorias 2025 y 2026) | Deudas, derechos, seguros | Transparencia, TCEA, información al usuario, trato justo | [Banco de la Nación](https://www.bn.com.pe/transparenciabn/transparencia-financiera/Res-SBS-3274-2017-Reglamento-Gestion-Conducta-Mercado.pdf) · [El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/2378225-1) |
| Res. SMV 011-2026-SMV/01 (perfil de riesgo y asesoría de inversiones) | Inversión básica | Sustenta por qué Lucas **no** da recomendaciones personalizadas de inversión: la norma exige evaluar el perfil de riesgo antes de asesorar | [SMV en gob.pe](https://www.gob.pe/institucion/smv/normas-legales/8492182-011-2026-smv-01) · [resumen CMS](https://cms.law/es/per/publication/smv-homologa-la-asesoria-y-regula-la-gestion-de-carteras-de-terceros) |
| Ley 29733 y su Reglamento (DS 016-2024-JUS) | Derechos (privacidad) | Base legal de la memoria del usuario: consentimiento, derecho a borrar | [ANPD en gob.pe](https://www.gob.pe/institucion/anpd/normas-legales/6554453-16-2024-jus) · [Congreso](https://www.congreso.gob.pe/Docs/DGP/DIDP/files/ds_016-2024-jus.pdf) |
| Ley 29571, Código de Protección y Defensa del Consumidor (capítulo de servicios financieros) | Derechos | Reclamos y derechos frente a bancos | *Buscar texto oficial en El Peruano o gob.pe (JF-01)* |
| Plan Estratégico Multisectorial de la Política Nacional de Inclusión Financiera (MEF) | Contexto | Marco oficial de educación financiera en Perú (pitch y README) | [MEF](https://www.mef.gob.pe/contenidos/archivos-descarga/Plan_Estrategico_Multisectorial_PEM.pdf) |

Usar las copias del Banco de la Nación, El Peruano o gob.pe. **No** usar las copias alojadas en sitios de bancos privados, para no dar la impresión de ser un producto oficial.

### Entidades públicas peruanas (nivel A, reproducción permitida citando)

| Documento | Módulo | Licencia | Enlace |
|---|---|---|---|
| Cartillas educativas del BCRP | Ahorro, conceptos básicos | Las condiciones de uso del BCRP dicen: «Puede reproducirse total o parcialmente, sin autorización expresa, siempre y cuando se cite la fuente.» Esa frase está en el portal de estadísticas; confirmar que aplica a las cartillas | [Condiciones de uso](https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/condiciones-de-uso) · [Cartilla 5.º secundaria](https://www.bcrp.gob.pe/docs/Proyeccion-Institucional/sala-economia/cartillas/cartilla-profesores-5-secundaria.pdf) |

### Internacional (nivel A)

| Documento | Módulo | Licencia | Enlace |
|---|---|---|---|
| CFPB, «Su dinero, sus metas» (kit en español) | Salud financiera, metas, ahorro, presupuesto | Gobierno federal de EE. UU.: dominio público (17 U.S.C. §105); la política del CFPB dice que su contenido se puede reproducir sin permiso | [Kit en español](https://files.consumerfinance.gov/f/201603_cfpb_your-money-your-goals_toolkit_spanish.pdf) |
| CFPB, folleto de crédito (español) | Deudas | Dominio público | [PDF](https://files.consumerfinance.gov/f/documents/cfpb_your-money-your-goals_credit_booklet_cobrand_es.pdf) |
| CFPB, folleto «atrasado en los pagos» (español) | Deudas | Dominio público | [PDF](https://files.consumerfinance.gov/f/documents/bcfp_your-money-goals_behind-on-bills_booklet_es_print.pdf) |
| CFPB, plan de acción para deudas (español) | Deudas | Dominio público | [PDF](https://files.consumerfinance.gov/f/documents/cfpb_YMYG_toolkit_spanish_debt_action_plan_ADA3.21.pdf) |
| FDIC, Money Smart para Adultos (14 módulos en español) | Ahorro, crédito, presupuesto, inversión básica | Gobierno federal de EE. UU.; confirmar que el módulo elegido no tenga material de terceros | [FDIC](https://fdic.gov/consumer-resource-center/money-smart-para-adultos) |
| Banco Mundial, *Good Practices for Financial Consumer Protection* (2017) | Derechos, protección al consumidor | CC BY 3.0 IGO en el repositorio; el PDF dice «uso no comercial con atribución». El hackathon no es comercial, así que cumple las dos | [Repositorio](https://openknowledge.worldbank.org/entities/publication/ff9c9482-5ffe-5c98-b6f3-5b97eeab5ed1) · [PDF](https://documents1.worldbank.org/curated/en/492761513113437043/pdf/Good-practices-for-financial-consumer-protection-2017-edition.pdf) |
| Banco Mundial / CGAP / SBS, *Financial Inclusion and Consumer Protection in Peru: The Branchless Banking Business* | Contexto Perú | CC BY 3.0 IGO | [Repositorio](https://openknowledge.worldbank.org/entities/publication/6e86f48b-ba5a-555e-81c5-7afbc81eafe9/full) |

**Cuidado con CFPB y FDIC:** explican leyes y productos de EE. UU. (reportes de crédito, FICO, seguros de depósito de EE. UU.). Solo se cargan los capítulos generales (presupuesto, metas, ahorro, manejo de deudas). Cada fragmento lleva la etiqueta `contexto: EE. UU.` y el agente nunca lo usa para hablar de leyes peruanas; para eso están los textos de la SBS y la SMV.

### Nivel B (Creative Commons con restricciones)

| Documento | Licencia | Uso |
|---|---|---|
| CAF, *Capacidades financieras de las mujeres* (Brasil, Colombia, Ecuador y Perú) | CC BY-NC-ND 4.0 | Fragmentos textuales con cita; útil para cifras del pitch. [PDF](https://findevgateway.org/sites/default/files/publications/2024/Capacidades%20financieras%20de%20las%20mujeres.%20Brechas%20de%20g%C3%A9nero%20en%20las%20encuestas%20de%20capacidades%20financieras%20de%20CAF_Brasil%2C%20Colombia%2C%20Ecuador%20y%20Per%C3%BA.pdf) |

### Nivel C (no entra al RAG hasta confirmar)

| Documento | Motivo | Qué hacer |
|---|---|---|
| Guías de educación financiera de la SBS («Domina tus finanzas», «Para vivir seguros», «Infórmate y planea tu ahorro para el futuro») | Son ideales por contenido, pero no encontré sus condiciones de uso (la página de la SBS no cargó) | Revisar el aviso legal de sbs.gob.pe o preguntar a la organización. Si se confirma, pasan a A. [Página de materiales](https://www.sbs.gob.pe/material-de-educacion-financiera) · [Finanzas para ti](https://www.sbs.gob.pe/educacion-financiera/Finanzas-para-ti) |
| Encuestas Nacionales de Capacidades Financieras SBS–CAF (2019, 2022, 2026) | Licencia no visible en los resultados | Revisar los créditos del PDF. Pueden ser la fuente del 61 % del pitch. [Scioteca CAF 2019](https://scioteca.caf.com/handle/123456789/1689) |
| OCDE, Recomendación del Consejo sobre Educación Financiera (2020) | © OCDE, sin permiso de reproducción confirmado | Solo citar y enlazar en el README como marco internacional. [OECD/LEGAL/0461](https://legalinstruments.oecd.org/public/doc/77/77.en.pdf) |

## Recomendación

1. **Núcleo del RAG (cargar primero):** Res. SBS 3274-2017, Res. SMV 011-2026, Ley 29733 + DS 016-2024-JUS, CFPB «Su dinero, sus metas» y los folletos de deudas, Banco Mundial 2017.
2. **Segundo paso:** cartillas del BCRP, FDIC Money Smart, Ley 29571.
3. **Hacer en el bloque 1:** preguntar a la organización si se pueden usar las guías de la SBS (agregado a las preguntas en `reglas/bases-hackathon.md`). Son las más alineadas con Perú.

## Riesgos

- Mezclar consejos de EE. UU. con leyes peruanas → etiqueta `contexto` + juez del agente.
- Normas con modificatorias → usar el texto consolidado o anotar la fecha de la versión.
- Las licencias se verificaron desde los avisos públicos el 2026-11-14; si una fuente cambia su aviso, se retira.
