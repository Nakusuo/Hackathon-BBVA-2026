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
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
