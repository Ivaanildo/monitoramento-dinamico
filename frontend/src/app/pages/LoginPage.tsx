import React, { useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../services/api";
import { RadarIcon } from "../components/RadarIcon";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
                credentials: "include",
            });

            if (!res.ok) {
                throw new Error("Credenciais inválidas");
            }

            navigate("/painel");
        } catch (err: any) {
            setError(err.message || "Erro ao fazer login");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#2d2d2d" }}>
            <div className="w-full max-w-md p-8 rounded-xl" style={{ background: "#1e1e1e", border: "2px solid #FFD700" }}>

                <div className="flex flex-col items-center mb-8 gap-3">
                    <RadarIcon size={64} />
                    <h1 className="text-3xl font-black text-center" style={{ color: "#FFD700" }}>
                        Monitoramento de Vias
                    </h1>
                    <p className="text-gray-400 text-sm">Entre com suas credenciais de operação</p>
                </div>

                <form onSubmit={handleLogin} className="flex flex-col gap-5">
                    {error && (
                        <div className="p-3 rounded text-sm text-center font-medium" style={{ background: "#ef444420", color: "#fca5a5", border: "1px solid #ef4444" }}>
                            {error}
                        </div>
                    )}

                    <div className="flex flex-col gap-1">
                        <label className="text-sm font-medium" style={{ color: "#d1d5db" }}>Usuário</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="p-3 rounded border outline-none text-white focus:border-yellow-400"
                            style={{ background: "#111", borderColor: "#333" }}
                            required
                        />
                    </div>

                    <div className="flex flex-col gap-1">
                        <label className="text-sm font-medium" style={{ color: "#d1d5db" }}>Senha</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="p-3 rounded border outline-none text-white focus:border-yellow-400"
                            style={{ background: "#111", borderColor: "#333" }}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="p-3 rounded font-bold transition-all disabled:opacity-50 hover:opacity-90 mt-2"
                        style={{ background: "#FFD700", color: "#111" }}
                    >
                        {loading ? "Entrando..." : "Entrar"}
                    </button>
                </form>

                <div className="mt-8 flex justify-center">
                    <div className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-white">
                        <img src="/logo-brk.png" alt="BRK" className="h-9 w-auto object-contain" style={{ maxWidth: 140 }} />
                    </div>
                </div>
            </div>
        </div>
    );
}
