import { BrowserRouter as Router, Route, Routes, Navigate,  } from 'react-router-dom'
import './App.css'
import { Login } from "./pages/login"
import { Home } from "./pages/home"
import { OrgImpacts } from "./pages/org_impacts"
import { Dashboard } from "./pages/dashboard"

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/home" element={<Home />} />
        <Route path="/org/:orgName" element={<OrgImpacts />} />
        <Route path="*" element={<Navigate to="/" replace/>} />
      </Routes>
    </Router>
  )
}

export default App
