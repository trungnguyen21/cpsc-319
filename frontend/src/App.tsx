import { BrowserRouter as Router, Route, Routes, Navigate,  } from 'react-router-dom'
import './App.css'
import { Login } from "./pages/login"
//import { Home } from "./pages/Home"

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="*" element={<Navigate to="/" replace/>} />
      </Routes>
    </Router>
  )
}

export default App
