import { BrowserRouter as Router, Route, Routes, Navigate,  } from 'react-router-dom'
import './App.css'
import { Login } from "./pages/login"
import { Home } from "./pages/home"
import { OrgImpacts } from "./pages/org_impacts"
import GeneratedStory from './pages/generated_story'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/org/:orgName" element={<OrgImpacts />} />
        <Route path="/org/:orgName/story" element={<GeneratedStory />} />
        <Route path="*" element={<Navigate to="/" replace/>} />
      </Routes>
    </Router>
  )
}

export default App
