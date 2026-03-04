import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "./pages/LoginPage";
import PainelPage from "./pages/PainelPage";
import ConsultaPage from "./pages/ConsultaPage";

// ─── Error Boundary — catches white-screen crashes and shows them visually ────
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null };
  static getDerivedStateFromError(e: Error) { return { error: e }; }
  render() {
    if (this.state.error) {
      const err = this.state.error as Error;
      return (
        <div style={{
          minHeight: "100vh", background: "#1a1a1a", display: "flex",
          alignItems: "center", justifyContent: "center", padding: "2rem"
        }}>
          <div style={{
            background: "#2a0000", border: "2px solid #ef4444", borderRadius: "12px",
            padding: "2rem", maxWidth: "640px", width: "100%"
          }}>
            <h2 style={{ color: "#ef4444", marginBottom: "1rem" }}>⚠ Erro de Renderização</h2>
            <pre style={{ color: "#fca5a5", fontSize: "12px", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {err.message}
              {"\n\n"}
              {err.stack}
            </pre>
            <button
              onClick={() => { this.setState({ error: null }); window.location.href = "/painel"; }}
              style={{
                marginTop: "1.5rem", background: "#ef4444", color: "white", border: "none",
                borderRadius: "8px", padding: "8px 20px", cursor: "pointer", fontWeight: "bold"
              }}
            >
              Voltar ao Painel
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/painel" element={<PainelPage />} />
          <Route path="/consulta" element={<ConsultaPage />} />
          <Route path="/" element={<Navigate to="/painel" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

