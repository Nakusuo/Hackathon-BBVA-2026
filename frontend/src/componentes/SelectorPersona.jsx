import { PERSONAS, personaPorId } from '../motor/personas.js'

// Radios nativos con apariencia de selector: el teclado y el lector de pantalla los tratan como un solo grupo.
export default function SelectorPersona({ valor, alCambiar }) {
  const elegida = personaPorId(valor)
  return (
    <fieldset className="selector-persona">
      <legend>Persona de la demo</legend>
      <div className="selector selector-ancho">
        {PERSONAS.map((p) => (
          <label key={p.id} className="selector-opcion">
            <input
              type="radio"
              name="persona-demo"
              value={p.id}
              checked={valor === p.id}
              onChange={() => alCambiar(p.id)}
              aria-describedby="persona-descripcion"
            />
            <span>{p.nombre}</span>
          </label>
        ))}
      </div>
      <p id="persona-descripcion" className="suave">
        {elegida.descripcion}
      </p>
    </fieldset>
  )
}
