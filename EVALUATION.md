# Evaluación de Lucas

Lucas se evalúa con datos sintéticos de semilla fija. El detalle, con cada tabla y su método, está en [docs/EVALUACION_ANALITICA.md](docs/EVALUACION_ANALITICA.md); este archivo solo dice qué se mide y dónde mirar.

## Qué se evalúa

- **Modelos entrenados** (segmentación, pronóstico a 30 días, proyección mensual, clasificación de glosas, impacto): cada uno se mide contra un baseline sencillo (promedio móvil, reglas 2x2, etc.).
- **Pronóstico en una muestra nueva**: se probó sin reentrenar con 500 clientes de otra semilla. La cobertura de la banda al 80 % a 30 días fue 0.806 en la muestra de entrenamiento y 0.772 en la nueva (sección «Prueba con otra muestra del generador»).
- **RAG y agente**: recuperación de fuentes, rutas del agente con plantillas y verificación de que toda cifra salga de una herramienta.
- **Módulos de reglas** (ofertas, recomendador, puntos, clima, campañas, calendario laboral): no son modelos, se comprueban con pruebas en `backend/tests` (sección 11 del documento).
- **Puerta de calidad**: [docs/QA_ANALITICA.md](docs/QA_ANALITICA.md), con 52 PASS, 3 WARN, 0 FAIL y 3 NOT RUN en su última corrida.

## Límites

Los datos son sintéticos: las cifras muestran que el método funciona sobre los supuestos del generador, no cuánto ahorraría un cliente real. Un piloto con datos reales mediría el impacto.

## Cómo reproducirlo

```bash
make data    # datos de muestra
make eval    # entrena y evalúa los modelos
make test    # pruebas de backend y front
```
