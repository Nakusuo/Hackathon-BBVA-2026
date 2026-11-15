import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Consentimiento from './banca/Consentimiento.jsx'
import Ingreso from './banca/Ingreso.jsx'
import InicioBanca from './banca/InicioBanca.jsx'
import MarcoBanca from './banca/MarcoBanca.jsx'
import Preferencias from './banca/Preferencias.jsx'
import EspacioLucas from './lucas/EspacioLucas.jsx'

// Evidencia lleva los JSON de `make eval`: se carga solo si alguien abre esa pantalla.
const Evidencia = lazy(() => import('./evidencia/Evidencia.jsx'))

export default function App() {
  return (
    <Routes>
      <Route path="/ingresar" element={<Ingreso />} />
      <Route path="/consentimiento" element={<Consentimiento />} />
      <Route
        path="/evidencia"
        element={
          <Suspense fallback={null}>
            <Evidencia />
          </Suspense>
        }
      />
      <Route element={<MarcoBanca />}>
        <Route path="/banca" element={<InicioBanca />} />
        <Route path="/preferencias" element={<Preferencias />} />
        <Route path="/lucas" element={<Navigate to="/lucas/resumen" replace />} />
        <Route path="/lucas/:seccion" element={<EspacioLucas />} />
      </Route>
      <Route path="*" element={<Navigate to="/ingresar" replace />} />
    </Routes>
  )
}
