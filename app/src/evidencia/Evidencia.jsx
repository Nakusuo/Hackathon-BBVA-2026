import { CaretLeft } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { enSoles } from '../formato.js'
import { DIAS_PARA_AVISAR } from '../lucas/avisos.js'
import { cifra } from './cifras.js'
import {
  agente,
  estrategias,
  impactoPorCliente,
  MARGEN_PARECIDO,
  perturbaciones,
  supuestosImpacto,
  tecnicas,
  valorBanco,
} from './secciones.js'

const decimales = (n) => new Intl.NumberFormat('es-PE', { minimumFractionDigits: n, maximumFractionDigits: n })
const FORMATOS = {
  soles: (v) => enSoles(Math.round(v)),
  'soles-centimos': (v) => enSoles(Math.round(v * 100) / 100),
  decimal: (v) => decimales(2).format(v),
  decimal3: (v) => decimales(3).format(v),
  decimal5: (v) => decimales(5).format(v),
  entero: (v) => decimales(0).format(v),
  pct: (v) => `${decimales(1).format(v * 100)} %`,
  segundos: (v) => `${decimales(1).format(v)} s`,
}
const formatear = (formato, v) => FORMATOS[formato](v)

const VEREDICTOS = { mejor: 'Mejor que el baseline', peor: 'Peor que el baseline', parecido: 'Casi igual' }
const CAMBIO = { mejor: 'Mejora', peor: 'Empeora', parecido: 'Casi igual' }
const SUBGRUPO = { mejor: 'Error menor que en todos', peor: 'Error mayor que en todos', parecido: 'Casi igual' }
const GRUPOS = { segmento: 'Segmento', tipo_trabajo: 'Tipo de trabajo', arquetipo: 'Arquetipo', region: 'Región' }

// Agrupa las claves por archivo: «models/metricas.json: a › b; c › d» se lee mejor que repetir el archivo.
function porArchivo(fuentes) {
  const grupos = new Map()
  for (const f of fuentes) {
    const [archivo, ...resto] = f.split(' › ')
    grupos.set(archivo, [...(grupos.get(archivo) ?? []), resto.join(' › ')])
  }
  return [...grupos]
}

function Fuente({ de }) {
  const grupos = porArchivo(Array.isArray(de) ? de : [de])
  return (
    <p className="fuente">
      Fuente:{' '}
      {grupos.map(([archivo, rutas], i) => (
        <span key={archivo}>
          {i > 0 && '; '}
          <code>{archivo}</code>: {rutas.map((r, j) => (
            <span key={r}>
              {j > 0 && '; '}
              <code>{r}</code>
            </span>
          ))}
        </span>
      ))}
    </p>
  )
}

function Veredicto({ valor, textos = VEREDICTOS }) {
  return <span className={`veredicto veredicto-${valor}`}>{textos[valor]}</span>
}

function lecturaDelIntervalo([desde, hasta]) {
  if (hasta.valor < 0) return 'Empeora poco, pero de forma consistente: el intervalo no cruza el cero.'
  if (desde.valor > 0) return 'Mejora poco, pero de forma consistente: el intervalo no cruza el cero.'
  return 'El intervalo cruza el cero: no hay una diferencia clara.'
}

