import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import UploadsPage from "./pages/UploadsPage";
import ReconciliationPage from "./pages/ReconciliationPage";
import ReportsPage from "./pages/ReportsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/uploads" element={<UploadsPage />} />
        <Route path="/reconciliation" element={<ReconciliationPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
