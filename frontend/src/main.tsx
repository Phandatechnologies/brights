import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { listenForInstallPrompt, registerServiceWorker } from './lib/install'
import { watchSystemTheme } from './lib/theme'

watchSystemTheme()
listenForInstallPrompt()
registerServiceWorker()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
