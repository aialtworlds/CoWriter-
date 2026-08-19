import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { WalletProvider } from "@/contexts/WalletContext";
import { Header } from "@/components/Header";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Toaster } from "@/components/ui/sonner";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import Dashboard from "@/pages/Dashboard";
import ProjectDetail from "@/pages/ProjectDetail";
import ChapterNew from "@/pages/ChapterNew";
import ChapterAnalyze from "@/pages/ChapterAnalyze";
import ChapterResult from "@/pages/ChapterResult";
import CreditStatement from "@/pages/CreditStatement";
import RulesPage from "@/pages/RulesPage";
import BuyCredits from "@/pages/BuyCredits";
import PaymentSuccess from "@/pages/PaymentSuccess";
import PaymentCancel from "@/pages/PaymentCancel";

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#0C0C0E] text-[#E6E4DD]">
      <Header />
      {children}
    </div>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <WalletProvider>
            <Toaster />
            <Routes>
              <Route path="/" element={<Login />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <AppLayout><Dashboard /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId"
                element={
                  <ProtectedRoute>
                    <AppLayout><ProjectDetail /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/chapters/new"
                element={
                  <ProtectedRoute>
                    <AppLayout><ChapterNew /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chapters/:chapterId"
                element={
                  <ProtectedRoute>
                    <AppLayout><ChapterAnalyze /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analysis/:analysisRunId"
                element={
                  <ProtectedRoute>
                    <AppLayout><ChapterResult /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/credits"
                element={
                  <ProtectedRoute>
                    <AppLayout><CreditStatement /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/rules"
                element={
                  <ProtectedRoute>
                    <AppLayout><RulesPage /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/comprar-creditos"
                element={
                  <ProtectedRoute>
                    <AppLayout><BuyCredits /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/pagamento/sucesso"
                element={
                  <ProtectedRoute>
                    <AppLayout><PaymentSuccess /></AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/pagamento/cancelado"
                element={
                  <ProtectedRoute>
                    <AppLayout><PaymentCancel /></AppLayout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </WalletProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
