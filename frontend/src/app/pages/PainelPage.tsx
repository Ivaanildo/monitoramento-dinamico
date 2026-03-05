import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { FilterDropdown } from "../components/FilterDropdown";
import { GaugeChart } from "../components/GaugeChart";
import { StatusTicker } from "../components/StatusTicker";
import { RadarIcon } from "../components/RadarIcon";
import { ArrowUpDown, ChevronUp, ChevronDown } from "lucide-react";

// ─── Mock Data ───────────────────────────────────────────────────────────────
interface Road {
  id: number;
  via: string;
  nome: string;
  trecho: string;
  status: "Normal" | "Moderado" | "Intenso" | "Parado" | "Erro" | "N/A";
  ocorrencia: string;
  relato: string;
  hora: string;
  atraso_min: number;
  confianca_pct: number;
}


// ─── Status helpers ───────────────────────────────────────────────────────────
const STATUS_COLOR = {
  Normal: "#22c55e",
  Moderado: "#f97316",
  Intenso: "#ef4444",
  Parado: "#7c3aed",
};

import { useNavigate } from "react-router";
import { api } from "../services/api";
import { RouteCard } from "../components/RouteCard";
import { VersionIndicator } from "../components/VersionIndicator";
import { ErrorBoundaryFallback } from "../components/ErrorBoundaryFallback";

type SortKey = keyof Road | "";
type SortDir = "asc" | "desc";

