// Los mismos JSON de ejemplo del contrato: si la API no responde, la pantalla los usa y lo dice.
import eventos from '../../../data/sample/mocks/events.json' with { type: 'json' }
import pronostico from '../../../data/sample/mocks/forecast.json' with { type: 'json' }
import tipoCambio from '../../../data/sample/mocks/fx.json' with { type: 'json' }
import salud from '../../../data/sample/mocks/health.json' with { type: 'json' }
import recomendaciones from '../../../data/sample/mocks/recommendations.json' with { type: 'json' }
import simulacion from '../../../data/sample/mocks/simulation.json' with { type: 'json' }

export const RESPALDO = { salud, pronostico, recomendaciones, eventos, tipoCambio, simulacion }
