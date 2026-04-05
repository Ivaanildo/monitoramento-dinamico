import React, { useState } from "react";
import { ArrowLeft, ArrowRight, Clock3, MapPinned, ShieldCheck, TriangleAlert } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";

interface IncidenteCard {
  categoria?: string;
  descricao?: string;
  severidade?: string;
  severidade_codigo?: string;
  rodovia_afetada?: string;
  road_closed?: boolean;
}

export interface RouteCardProps {
  id: string | number;
  via: string;
  nome: string;
  trecho: string;
  ocorrencia: string;
  status: "Normal" | "Moderado" | "Intenso" | "Parado" | "Erro" | "N/A";
  relato: string;
  hora: string;
  atraso_min?: number;
  confianca_pct?: number;
  incidentes?: IncidenteCard[];
  duracao_normal_min?: number;
  duracao_transito_min?: number;
  jam_factor_max?: number;
  onVerObs?: (id: string | number) => void;
}

const STATUS_THEME = {
  Normal: {
    accent: "#16a34a",
    ring: "rgba(22, 163, 74, 0.16)",
    surface: "#ecfdf5",
    text: "#166534",
    label: "Fluxo controlado",
  },
  Moderado: {
    accent: "#ea580c",
    ring: "rgba(234, 88, 12, 0.18)",
    surface: "#fff7ed",
    text: "#9a3412",
    label: "Atencao operacional",
  },
  Intenso: {
    accent: "#dc2626",
    ring: "rgba(220, 38, 38, 0.18)",
    surface: "#fef2f2",
    text: "#991b1b",
    label: "Prioridade imediata",
  },
  Parado: {
    accent: "#7c3aed",
    ring: "rgba(124, 58, 237, 0.2)",
    surface: "#f5f3ff",
    text: "#5b21b6",
    label: "Interrupcao critica",
  },
  Erro: {
    accent: "#334155",
    ring: "rgba(51, 65, 85, 0.16)",
    surface: "#f8fafc",
    text: "#334155",
    label: "Leitura indisponivel",
  },
  "N/A": {
    accent: "#64748b",
    ring: "rgba(100, 116, 139, 0.16)",
    surface: "#f8fafc",
    text: "#475569",
    label: "Sem telemetria",
  },
} as const;

const severityDot = (severity?: string) => {
  if (severity === "critical") return "#dc2626";
  if (severity === "major") return "#f97316";
  return "#eab308";
};