function unique(arr: string[]) {
  return [...new Set(arr.filter(Boolean))].sort();
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function PainelPage() {
  const navigate = useNavigate();
  const [roads, setRoads] = useState<Road[]>([]);
  const [loading, setLoading] = useState(true);

  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [viaFilter, setViaFilter] = useState<string[]>([]);
  const [nomeFilter, setNomeFilter] = useState<string[]>([]);
  const [trechoFilter, setTrechoFilter] = useState<string[]>([]);
  const [ocorrenciaFilter, setOcorrenciaFilter] = useState<string[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>("");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [currentTime, setCurrentTime] = useState(new Date());
  const [gaugesExpanded, setGaugesExpanded] = useState(true);

  // Dynamic values for filters
  const STATUS_OPTIONS = ["Normal", "Moderado", "Intenso", "Parado", "Erro"];
  const VIA_OPTIONS = useMemo(() => unique(roads.map((r) => r.via)), [roads]);
  const NOME_OPTIONS = useMemo(() => unique(roads.map((r) => r.nome)), [roads]);
  const TRECHO_OPTIONS = useMemo(() => unique(roads.map((r) => r.trecho)), [roads]);
  const OCORRENCIA_OPTIONS = useMemo(() => ["(Em branco)", ...unique(roads.map((r) => r.ocorrencia).filter(Boolean))], [roads]);

  useEffect(() => {
    let active = true;
    async function fetchPainel() {
      try {
        setLoading(true);
        const data = await api.get("/painel");
        if (!active) return;

        const mapped = data.resultados.map((r: any) => ({
          id: r.rota_id,
          via: r.sigla || "N/A",
          nome: r.nome || "N/A",
          trecho: r.trecho,
          status: r.status,
          ocorrencia: r.ocorrencia || "",
          relato: r.relato || "",
          hora: r.hora_atualizacao,
          atraso_min: r.atraso_min || 0,
          confianca_pct: r.confianca_pct || 0
        }));
        setRoads(mapped);
      } catch (err: any) {
        if (err.message === "Unauthorized") {
          navigate("/login");
        }
        console.error("Erro ao carregar painel:", err);
      } finally {
        if (active) setLoading(false);
      }
    }
    fetchPainel();

    // Auto-refresh every 5 minutes
    const fetchInterval = setInterval(fetchPainel, 300000);
    return () => {
      active = false;
      clearInterval(fetchInterval);
    };
  }, [navigate]);

  // Live clock
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Filtered data
  const filteredRoads = useMemo(() => {
    let data = roads;

    if (statusFilter.length > 0) {
      data = data.filter((r) => statusFilter.includes(r.status));
    }
    if (viaFilter.length > 0) {
      data = data.filter((r) => viaFilter.includes(r.via));
    }
    if (nomeFilter.length > 0) {
      data = data.filter((r) => nomeFilter.includes(r.nome));
    }
    if (trechoFilter.length > 0) {
      data = data.filter((r) => trechoFilter.includes(r.trecho));
    }
    if (ocorrenciaFilter.length > 0) {
      data = data.filter((r) => {
        if (ocorrenciaFilter.includes("(Em branco)") && r.ocorrencia === "") return true;
        return ocorrenciaFilter.includes(r.ocorrencia);
      });
    }

    if (sortKey) {
      data = [...data].sort((a, b) => {
        const av = String(a[sortKey] ?? "").toLowerCase();
        const bv = String(b[sortKey] ?? "").toLowerCase();
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    } else {
      // Ordenação padrão por severidade: Intenso > Moderado > Normal > Erro > N/A
      const severityOrder: Record<string, number> = {
        Parado: 1,
        Intenso: 2,
        Moderado: 3,
        Normal: 4,
        Erro: 5,
        "N/A": 6,
        "Sem dados": 7,
      };
      data = [...data].sort((a, b) => {
        const sa = severityOrder[a.status] ?? 99;
        const sb = severityOrder[b.status] ?? 99;
        return sa - sb;
      });
    }

    return data;
  }, [roads, statusFilter, viaFilter, nomeFilter, trechoFilter, ocorrenciaFilter, sortKey, sortDir]);

  // Gauges
  const countNormal = filteredRoads.filter((r) => r.status === "Normal").length;
  const countModerado = filteredRoads.filter((r) => r.status === "Moderado").length;
  const countIntenso = filteredRoads.filter((r) => r.status === "Intenso").length;

  // Define max gauge removing the explicit N/A ones from the total
  const countValid = filteredRoads.filter(
    (r) => r.status !== "N/A" && r.status !== "Erro" && r.status !== "Sem dados"
  ).length;
  const maxGauge = Math.max(countValid, 1);

  // Ticker messages
  const tickerMessages = useMemo(() => {
    if (countIntenso > 0) {
      const roads = filteredRoads.filter((r) => r.status === "Intenso");
      return roads.map((r) => `⚠ TRÁFEGO INTENSO: ${r.nome} – ${r.trecho} (${r.ocorrencia})`);
    }
    if (countModerado > 0) {
      return [`Tráfego moderado em ${countModerado} via(s). Atenção ao dirigir.`];
    }
    return ["✔  Fluxo normal em todas as vias no momento"];
  }, [filteredRoads, countIntenso, countModerado]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <ArrowUpDown size={12} className="opacity-40 ml-1" />;
    return sortDir === "asc" ? (
      <ChevronUp size={13} className="ml-1 text-yellow-300" />
    ) : (
      <ChevronDown size={13} className="ml-1 text-yellow-300" />
    );
  };

  const fmtTime = currentTime.toLocaleTimeString("pt-BR");
  const fmtDate = currentTime.toLocaleDateString("pt-BR");

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: "#2d2d2d", fontFamily: "Arial, sans-serif" }}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-5 py-3"
        style={{ background: "#1e1e1e", borderBottom: "3px solid #FFD700" }}
      >
        <div className="flex-1 flex items-center min-w-0">
          <RadarIcon size={56} className="flex-shrink-0" />
        </div>
        <motion.h1
          className="flex-1 text-center text-xl sm:text-2xl md:text-3xl lg:text-4xl font-black tracking-tight min-w-0 whitespace-nowrap"
          style={{ color: "#FFD700", textShadow: "0 2px 10px rgba(255,215,0,0.3)" }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          Monitoramento de Vias
        </motion.h1>

        {/* BRK Logo + Relógio */}
        <div className="flex-1 flex items-center justify-end gap-6 min-w-0">
          <div
            className="flex items-center justify-center px-4 py-2 rounded-lg bg-white shadow-sm"
            style={{ minHeight: 44 }}
          >
            <img
              src="/logo-brk.png"
              alt="BRK"
              className="h-8 w-auto object-contain"
              style={{ maxWidth: 120 }}
            />
          </div>
          <div className="flex items-center gap-2">
            <ErrorBoundaryFallback fallback={null}>
              <VersionIndicator />
            </ErrorBoundaryFallback>
            <div className="flex flex-col items-end">
              <span className="text-xs uppercase tracking-wider text-gray-400">{fmtDate}</span>
              <span className="text-lg font-mono font-bold tabular-nums" style={{ color: "#FFD700" }}>{fmtTime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Filters ────────────────────────────────────────────── */}
      <div className="px-4 py-3" style={{ background: "#252525" }}>
        <div className="flex gap-3 flex-wrap">
          <FilterDropdown
            label="Status da Via"
            options={STATUS_OPTIONS}
            selected={statusFilter}
            onChange={setStatusFilter}
          />
          <FilterDropdown
            label="Sigla da Via"
            options={VIA_OPTIONS}
            selected={viaFilter}
            onChange={setViaFilter}
          />
          <FilterDropdown
            label="Nome Rodovia"
            options={NOME_OPTIONS}
            selected={nomeFilter}
            onChange={setNomeFilter}
          />
          <FilterDropdown
            label="Trecho"
            options={TRECHO_OPTIONS}
            selected={trechoFilter}
            onChange={setTrechoFilter}
          />
          <FilterDropdown
            label="Ocorrencia"
            options={OCORRENCIA_OPTIONS}
            selected={ocorrenciaFilter}
            onChange={setOcorrenciaFilter}
          />
        </div>
      </div>

      {/* ── Status Ticker ───────────────────────────────────────── */}
      <StatusTicker messages={tickerMessages} />

      {/* ── Gauges (expandível) ─────────────────────────────────── */}
      <div
        className="px-4 py-3"
        style={{ background: "#252525", borderBottom: "1px solid #333" }}
      >
        <button
          type="button"
          onClick={() => setGaugesExpanded((e) => !e)}
          className="w-full flex items-center gap-3 py-2 px-3 rounded-lg transition-colors hover:bg-white/5"
          aria-expanded={gaugesExpanded}
          aria-label={gaugesExpanded ? "Recolher painel de vias" : "Expandir painel de vias"}
        >
          <div className="flex-1 grid grid-cols-3 gap-2 sm:gap-4 min-w-0">
            <span
              className="flex items-center justify-start gap-2 text-sm font-bold"
              style={{ color: "#ef4444" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#ef4444] flex-shrink-0" />
              <span className="truncate">Intenso {countIntenso}</span>
            </span>
            <span
              className="flex items-center justify-center gap-2 text-sm font-bold"
              style={{ color: "#f97316" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#f97316] flex-shrink-0" />
              <span className="truncate">Moderado {countModerado}</span>
            </span>
            <span
              className="flex items-center justify-end gap-2 text-sm font-bold"
              style={{ color: "#22c55e" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#22c55e] flex-shrink-0" />
              <span className="truncate">Normal {countNormal}</span>
            </span>
          </div>
          <motion.span
            className="flex-shrink-0 flex items-center"
            style={{ color: "#FFD700" }}
            animate={{ rotate: gaugesExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown size={20} />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {gaugesExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="pt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <motion.div
                  layout
                  className="min-w-0"
                  initial={{ scale: 0.95, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <GaugeChart
                    value={countIntenso}
                    max={maxGauge}
                    color="#ef4444"
                    title="Vias Tráfego Intenso"
                  />
                </motion.div>
                <motion.div
                  layout
                  className="min-w-0"
                  initial={{ scale: 0.95, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <GaugeChart
                    value={countModerado}
                    max={maxGauge}
                    color="#f97316"
                    title="Vias Tráfego Moderado"
                  />
                </motion.div>
                <motion.div
                  layout
                  className="min-w-0"
                  initial={{ scale: 0.95, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <GaugeChart
                    value={countNormal}
                    max={maxGauge}
                    color="#22c55e"
                    title="Vias Tráfego Normal"
                  />
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Grid of Cards ──────────────────────────────────────────────── */}
      <div className="px-5 pb-8 flex-1">
        <div className="flex justify-center items-center gap-4 mb-4">
          <span className="font-bold text-lg tracking-widest text-[#FFD700]">
            Visão Geral das Rotas
          </span>
          <span className="text-sm text-gray-400">
            {countValid} ativa{countValid !== 1 ? "s" : ""}
            {filteredRoads.length - countValid > 0 && ` + ${filteredRoads.length - countValid} sem dados`}
          </span>
        </div>

        {filteredRoads.length === 0 ? (
          <div className="py-12 text-center text-gray-400 bg-[#1e1e1e] rounded-xl border border-[#333]">
            Nenhum registro encontrado para os filtros selecionados.
          </div>
        ) : (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 items-stretch"
            layout
          >
            <AnimatePresence>
              {filteredRoads.map((road, idx) => (
                <motion.div
                  key={road.id}
                  className="min-h-0 flex"
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2, delay: idx * 0.015 }}
                >
                  <RouteCard
                    {...road}
                    onVerObs={(id) => navigate(`/consulta?rota_id=${id}`)}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}
