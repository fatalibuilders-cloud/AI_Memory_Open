import React from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  return (
    <div style={{padding:20}}>
      <h1>MIT-FATALI — Frontend (PWA) Starter</h1>
      <p>Frontend runs at /apps/frontend. Connect to the backend API at /api.</p>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
