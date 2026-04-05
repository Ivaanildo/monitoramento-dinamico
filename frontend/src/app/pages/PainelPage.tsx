import React, { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  AlertTriangle,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  Clock3,
  Layers3,
  Radar,
  ShieldAlert,
  SlidersHorizontal,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router";
import { FilterDropdown } from "../components/FilterDropdown";
import { GaugeChart } from "../components/GaugeChart";
import { StatusTicker } from "../components/StatusTicker";
import { RadarIcon } from "../components/RadarIcon";
import { api } from "../services/api";
import { RouteCard } from "../components/RouteCard";
import { VersionIndicator } from "../components/VersionIndicator";
import { ErrorBoundaryFallback } from "../components/ErrorBoundaryFallback";

interface Incidente {
  categoria?: string;
  descricao?: string;
  severidade?: string;
  severidade_codigo?: string;
  rodovia_afetada?: string;
  road_closed?: boolean;
}

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
  incidentes: Incidente[];
  duracao_normal_min: number;
  duracao_transito_min: number;
  jam_factor_max: number;
}

type SortKey = "" | "status" | "via" | "trecho" | "atraso_min" | "confianca_pct";
type SortDir = "asc" | "desc";

const STATUS_OPTIONS = ["Normal", "Moderado", "Intenso", "Parado", "Erro"];

const statusPriority: Record<Road["status"], number> = {
  Parado: 1,
  Intenso: 2,
  Moderado: 3,
  Normal: 4,
  Erro: 5,
  "N/A": 6,
};

const sortOptions: Array<{ key: Exclude<SortKey, "">; label: string }> = [
  { key: "status", label: "Status" },
  { key: "atraso_min", label: "Atraso" },
  { key: "confianca_pct", label: "Confianca" },
  { key: "via", label: "Via" },
  { key: "trecho", label: "Trecho" },
];

function unique(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort();
}

