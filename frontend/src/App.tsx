import { BrowserRouter as Router, Route, Routes, Navigate,  } from 'react-router-dom'
import './App.css'
import { Login } from "./pages/login"
import { Home } from "./pages/home"
import { OrgImpacts } from "./pages/org_impacts"
import ProtectedRoute from "./components/protected_route"

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/org/:orgName" element={<OrgImpacts />} />
        <Route path="*" element={<Navigate to="/" replace/>} />
      </Routes>
    </Router>
  )
}

export default App