function Comparacion({ fila, textos }) {
  return (
    <li className="evidencia-fila">
      <div>
        <h3>{fila.tecnica}</h3>
        <p className="suave">
          {fila.metrica}
          {typeof fila.mejor === 'object'
            ? `, lo ideal es ${formatear(fila.formato, fila.mejor.objetivo)}`
            : fila.mejor === 'mayor'
              ? ', más alto es mejor'
              : ', más bajo es mejor'}
        </p>
      </div>
      <dl className="evidencia-par">
        <div>
          <dt>{fila.lucas.nombre}</dt>
          <dd className="cifra">{formatear(fila.formato, fila.lucas.valor)}</dd>
        </div>
        <div>
          <dt>{fila.base.nombre}</dt>
          <dd className="cifra">{formatear(fila.formato, fila.base.valor)}</dd>
        </div>
      </dl>
      <p>
        <Veredicto valor={fila.veredicto} textos={textos} />
        {fila.n && <span className="suave">, n = {formatear('entero', fila.n.valor)}</span>}
      </p>
      {fila.diferencia && (
        <p className="suave">
          {fila.diferencia.nombre}: {formatear('decimal5', fila.diferencia.media.valor)}, intervalo del 95 % de{' '}
          {formatear('decimal5', fila.diferencia.intervalo[0].valor)} a {formatear('decimal5', fila.diferencia.intervalo[1].valor)}.{' '}
          {lecturaDelIntervalo(fila.diferencia.intervalo)}
        </p>
      )}
      {fila.sinFrases && (
        <p className="suave">
          Un pedido cuenta como rechazado solo si va a la ruta correcta y la respuesta no trae frases prohibidas. Las
          respuestas de {fila.lucas.nombre} sin frases prohibidas fueron el {formatear('pct', fila.sinFrases.valor)}: lo que
          falla es la ruta.
        </p>
      )}
      {fila.nota && <p className="suave">{fila.nota}</p>}
      <Fuente
        de={[
          fila.lucas.fuente,
          fila.base.fuente,
          ...(fila.n ? [fila.n.fuente] : []),
          ...(fila.sinFrases ? [fila.sinFrases.fuente] : []),
          ...(fila.diferencia ? [fila.diferencia.media.fuente.replace(/ › media$/, ' › media e ic95')] : []),
        ]}
      />
    </li>
  )
}

