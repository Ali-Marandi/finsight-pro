import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Reports from './pages/Reports';
import History from './pages/History';
import Settings from './pages/Settings';
import { useAnalysisStore } from './hooks/useAnalysisStore';

export default function App() {
  const { analyses } = useAnalysisStore();

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/analysis/:id" element={<Analysis />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
