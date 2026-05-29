import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import AuditPage from './pages/AuditPage';
import FlagsPage from './pages/FlagsPage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/flags" element={<FlagsPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
