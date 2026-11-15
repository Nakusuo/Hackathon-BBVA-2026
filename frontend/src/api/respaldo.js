// Los JSON de demo-001 (los genera el motor, así que dicen lo mismo que la pantalla) y los ejemplos del contrato: si la API no responde, la pantalla los usa y lo dice.
import eventos from '../../../data/sample/demo-001/events.json' with { type: 'json' }
import pronostico from '../../../data/sample/demo-001/forecast.json' with { type: 'json' }
import tipoCambio from '../../../data/sample/mocks/fx.json' with { type: 'json' }
import salud from '../../../data/sample/demo-001/health.json' with { type: 'json' }
import recomendaciones from '../../../data/sample/demo-001/recommendations.json' with { type: 'json' }
import simulacion from '../../../data/sample/mocks/simulation.json' with { type: 'json' }

export const RESPALDO = { salud, pronostico, recomendaciones, eventos, tipoCambio, simulacion }
