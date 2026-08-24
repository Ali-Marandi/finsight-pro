import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from '../renderer/components/Toast';
import Layout from '../renderer/components/Layout';
import Dashboard from '../renderer/pages/Dashboard';
import Analysis from '../renderer/pages/Analysis';
import Reports from '../renderer/pages/Reports';
import History from '../renderer/pages/History';
import Settings from '../renderer/pages/Settings';
import AICopilot from '../renderer/pages/AICopilot';
import Prediction from '../renderer/pages/Prediction';
import DocumentIntelligence from '../renderer/pages/DocumentIntelligence';
import Benchmarking from '../renderer/pages/Benchmarking';
import Compliance from '../renderer/pages/Compliance';
import Consolidation from '../renderer/pages/Consolidation';
import TSETMC from '../renderer/pages/TSETMC';
import TimeSeries from '../renderer/pages/TimeSeries';
import FinancialEngineering from '../renderer/pages/FinancialEngineering';

export default function App() {
  return (
    <HashRouter>
      <ToastProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/analysis/:id" element={<Analysis />} />
            <Route path="/ai-copilot" element={<AICopilot />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/document-intelligence" element={<DocumentIntelligence />} />
            <Route path="/benchmarking" element={<Benchmarking />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/consolidation" element={<Consolidation />} />
            <Route path="/tsetmc" element={<TSETMC />} />
            <Route path="/time-series" element={<TimeSeries />} />
            <Route path="/financial-engineering" element={<FinancialEngineering />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </ToastProvider>
    </HashRouter>
  );
}