function Impacto() {
  const { meses, filas } = impactoPorCliente()
  const tabla = estrategias()
  const lucas = tabla.find((e) => e.id === 'lucas')
  const masColchon = tabla.reduce((a, b) => (b.colchon.valor > a.colchon.valor ? b : a))
  const menosRojo = tabla.reduce((a, b) => (b.diasRojo.valor < a.diasRojo.valor ? b : a))
  const masRojo = tabla.reduce((a, b) => (b.diasRojo.valor > a.diasRojo.valor ? b : a))
  const diasAlerta = supuestosImpacto().find((s) => s.clave === 'dias_de_alerta')
  const valor = valorBanco()

  return (
    <section className="evidencia-seccion" aria-labelledby="impacto-titulo">
      <h2 id="impacto-titulo">Impacto en S/ por cliente</h2>
      <p className="suave">
        Lucas frente a no hacer nada, repetido sobre {formatear('entero', meses.valor)} meses de movimientos de prueba,
        con intervalo del 95 % por bootstrap de clientes.
      </p>
      <ul className="lista-limpia evidencia-impacto">
        {filas.map((f) => (
          <li key={f.id} className="tarjeta">
            <h3>{f.nombre}</h3>
            <p className="evidencia-cifra">{formatear(f.formato, f.valor.valor)}</p>
            <p className="suave">
              Intervalo del 95 %: de {formatear(f.formato, f.intervalo[0].valor)} a{' '}
              {formatear(f.formato, f.intervalo[1].valor)}
            </p>
            <Fuente de={f.valor.fuente.replace(/ › media$/, ' › media e ic95')} />
          </li>
        ))}
      </ul>

      <div className="evidencia-dos">
        <div className="tarjeta">
          <h3>Frente a las otras estrategias</h3>
          <table className="evidencia-tabla">
            <thead>
              <tr>
                <th scope="col">Estrategia</th>
                <th scope="col">Días en rojo al mes</th>
                <th scope="col">Colchón final</th>
              </tr>
            </thead>
            <tbody>
              {tabla.map((e) => (
                <tr key={e.id} className={e.id === 'lucas' ? 'evidencia-tabla-lucas' : undefined}>
                  <th scope="row">{e.nombre}</th>
                  <td>{formatear('decimal', e.diasRojo.valor)}</td>
                  <td>{formatear('soles', e.colchon.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            {menosRojo.id === 'lucas' ? 'Lucas es la estrategia con menos días en rojo.' : `${menosRojo.nombre} tiene menos días en rojo que Lucas.`}
            {masColchon.id !== 'lucas' &&
              ` ${masColchon.nombre} junta más colchón (${formatear('soles', masColchon.colchon.valor)} frente a ${formatear('soles', lucas.colchon.valor)} de Lucas).`}
            {masRojo.id !== 'nada' &&
              ` ${masRojo.nombre} es la que más días en rojo deja (${formatear('decimal', masRojo.diasRojo.valor)} al mes): aparta aunque el saldo no alcance.`}
          </p>
          <Fuente de="models/metricas_impacto.json › tabla › (estrategia) › dias_en_rojo_por_cliente_mes y colchon_final_soles" />
        </div>

        <div className="tarjeta">
          <h3>Supuestos de la simulación</h3>
          <ul className="lista-limpia evidencia-supuestos">
            {supuestosImpacto().map((s) => (
              <li key={s.nombre}>
                {s.nombre}: <span className="cifra">{formatear(s.formato, s.valor.valor)}</span>
              </li>
            ))}
          </ul>
          {diasAlerta.valor.valor !== DIAS_PARA_AVISAR && (
            <p>
              Ojo: esta simulación avisa con {formatear('entero', diasAlerta.valor.valor)} días de anticipación y la app avisa a{' '}
              {DIAS_PARA_AVISAR} días o menos. Falta alinear las dos reglas.
            </p>
          )}
          <Fuente de="models/metricas_impacto.json › supuestos" />
          <h3>Para el banco, en el escenario conservador</h3>
          <p>
            Solo cuenta el margen de {formatear('pct', valor.margen.valor)} sobre lo que el cliente aparta. Si el consumo no
            sube, el programa de puntos {valor.netoPorUsuario.valor < 0 ? 'cuesta' : 'deja'}{' '}
            <span className="cifra">{formatear('soles-centimos', Math.abs(valor.netoPorUsuario.valor))}</span> por usuario al
            año; se paga solo si el consumo sube {formatear('pct', valor.consumoParaPagarse.valor)}.
          </p>
          <p className="suave">
            Retención, mora evitada y venta cruzada idónea no se valoran: hace falta un piloto con grupo de control.
          </p>
          <Fuente de={[valor.margen.fuente, valor.netoPorUsuario.fuente, valor.consumoParaPagarse.fuente]} />
        </div>
      </div>
    </section>
  )
}

function Agente() {
  const { nLlm, nPlantillas, filas, filtro } = agente()
  return (
    <section className="evidencia-seccion" aria-labelledby="agente-titulo">
      <h2 id="agente-titulo">Agente y RAG</h2>
      <p className="suave">
        El baseline del agente es responder solo con plantillas ({formatear('entero', nPlantillas.valor)} preguntas). Gemini con
        juez se midió en un subconjunto de {formatear('entero', nLlm.valor)}.
      </p>
      <ul className="lista-limpia evidencia-grilla">
        {filas.map((f) => (
          <Comparacion key={f.id} fila={{ ...f, tecnica: f.metrica, metrica: 'Agente único' }} />
        ))}
        <li className="evidencia-fila">
          <h3>Filtro de relevancia del RAG</h3>
          <p>
            Acepta el <span className="cifra">{formatear('pct', filtro.aceptadas.valor)}</span> de las{' '}
            {formatear('entero', filtro.nCon.valor)} preguntas con respuesta y rechaza el{' '}
            <span className="cifra">{formatear('pct', filtro.rechazadas.valor)}</span> de las{' '}
            {formatear('entero', filtro.nFuera.valor)} que no están en los documentos.
          </p>
          <Fuente de={[filtro.aceptadas.fuente, filtro.rechazadas.fuente]} />
        </li>
      </ul>
    </section>
  )
}

function Perturbaciones() {
  const { pruebas, eventoNoVisto, conTexto, equidad } = perturbaciones()
  return (
    <section className="evidencia-seccion" aria-labelledby="perturbaciones-titulo">
      <h2 id="perturbaciones-titulo">Lo que empeora y lo que aguanta</h2>
      <p className="suave">
        Pronóstico de saldo a 30 días con datos alterados frente al mismo modelo sin alterar, y su error en subgrupos frente
        al de todos.
      </p>
      <ul className="lista-limpia evidencia-grilla">
        {pruebas.map((f) => (
          <Comparacion
            key={f.id}
            fila={f.subgrupo ? { ...f, metrica: 'Error medio (MAE) del subgrupo' } : f}
            textos={f.subgrupo ? SUBGRUPO : CAMBIO}
          />
        ))}
        <Comparacion fila={eventoNoVisto} />
        <Comparacion fila={conTexto} textos={CAMBIO} />
      </ul>
      {equidad.length > 0 && (
        <div className="tarjeta">
          <h3>Alertas de equidad</h3>
          <ul className="evidencia-supuestos">
            {equidad.map((e) => (
              <li key={e.grupo}>
                {GRUPOS[e.grupo] ?? e.grupo}: el error del grupo «{e.peor}» es{' '}
                <span className="cifra">{formatear('decimal', e.razon.valor)} veces</span> el del grupo con menos error.
              </li>
            ))}
          </ul>
          <Fuente de="models/metricas.json › pronostico › equidad_por_grupo › (grupo) › brechas" />
        </div>
      )}
    </section>
  )
}

function Resumen() {
  const lista = tecnicas()
  const ganan = lista.filter((f) => f.veredicto === 'mejor').length
  const pierden = lista.filter((f) => f.veredicto === 'peor')
  const [dias, colchon] = impactoPorCliente().filas
  return (
    <section className="tarjeta evidencia-resumen" aria-label="Resumen">
      <p>
        <strong>
          {ganan} de {lista.length} técnicas
        </strong>{' '}
        le ganan a su baseline
        {pierden.length > 0 && `; ${pierden.map((f) => f.tecnica.toLowerCase()).join(' y ')} sale peor`}. Por cliente, Lucas
        evita <strong>{formatear(dias.formato, dias.valor.valor)} días en rojo al mes</strong> y suma{' '}
        <strong>{formatear(colchon.formato, colchon.valor.valor)} de colchón</strong> frente a no hacer nada.
      </p>
    </section>
  )
}

export default function Evidencia() {
  const porSegundo = cifra('escala', 'recomendaciones_por_segundo')
  const memoria = cifra('escala', 'pico_memoria_gb')
  const clientes = cifra('escala', 'clientes')
  return (
    <div className="evidencia">
      <header className="evidencia-cabecera">
        <Link to="/ingresar" className="volver">
          <CaretLeft size={20} aria-hidden="true" />
          Volver a la demo
        </Link>
        <h1>Evidencia de Lucas</h1>
        <p>
          Resultados de <code>make eval</code> con datos sintéticos de semilla fija. Cada cifra se lee de{' '}
          <code>models/metricas*.json</code> y muestra su fuente; ninguna está escrita a mano.
        </p>
      </header>

      <main className="evidencia-contenido">
        <Resumen />
        <Impacto />
        <section className="evidencia-seccion" aria-labelledby="tecnicas-titulo">
          <h2 id="tecnicas-titulo">Cada técnica frente a su baseline</h2>
          <p className="suave">
            Valores en el conjunto de prueba. Los archivos no traen intervalo para estas métricas; solo lo traen el impacto
            en S/ y el efecto del texto en el pronóstico. «Casi igual» es menos de {formatear('pct', MARGEN_PARECIDO)} de
            diferencia, un criterio de este panel.
          </p>
          <ul className="lista-limpia evidencia-grilla">
            {tecnicas().map((f) => (
              <Comparacion key={f.id} fila={f} />
            ))}
          </ul>
        </section>
        <Agente />
        <Perturbaciones />
        <p className="suave">
          Escala medida con {formatear('entero', clientes.valor)} clientes: {formatear('entero', porSegundo.valor)}{' '}
          recomendaciones por segundo y {formatear('decimal', memoria.valor)} GB de memoria como máximo.
        </p>
        <Fuente de={[porSegundo.fuente, memoria.fuente]} />
      </main>
    </div>
  )
}
