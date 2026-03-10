import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import PolicyUpload from './pages/PolicyUpload';
import Chatbot from './pages/Chatbot';
import RiskDashboard from './pages/RiskDashboard';
import HospitalFinder from './pages/HospitalFinder';
import EligibilityChecker from './pages/EligibilityChecker';
import { useLocation } from 'react-router-dom';
import { UploadProvider } from './context/UploadContext';

const pageTitles = {
  '/upload': 'Upload Policy',
  '/chat': 'AI Assistant',
  '/risk': 'Risk Score',
  '/hospitals': 'Hospital Finder',
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
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<PolicyUpload />} />
            <Route path="/chat" element={<Chatbot />} />
            <Route path="/risk" element={<RiskDashboard />} />
            <Route path="/hospitals" element={<HospitalFinder />} />
            <Route path="/eligibility" element={<EligibilityChecker />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function DebugBar() {
  const raw = localStorage.getItem("ic_policy")
    || localStorage.getItem("insurance_copilot_policy")
    || localStorage.getItem("insurance_pdf_data")
    || localStorage.getItem("policy")
    || localStorage.getItem("uploadedPolicy")
    || localStorage.getItem("policyData");

  return (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0,
      background: "#1a2235", borderTop: "2px solid #00BFA5",
      padding: "6px 12px", fontSize: "11px",
      color: raw ? "#10B981" : "#EF4444",
      zIndex: 99999, display: "flex", gap: "16px"
    }}>
      <span>LocalStorage: {raw ? "✓ HAS DATA" : "✗ EMPTY"}</span>
      {raw && (() => {
        try {
          const parsed = JSON.parse(raw);
          return (
            <>
              <span>Insurer: {parsed?.insurer ?? "null"}</span>
              <span>Treatments: {parsed?.covered_treatments?.length ?? 0}</span>
              <span>Full text: {parsed?.full_text?.length ?? 0} chars</span>
            </>
          );
        } catch {
          return <span>✗ INVALID JSON</span>;
        }
      })()}
    </div>
  );
}

export default function App() {
  return (
    <UploadProvider>
      <BrowserRouter>
        <Layout />
        <DebugBar />
      </BrowserRouter>
    </UploadProvider>
  );
}