export function RouteCard(props: RouteCardProps) {
  const {
    id,
    via,
    nome,
    trecho,
    status,
    ocorrencia,
    relato,
    hora,
    atraso_min = 0,
    confianca_pct = 0,
    onVerObs,
    incidentes = [],
    duracao_normal_min = 0,
    duracao_transito_min = 0,
    jam_factor_max = 0,
  } = props;

  const [isFlipped, setIsFlipped] = useState(false);
  const theme = STATUS_THEME[status] || STATUS_THEME.Normal;
  const hasOccurrence = Boolean(ocorrencia);
  const routeLabel = nome || via || "Rota monitorada";

  return (
    <div
      className="surface-panel relative flex min-h-[300px] flex-1 overflow-hidden rounded-[30px] p-5"
      style={{ boxShadow: `0 22px 45px ${theme.ring}` }}
    >
      <div
        className="absolute inset-x-0 top-0 h-1.5"
        style={{ background: `linear-gradient(90deg, ${theme.accent}, rgba(255,255,255,0))` }}
      />

      <AnimatePresence mode="wait">
        {!isFlipped ? (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -14 }}
            transition={{ duration: 0.18 }}
            className="flex h-full w-full flex-col"
          >
            <div className="mb-5 flex items-start justify-between gap-4">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em]" style={{ background: theme.surface, color: theme.text }}>
                  <span className="h-2 w-2 rounded-full" style={{ background: theme.accent }} />
                  {via || "Via monitorada"}
                </div>
                <div>
                  <h3 className="text-xl font-black tracking-[-0.03em] text-slate-950">{routeLabel}</h3>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{trecho}</p>
                </div>
              </div>

              <div className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-right shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Status</p>
                <p className="mt-1 text-sm font-bold" style={{ color: theme.text }}>
                  {status}
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-3xl border border-slate-200/80 bg-slate-50/85 p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Atraso atual</p>
                <p className="mt-3 text-3xl font-black tracking-[-0.05em] text-slate-950">
                  {atraso_min > 0 ? `+${atraso_min}` : "0"}
                  <span className="ml-1 text-sm font-semibold tracking-normal text-slate-500">min</span>
                </p>
                <p className="mt-2 text-xs text-slate-500">{theme.label}</p>
              </div>

              <div className="rounded-3xl border border-slate-200/80 bg-slate-50/85 p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Confianca do ciclo</p>
                <p className="mt-3 text-3xl font-black tracking-[-0.05em] text-slate-950">
                  {Math.round(confianca_pct)}
                  <span className="ml-1 text-sm font-semibold tracking-normal text-slate-500">%</span>
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  {jam_factor_max > 0 ? `Jam factor max ${jam_factor_max.toFixed(1)}` : "Sem pico relevante neste recorte"}
                </p>
              </div>
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-3xl border border-slate-200/80 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Ocorrencia dominante</p>
                <p className="mt-3 text-sm font-semibold text-slate-900">
                  {hasOccurrence ? ocorrencia : "Nenhuma ocorrencia prioritaria nesta leitura"}
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  {relato ? relato.split("\n")[0] : "Use a visao detalhada para consultar mapa, incidentes e links externos da rota."}
                </p>
              </div>

              <div className="rounded-3xl border border-slate-200/80 bg-slate-50/85 p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Recorte operacional</p>
                <div className="mt-3 space-y-2 text-sm text-slate-600">
                  <div className="flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2">
                      <Clock3 className="h-4 w-4 text-amber-600" />
                      Atualizado
                    </span>
                    <span className="font-semibold text-slate-900">{hora || "--"}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2">
                      <TriangleAlert className="h-4 w-4 text-slate-400" />
                      Incidentes
                    </span>
                    <span className="font-semibold text-slate-900">{incidentes.length}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-slate-400" />
                      Duracao base
                    </span>
                    <span className="font-semibold text-slate-900">{duracao_normal_min || 0} min</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-auto flex items-center justify-between gap-3 pt-5">
              <button
                onClick={() => onVerObs && onVerObs(id)}
                className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <MapPinned className="h-4 w-4" />
                Abrir consulta
              </button>

              <button
                onClick={() => setIsFlipped(true)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
              >
                Ver detalhes
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="details"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -14 }}
            transition={{ duration: 0.18 }}
            className="flex h-full w-full flex-col"
          >
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow-label">Leitura detalhada</p>
                <h3 className="mt-2 text-xl font-black tracking-[-0.03em] text-slate-950">{routeLabel}</h3>
              </div>
              <div className="rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em]" style={{ background: theme.surface, color: theme.text }}>
                {status}
              </div>
            </div>

            <div className="mb-4 flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-600">
                Base {duracao_normal_min || 0} min
              </span>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-[11px] font-semibold text-amber-700">
                Atual {duracao_transito_min || 0} min
              </span>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-600">
                Jam {jam_factor_max > 0 ? jam_factor_max.toFixed(1) : "0.0"}
              </span>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-600">
                Confianca {Math.round(confianca_pct)}%
              </span>
            </div>

            <div className="rounded-[28px] border border-slate-200 bg-slate-50/85 p-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Relato operacional</p>
              <div className="mt-3 max-h-[116px] overflow-y-auto pr-1 text-sm leading-6 text-slate-600">
                {relato ? (
                  relato.split("\n").map((line, index) => (
                    <p key={`${id}-${index}`} className={index === 0 ? "font-semibold text-slate-900" : ""}>
                      {line}
                    </p>
                  ))
                ) : (
                  <p>Nenhuma observacao adicional foi registrada para esta rota.</p>
                )}
              </div>
            </div>

            <div className="mt-4 flex-1 rounded-[28px] border border-slate-200 bg-white p-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
                Incidentes relacionados ({incidentes.length})
              </p>

              <div className="mt-3 space-y-3">
                {incidentes.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-4 py-5 text-sm text-slate-500">
                    Nenhum incidente adicional foi associado ao trecho neste recorte.
                  </div>
                ) : (
                  incidentes.slice(0, 3).map((incidente, index) => (
                    <div key={`${id}-incidente-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
                      <div className="flex items-start gap-3">
                        <span
                          className="mt-1 h-2.5 w-2.5 rounded-full"
                          style={{ background: severityDot(incidente.severidade_codigo || incidente.severidade) }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold text-slate-900">{incidente.categoria || "Incidente viario"}</p>
                            {incidente.rodovia_afetada ? (
                              <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                                {incidente.rodovia_afetada}
                              </span>
                            ) : null}
                            {incidente.road_closed ? (
                              <span className="rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-rose-600">
                                Fechada
                              </span>
                            ) : null}
                          </div>
                          {incidente.descricao ? (
                            <p className="mt-1 text-xs leading-5 text-slate-500">{incidente.descricao}</p>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
              <button
                onClick={() => setIsFlipped(false)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
              >
                <ArrowLeft className="h-4 w-4" />
                Voltar
              </button>

              <button
                onClick={() => onVerObs && onVerObs(id)}
                className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <MapPinned className="h-4 w-4" />
                Abrir mapa
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
