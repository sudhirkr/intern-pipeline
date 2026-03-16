import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './components/Toast';
import ApplyPage from './components/ApplyPage';
import ApplicationView from './components/ApplicationView';
import LoginPage from './components/LoginPage';
import AdminDashboard from './components/AdminDashboard';
import AssignmentManager from './components/AssignmentManager';
import ProjectSheet from './components/ProjectSheet';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/apply" replace />} />
          <Route path="/apply" element={<ApplyPage />} />
          <Route path="/application/:token" element={<ApplicationView />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/assignments" element={<AssignmentManager />} />
          <Route path="/admin/projects" element={<ProjectSheet />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