function toneForCount(value: number) {
  if (value > 0) {
    return "text-rose-600";
  }
  return "text-emerald-600";
}

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

  const viaOptions = useMemo(() => unique(roads.map((road) => road.via)), [roads]);
  const nomeOptions = useMemo(() => unique(roads.map((road) => road.nome)), [roads]);
  const trechoOptions = useMemo(() => unique(roads.map((road) => road.trecho)), [roads]);
  const ocorrenciaOptions = useMemo(
    () => ["(Em branco)", ...unique(roads.map((road) => road.ocorrencia).filter(Boolean))],
    [roads],
  );

  useEffect(() => {
    let active = true;

    async function fetchPainel() {
      try {
        setLoading(true);
        const data = await api.get("/painel");
        if (!active) {
          return;
        }

        const mapped = data.resultados.map((road: any) => ({
          id: road.rota_id,
          via: road.sigla || "N/A",
          nome: road.nome || "N/A",
          trecho: road.trecho,
          status: road.status,
          ocorrencia: road.ocorrencia || "",
          relato: road.relato || "",
          hora: road.hora_atualizacao,
          atraso_min: road.atraso_min || 0,
          confianca_pct: road.confianca_pct || 0,
          incidentes: road.incidentes || [],
          duracao_normal_min: road.duracao_normal_min || 0,
          duracao_transito_min: road.duracao_transito_min || 0,
          jam_factor_max: road.jam_factor_max || 0,
        }));

        setRoads(mapped);
      } catch (error: any) {
        if (error.message === "Unauthorized") {
          navigate("/login");
        }
        console.error("Erro ao carregar painel:", error);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    fetchPainel();
    const interval = setInterval(fetchPainel, 300000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [navigate]);

  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const filteredRoads = useMemo(() => {
    let data = roads;

    if (statusFilter.length > 0) {
      data = data.filter((road) => statusFilter.includes(road.status));
    }
    if (viaFilter.length > 0) {
      data = data.filter((road) => viaFilter.includes(road.via));
    }
    if (nomeFilter.length > 0) {
      data = data.filter((road) => nomeFilter.includes(road.nome));
    }
    if (trechoFilter.length > 0) {
      data = data.filter((road) => trechoFilter.includes(road.trecho));
    }
    if (ocorrenciaFilter.length > 0) {
      data = data.filter((road) => {
        if (ocorrenciaFilter.includes("(Em branco)") && road.ocorrencia === "") {
          return true;
        }
        return ocorrenciaFilter.includes(road.ocorrencia);
      });
    }

    const sorted = [...data];

    if (!sortKey) {
      return sorted.sort((left, right) => {
        const leftRank = statusPriority[left.status] ?? 99;
        const rightRank = statusPriority[right.status] ?? 99;
        return leftRank - rightRank;
      });
    }

    return sorted.sort((left, right) => {
      if (sortKey === "status") {
        const comparison = (statusPriority[left.status] ?? 99) - (statusPriority[right.status] ?? 99);
        return sortDir === "asc" ? comparison : comparison * -1;
      }

      if (sortKey === "atraso_min" || sortKey === "confianca_pct") {
        const comparison = Number(left[sortKey]) - Number(right[sortKey]);
        return sortDir === "asc" ? comparison : comparison * -1;
      }

      const leftValue = String(left[sortKey] ?? "").toLowerCase();
      const rightValue = String(right[sortKey] ?? "").toLowerCase();
      return sortDir === "asc"
        ? leftValue.localeCompare(rightValue)
        : rightValue.localeCompare(leftValue);
    });
  }, [
    roads,
    statusFilter,
    viaFilter,
    nomeFilter,
    trechoFilter,
    ocorrenciaFilter,
    sortKey,
    sortDir,
  ]);

  const countNormal = filteredRoads.filter((road) => road.status === "Normal").length;
  const countModerado = filteredRoads.filter((road) => road.status === "Moderado").length;
  const countIntenso = filteredRoads.filter((road) => road.status === "Intenso").length;
  const countParado = filteredRoads.filter((road) => road.status === "Parado").length;
  const countErro = filteredRoads.filter((road) => road.status === "Erro" || road.status === "N/A").length;
  const countCritico = countIntenso + countParado;
  const countValid = filteredRoads.filter((road) => road.status !== "Erro" && road.status !== "N/A").length;
  const maxGauge = Math.max(countValid, 1);
  const withOccurrence = filteredRoads.filter((road) => road.ocorrencia).length;
  const totalIncidents = filteredRoads.reduce((acc, road) => acc + (road.incidentes?.length || 0), 0);
  const totalDelay = filteredRoads.reduce((acc, road) => acc + (road.atraso_min || 0), 0);
  const averageDelay = filteredRoads.length ? Math.round(totalDelay / filteredRoads.length) : 0;
  const averageConfidence = filteredRoads.length
    ? Math.round(filteredRoads.reduce((acc, road) => acc + (road.confianca_pct || 0), 0) / filteredRoads.length)
    : 0;
  const averageJam = filteredRoads.length
    ? Number((filteredRoads.reduce((acc, road) => acc + (road.jam_factor_max || 0), 0) / filteredRoads.length).toFixed(1))
    : 0;
  const lastSnapshot = filteredRoads.find((road) => road.hora)?.hora || "--";

  const commandCards = [
    {
      label: "Rotas monitoradas",
      value: filteredRoads.length,
      note: `${countValid} com leitura operacional`,
      icon: Layers3,
      tone: "bg-white text-slate-950",
    },
    {
      label: "Status critico",
      value: countCritico,
      note: countParado > 0 ? `${countParado} paradas no ciclo` : "Sem paradas registradas",
      icon: ShieldAlert,
      tone: "bg-rose-50 text-rose-700",
    },
    {
      label: "Atraso medio",
      value: `${averageDelay} min`,
      note: `${totalDelay} min acumulados`,
      icon: Clock3,
      tone: "bg-amber-50 text-amber-700",
    },
    {
      label: "Confianca media",
      value: `${averageConfidence}%`,
      note: `Jam medio ${averageJam}`,
      icon: TrendingUp,
      tone: "bg-emerald-50 text-emerald-700",
    },
  ];

  const focusNotes = [
    {
      title: "Prioridade imediata",
      value: `${countCritico} rotas em alerta maximo`,
      helper: countCritico > 0 ? "Foque primeiro nas rotas com status Intenso ou Parado." : "Nenhuma rota critica neste recorte.",
      accent: toneForCount(countCritico),
    },
    {
      title: "Ocorrencias abertas",
      value: `${withOccurrence} rotas com relato ativo`,
      helper: totalIncidents > 0 ? `${totalIncidents} incidentes relacionados no total.` : "Sem incidentes associados neste momento.",
      accent: withOccurrence > 0 ? "text-amber-600" : "text-slate-600",
    },
    {
      title: "Leitura do ciclo",
      value: `Atualizado ${lastSnapshot}`,
      helper: `${countErro} rotas sem leitura valida no momento.`,
      accent: "text-slate-900",
    },
  ];

  const tickerMessages = useMemo(() => {
    const criticalRoads = filteredRoads.filter((road) => road.status === "Intenso" || road.status === "Parado").slice(0, 4);

    if (criticalRoads.length > 0) {
      return criticalRoads.map(
        (road) => `${road.status}: ${road.nome || road.via} - ${road.ocorrencia || road.trecho}`,
      );
    }

    if (countModerado > 0) {
      return [
        `${countModerado} rotas em atencao moderada. Use os filtros para priorizar os trechos com maior impacto operacional.`,
      ];
    }

    return ["Fluxo estavel em toda a malha monitorada. O painel segue acompanhando o proximo ciclo automaticamente."];
  }, [filteredRoads, countModerado]);

  const handleSort = (key: Exclude<SortKey, "">) => {
    if (sortKey === key) {
      setSortDir((direction) => (direction === "asc" ? "desc" : "asc"));
      return;
    }

    setSortKey(key);
    setSortDir("asc");
  };

  const currentDate = currentTime.toLocaleDateString("pt-BR");
  const currentClock = currentTime.toLocaleTimeString("pt-BR");

  const SortIcon = ({ column }: { column: Exclude<SortKey, ""> }) => {
    if (sortKey !== column) {
      return <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />;
    }

    return sortDir === "asc" ? (
      <ChevronUp className="h-3.5 w-3.5 text-slate-900" />
    ) : (
      <ChevronDown className="h-3.5 w-3.5 text-slate-900" />
    );
  };

  return (
    <div className="relative min-h-screen overflow-hidden text-slate-900">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_26%),radial-gradient(circle_at_top_right,_rgba(15,23,42,0.1),_transparent_24%),linear-gradient(180deg,_rgba(248,250,252,0.65),_rgba(238,242,255,0.85))]" />

      <div className="relative mx-auto flex max-w-[1600px] flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <header className="glass-panel rounded-[34px] px-6 py-5 sm:px-7">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex items-start gap-4">
              <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-[24px] bg-slate-950 text-white shadow-[0_20px_45px_rgba(15,23,42,0.16)]">
                <RadarIcon size={38} />
              </div>

              <div className="min-w-0">
                <div className="inline-flex w-fit items-center gap-2 rounded-full bg-white/80 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  Painel corporativo ao vivo
                </div>
                <h1 className="mt-3 text-3xl font-black tracking-[-0.05em] text-slate-950 sm:text-4xl">
                  Monitoramento Dinamico
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                  Visao executiva da malha rodoviaria com leitura consolidada, filtros de triagem e acesso rapido a cada consulta detalhada.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="rounded-[26px] border border-white/80 bg-white/80 px-4 py-3 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                    <Radar className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Janela operacional</p>
                    <p className="mt-1 text-sm font-semibold text-slate-900">Atualizacao automatica a cada 5 min</p>
                  </div>
                </div>
              </div>

              <div className="rounded-[26px] border border-white/80 bg-slate-950 px-4 py-3 text-white shadow-[0_18px_40px_rgba(15,23,42,0.16)]">
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{currentDate}</p>
                    <p className="mt-1 font-mono text-xl font-bold">{currentClock}</p>
                  </div>

                  <div className="h-8 w-px bg-white/10" />

                  <div className="flex items-center gap-3">
                    <ErrorBoundaryFallback fallback={null}>
                      <VersionIndicator />
                    </ErrorBoundaryFallback>
                    <div className="rounded-2xl bg-white px-4 py-2">
                      <img
                        src="/logo-brk.png"
                        alt="BRK"
                        className="h-8 w-auto object-contain"
                        style={{ maxWidth: 120 }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-4 xl:grid-cols-[1.16fr_0.84fr]">
          <div className="glass-panel rounded-[34px] p-6 sm:p-7">
            <div className="flex h-full flex-col gap-6">
              <div className="space-y-3">
                <p className="eyebrow-label">Centro de comando viario</p>
                <h2 className="max-w-3xl text-3xl font-black tracking-[-0.05em] text-slate-950 sm:text-[2.6rem]">
                  Entenda o estado das rotas em um painel que privilegia triagem, leitura rapida e decisao.
                </h2>
                <p className="max-w-2xl text-sm leading-7 text-slate-600 sm:text-base">
                  O mesmo conjunto de dados agora aparece em uma camada visual mais clara: contexto do ciclo, distribuicao de status, filtros por dominio e acesso direto ao mapa de cada rota.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {commandCards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <motion.div
                      key={card.label}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.28 }}
                      className={`rounded-[28px] border border-white/80 p-5 shadow-[0_20px_36px_rgba(15,23,42,0.06)] ${card.tone}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{card.label}</p>
                          <p className="mt-3 text-3xl font-black tracking-[-0.05em]">{card.value}</p>
                        </div>
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white">
                          <Icon className="h-5 w-5" />
                        </div>
                      </div>
                      <p className="mt-3 text-sm text-slate-500">{card.note}</p>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="glass-panel rounded-[34px] p-6">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="eyebrow-label">Leitura do ciclo</p>
                  <h2 className="mt-2 text-xl font-black tracking-[-0.03em] text-slate-950">Onde agir agora</h2>
                </div>
                <div className="rounded-full bg-white px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  snapshot {lastSnapshot}
                </div>
              </div>

              <div className="space-y-3">
                {focusNotes.map((item) => (
                  <div key={item.title} className="surface-panel rounded-[26px] px-4 py-4">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{item.title}</p>
                    <p className={`mt-2 text-lg font-black tracking-[-0.03em] ${item.accent}`}>{item.value}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-500">{item.helper}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel rounded-[34px] p-6">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <p className="eyebrow-label">Filtros de triagem</p>
                  <h2 className="mt-2 text-xl font-black tracking-[-0.03em] text-slate-950">Recorte por dominio</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    Refine o painel por status, via, nome, trecho ou ocorrencia sem perder a leitura geral do ciclo.
                  </p>
                </div>
                <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-white">
                  <SlidersHorizontal className="h-5 w-5" />
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <FilterDropdown label="Status" options={STATUS_OPTIONS} selected={statusFilter} onChange={setStatusFilter} />
                <FilterDropdown label="Via" options={viaOptions} selected={viaFilter} onChange={setViaFilter} />
                <FilterDropdown label="Nome" options={nomeOptions} selected={nomeFilter} onChange={setNomeFilter} />
                <FilterDropdown label="Trecho" options={trechoOptions} selected={trechoFilter} onChange={setTrechoFilter} />
                <div className="md:col-span-2">
                  <FilterDropdown
                    label="Ocorrencia"
                    options={ocorrenciaOptions}
                    selected={ocorrenciaFilter}
                    onChange={setOcorrenciaFilter}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        <StatusTicker messages={tickerMessages} />

        <section className="glass-panel rounded-[34px] p-5 sm:p-6">
          <button
            type="button"
            onClick={() => setGaugesExpanded((value) => !value)}
            className="flex w-full items-center justify-between gap-4 rounded-[26px] bg-white/70 px-4 py-4 text-left transition hover:bg-white/82"
            aria-expanded={gaugesExpanded}
            aria-label={gaugesExpanded ? "Recolher distribuicao de status" : "Expandir distribuicao de status"}
          >
            <div className="grid min-w-0 flex-1 gap-3 sm:grid-cols-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Critico</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.04em] text-rose-600">{countCritico}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Moderado</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.04em] text-amber-600">{countModerado}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Normal</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.04em] text-emerald-600">{countNormal}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Sem leitura</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.04em] text-slate-600">{countErro}</p>
              </div>
            </div>

            <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-slate-950 text-white">
              {gaugesExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </span>
          </button>

          <AnimatePresence initial={false}>
            {gaugesExpanded ? (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.22, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="grid gap-4 pt-4 sm:grid-cols-2 xl:grid-cols-4">
                  <GaugeChart value={countParado} max={maxGauge} color="#7c3aed" title="Rotas paradas" />
                  <GaugeChart value={countIntenso} max={maxGauge} color="#dc2626" title="Rotas intensas" />
                  <GaugeChart value={countModerado} max={maxGauge} color="#f97316" title="Rotas moderadas" />
                  <GaugeChart value={countNormal} max={maxGauge} color="#16a34a" title="Rotas normais" />
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </section>

        <section className="glass-panel rounded-[34px] p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="eyebrow-label">Rotas priorizadas</p>
              <h2 className="mt-2 text-2xl font-black tracking-[-0.04em] text-slate-950">Leitura consolidada da malha</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {filteredRoads.length} rotas no recorte atual, {withOccurrence} com ocorrencia registrada e {totalIncidents} incidentes relacionados.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {sortOptions.map((option) => {
                const isActive = sortKey === option.key;
                return (
                  <button
                    key={option.key}
                    type="button"
                    onClick={() => handleSort(option.key)}
                    className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "border-slate-950 bg-slate-950 text-white"
                        : "border-white/80 bg-white/82 text-slate-600 hover:border-slate-300 hover:text-slate-900"
                    }`}
                  >
                    {option.label}
                    <SortIcon column={option.key} />
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-5">
            {loading ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={`skeleton-${index}`} className="surface-panel min-h-[280px] animate-pulse rounded-[30px]" />
                ))}
              </div>
            ) : filteredRoads.length === 0 ? (
              <div className="surface-panel rounded-[30px] px-6 py-12 text-center">
                <AlertTriangle className="mx-auto h-10 w-10 text-amber-500" />
                <h3 className="mt-4 text-xl font-black tracking-[-0.03em] text-slate-950">
                  Nenhuma rota encontrada
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Revise os filtros aplicados para voltar a ver a leitura consolidada do ciclo.
                </p>
              </div>
            ) : (
              <motion.div layout className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <AnimatePresence>
                  {filteredRoads.map((road, index) => (
                    <motion.div
                      key={road.id}
                      layout
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -18 }}
                      transition={{ duration: 0.22, delay: index * 0.015 }}
                    >
                      <RouteCard
                        {...road}
                        incidentes={road.incidentes}
                        duracao_normal_min={road.duracao_normal_min}
                        duracao_transito_min={road.duracao_transito_min}
                        jam_factor_max={road.jam_factor_max}
                        onVerObs={(id) => window.open(`/consulta?rota_id=${id}`, "_blank")}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
