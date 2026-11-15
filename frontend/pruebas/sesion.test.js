import assert from 'node:assert/strict'
import { beforeEach, test } from 'node:test'

// Almacenamiento en memoria: en Node no hay navegador.
const datos = new Map()
globalThis.window = {
  localStorage: {
    getItem: (k) => (datos.has(k) ? datos.get(k) : null),
    setItem: (k, v) => datos.set(k, String(v)),
    removeItem: (k) => datos.delete(k),
  },
}
const { CLAVE_TIPS, darPermiso, guardarPersona, permisoDe, personaGuardada, retirarPermiso } = await import(
  '../src/sesion.js'
)

beforeEach(() => datos.clear())

test('sin elección válida guardada entra la persona de la demo', () => {
  assert.equal(personaGuardada(), 'independiente')
  datos.set('lucas-persona', 'inventada')
  assert.equal(personaGuardada(), 'independiente')
})

test('el permiso es de cada persona: el del independiente no vale para el formal', () => {
  darPermiso('independiente', '2026-11-14')
  assert.equal(permisoDe('independiente'), '2026-11-14')
  assert.equal(permisoDe('formal'), null)
})

test('retirar el permiso apaga Lucas para esa persona y borra sus tips, sin tocar a la otra', () => {
  darPermiso('independiente', '2026-11-14')
  darPermiso('formal', '2026-11-14')
  datos.set(CLAVE_TIPS, '["musika"]')
  retirarPermiso('independiente')
  assert.equal(permisoDe('independiente'), null)
  assert.equal(permisoDe('formal'), '2026-11-14')
  assert.equal(datos.has(CLAVE_TIPS), false)
})

test('cambiar de persona descarta los tips elegidos; guardar la misma, no', () => {
  datos.set(CLAVE_TIPS, '["musika"]')
  guardarPersona('independiente')
  assert.equal(datos.get(CLAVE_TIPS), '["musika"]')
  guardarPersona('formal')
  assert.equal(personaGuardada(), 'formal')
  assert.equal(datos.has(CLAVE_TIPS), false)
})

test('un permiso guardado roto no rompe la app', () => {
  datos.set('lucas-consentimiento', '{roto')
  assert.equal(permisoDe('independiente'), null)
})
