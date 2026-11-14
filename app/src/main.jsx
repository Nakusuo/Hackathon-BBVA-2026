import { MotionConfig } from 'motion/react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './estilos/tokens.css'
import './estilos/base.css'
import './estilos/piezas.css'
import './estilos/marco.css'
import './estilos/banca.css'
import './estilos/lucas.css'
import './estilos/panel.css'
import './estilos/chat.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* Quien pidió reducir movimiento en su sistema ve todo quieto, también las entradas de sección. */}
    <MotionConfig reducedMotion="user">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </MotionConfig>
  </StrictMode>,
)
