import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import TextToVoice from './pages/TextToVoice';
import MyVoices from './pages/MyVoices';
import Models from './pages/Models';
import History from './pages/History';
import Settings from './pages/Settings';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tts" element={<TextToVoice />} />
            <Route path="/voices" element={<MyVoices />} />
            <Route path="/models" element={<Models />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
