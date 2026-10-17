import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import './canon.css'
import About from './pages/About'
import Agents from './pages/Agents'
import Ask from './pages/Ask'
import Benchmark from './pages/Benchmark'
import Decision, { DecisionList } from './pages/Decision'
import Home from './pages/Home'
import Ingest from './pages/Ingest'
import { Bar } from './ui'

function NotFound() {
  return <main className="page"><h1 className="h1">Not on record.</h1><p style={{ marginTop: 12 }}><Link className="lnk" to="/">Go home</Link></p></main>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Bar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/decisions" element={<DecisionList />} />
        <Route path="/decisions/:id" element={<Decision />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/ingest" element={<Ingest />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/benchmark" element={<Benchmark />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
