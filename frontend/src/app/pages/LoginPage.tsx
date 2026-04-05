import React, { useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, Clock3, Radar, Route, ShieldCheck } from "lucide-react";
import { RadarIcon } from "../components/RadarIcon";

const heroMetrics = [
  { label: "Rotas monitoradas", value: "20" },
  { label: "Cobertura atual", value: "22,3 mil km" },
  { label: "Atualizacao", value: "a cada 1h" },
];

const workflowItems = [
  {
    icon: Radar,
    title: "Leitura consolidada",
    description: "Google Routes, HERE Traffic e historico salvo no mesmo cockpit operacional.",
  },
  {
    icon: Route,
    title: "Consulta detalhada",
    description: "Mapa, incidentes, atraso, velocidade e exportacao imediata por rota.",
  },
  {
    icon: ShieldCheck,
    title: "Contexto reutilizavel",
    description: "Painel corporativo com classificacao consistente para operacao e gestao.",
  },
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Credenciais invalidas");
      }

      navigate("/painel");
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-4 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl overflow-hidden rounded-[32px] border border-white/70 bg-white/45 shadow-[0_30px_90px_rgba(15,23,42,0.12)] backdrop-blur-2xl lg:grid-cols-[1.15fr_0.85fr]">
        <section className="relative overflow-hidden px-6 py-8 sm:px-10 lg:px-12">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(15,23,42,0.12),_transparent_34%)]" />
          <div className="relative flex h-full flex-col justify-between gap-10">
            <div className="space-y-8">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-600">
                <Clock3 className="h-3.5 w-3.5 text-amber-600" />
                Centro de monitoramento viario
              </div>

              <div className="space-y-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-950 text-white shadow-[0_20px_45px_rgba(15,23,42,0.18)]">
                    <RadarIcon size={40} />
                  </div>
                  <div>
                    <p className="eyebrow-label">Monitoramento Dinamico</p>
                    <p className="text-sm text-slate-500">Painel operacional para leitura, priorizacao e consulta de rotas.</p>
                  </div>
                </div>

                <div className="max-w-2xl space-y-4">
                  <h1 className="text-4xl font-black tracking-[-0.04em] text-slate-950 sm:text-5xl lg:text-6xl">
                    A mesma rota pode virar operacao, risco ou decisao em poucos minutos.
                  </h1>
                  <p className="max-w-xl text-base leading-7 text-slate-600 sm:text-lg">
                    Entre no cockpit corporativo para acompanhar o status viario, conferir incidentes e abrir consultas profundas sem sair do fluxo operacional.
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {heroMetrics.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-3xl border border-white/80 bg-white/78 px-5 py-4 shadow-[0_18px_32px_rgba(15,23,42,0.08)]"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{item.label}</p>
                    <p className="mt-3 text-2xl font-black tracking-[-0.04em] text-slate-950">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              {workflowItems.map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.title}
                    className="rounded-[28px] border border-white/75 bg-white/82 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)]"
                  >
                    <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="text-lg font-semibold tracking-[-0.02em] text-slate-900">{item.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <aside className="relative border-t border-white/60 bg-slate-950 px-6 py-8 text-white sm:px-8 lg:border-l lg:border-t-0 lg:px-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.22),_transparent_24%),linear-gradient(180deg,_rgba(15,23,42,0.08),_rgba(15,23,42,0.88))]" />
          <div className="relative flex h-full flex-col justify-between gap-8">
            <div className="space-y-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-amber-300">Acesso protegido</p>
                  <h2 className="mt-2 text-3xl font-black tracking-[-0.04em] text-white">Entrar na operacao</h2>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/8 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.16em] text-emerald-300">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  Ambiente ativo
                </div>
              </div>

              <p className="max-w-md text-sm leading-6 text-slate-300">
                Use suas credenciais de operacao para abrir o painel, revisar a situacao das rotas e iniciar consultas detalhadas.
              </p>

              <form onSubmit={handleLogin} className="space-y-5 rounded-[30px] border border-white/10 bg-white/6 p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur">
                {error && (
                  <div className="rounded-2xl border border-rose-400/35 bg-rose-500/10 px-4 py-3 text-sm font-medium text-rose-200">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-200">Usuario</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-amber-400/80 focus:ring-2 focus:ring-amber-400/20"
                    placeholder="Seu usuario de operacao"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-200">Senha</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-amber-400/80 focus:ring-2 focus:ring-amber-400/20"
                    placeholder="Sua senha"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  {loading ? "Entrando..." : "Acessar painel"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              </form>
            </div>

            <div className="rounded-[30px] border border-white/10 bg-white/6 p-5 backdrop-blur">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Operacao conectada</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    Painel corporativo com coleta automatizada, historico salvo e exportacao pronta para gestao.
                  </p>
                </div>
                <div className="inline-flex items-center justify-center rounded-2xl bg-white px-4 py-3 shadow-[0_18px_32px_rgba(15,23,42,0.18)]">
                  <img
                    src="/logo-brk.png"
                    alt="BRK"
                    className="h-9 w-auto object-contain"
                    style={{ maxWidth: 132 }}
                  />
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
