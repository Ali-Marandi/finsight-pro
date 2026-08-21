import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from '../renderer/components/Layout';
import Dashboard from '../renderer/pages/Dashboard';
import Analysis from '../renderer/pages/Analysis';
import Reports from '../renderer/pages/Reports';
import History from '../renderer/pages/History';
import Settings from '../renderer/pages/Settings';

export default function App() {
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
