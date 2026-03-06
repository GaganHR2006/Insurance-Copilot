import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import PolicyUpload from './pages/PolicyUpload';
import Chatbot from './pages/Chatbot';
import RiskDashboard from './pages/RiskDashboard';
import HospitalFinder from './pages/HospitalFinder';
import EligibilityChecker from './pages/EligibilityChecker';
import { useLocation } from 'react-router-dom';

const pageTitles = {
  '/upload':      'Upload Policy',
  '/chat':        'AI Assistant',
  '/risk':        'Risk Score',
  '/hospitals':   'Hospital Finder',
  '/eligibility': 'Eligibility Checker',
};

function Layout() {
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? 'Insurance Copilot';

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main area */}
      <div className="flex flex-col flex-1 overflow-hidden gradient-bg">
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/"            element={<Navigate to="/upload" replace />} />
            <Route path="/upload"      element={<PolicyUpload />} />
            <Route path="/chat"        element={<Chatbot />} />
            <Route path="/risk"        element={<RiskDashboard />} />
            <Route path="/hospitals"   element={<HospitalFinder />} />
            <Route path="/eligibility" element={<EligibilityChecker />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
