import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";
import { AuthProvider } from "@/auth/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/auth/RequireAuth";

// Lazy imports for code splitting (avoids leaflet loading everywhere)
import { lazy, Suspense } from "react";

const MapPage = lazy(() => import("@/features/map/MapPage").then(m => ({ default: m.MapPage })));
const ReportFormPage = lazy(() => import("@/features/report/ReportFormPage").then(m => ({ default: m.ReportFormPage })));
const ForwardingsPage = lazy(() => import("@/features/forwardings/ForwardingsPage").then(m => ({ default: m.ForwardingsPage })));
const LoginPage = lazy(() => import("@/features/auth/LoginPage").then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/features/auth/RegisterPage").then(m => ({ default: m.RegisterPage })));

function LoadingFallback() {
  return (
    <div className="flex h-full items-center justify-center">
      <span className="text-neutral-500">Carregando...</span>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route
                path="/"
                element={
                  <Suspense fallback={<LoadingFallback />}>
                    <MapPage />
                  </Suspense>
                }
              />
              <Route path="/login" element={<Suspense fallback={<LoadingFallback />}><LoginPage /></Suspense>} />
              <Route path="/register" element={<Suspense fallback={<LoadingFallback />}><RegisterPage /></Suspense>} />
              <Route
                path="/report"
                element={
                  <RequireAuth>
                    <Suspense fallback={<LoadingFallback />}>
                      <ReportFormPage />
                    </Suspense>
                  </RequireAuth>
                }
              />
              <Route
                path="/agent"
                element={
                  <RequireAuth roles={["agent", "admin"]}>
                    <Suspense fallback={<LoadingFallback />}>
                      <ForwardingsPage />
                    </Suspense>
                  </RequireAuth>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
