import { Navigate, Route, Routes } from 'react-router-dom'
import Ingreso from './banca/Ingreso.jsx'
import InicioBanca from './banca/InicioBanca.jsx'
import MarcoBanca from './banca/MarcoBanca.jsx'
import EspacioLucas from './lucas/EspacioLucas.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/ingresar" element={<Ingreso />} />
      <Route element={<MarcoBanca />}>
        <Route path="/banca" element={<InicioBanca />} />
        <Route path="/lucas" element={<Navigate to="/lucas/resumen" replace />} />
        <Route path="/lucas/:seccion" element={<EspacioLucas />} />
      </Route>
      <Route path="*" element={<Navigate to="/ingresar" replace />} />
    </Routes>
  )
}
