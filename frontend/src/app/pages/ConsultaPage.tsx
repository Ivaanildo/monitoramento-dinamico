import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
    ArrowLeft,
    AlertTriangle,
    CheckCircle,
    Clock,
    Gauge,
    MapPin,
    Navigation,
    Zap,
    TrendingUp,
    ExternalLink,
    RefreshCw,
    Info,
    Wind,
    Activity,
    Download,
} from "lucide-react";
import { api } from "../services/api";
import { RadarIcon } from "../components/RadarIcon";

// ─── Lazy-load MapView to avoid SSR issues with Leaflet ──────────────────────
const MapView = React.lazy(() =>
    import("../components/MapView").then((m) => ({ default: m.MapView }))
);

// ─── Types ────────────────────────────────────────────────────────────────────
interface ConsultaData {
    rota_id: string;
    origem?: string;       // raw "lat,lng" string
    destino?: string;      // raw "lat,lng" string
    hub_origem?: string;
    hub_destino?: string;
    status: "Normal" | "Moderado" | "Intenso" | "Erro" | "N/A";
    atraso_min: number;
    duracao_normal_min: number;
    duracao_transito_min: number;
    distancia_km: number;
    velocidade_atual_kmh: number;
    velocidade_livre_kmh: number;
    pct_congestionado: number;
    jam_factor_avg: number;
    jam_factor_max: number;
    confianca_pct: number;
    confianca: string;
    incidente_principal?: { categoria: string; descricao: string; severidade?: string } | null;
    incidentes: { lat?: number; lng?: number; tipo?: string; descricao?: string; severidade?: string; categoria?: string }[];
    route_pts: { lat: number; lng: number }[];
    flow_pts?: { lat: number; lng: number; jam: number }[];
    via_coords?: { lat: number; lng: number }[];
    link_waze?: string;
    link_gmaps?: string;
    fontes: string[];
    status_google?: string;
    status_here?: string;
    consultado_em?: string;
    cache_hit?: boolean;
    erros?: { google?: string; here?: string };
}

// ─── Timezone helper ──────────────────────────────────────────────────────────
function toLocalBRT(utcStr?: string): string {
    if (!utcStr) return '—';
    // Handle both space-separated and T-separated ISO formats
    const dt = new Date(utcStr.trim().replace(' ', 'T') + 'Z');
    if (isNaN(dt.getTime())) return utcStr;
    return dt.toLocaleString('pt-BR', {
        timeZone: 'America/Sao_Paulo',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });
}

// ─── Status theme ────────────────────────────────────────────────────────────
const STATUS_THEME = {
    Normal: { border: "#10b981", bg: "#d1fae5", text: "#065f46", icon: CheckCircle },
    Moderado: { border: "#f59e0b", bg: "#fef3c7", text: "#92400e", icon: AlertTriangle },
    Intenso: { border: "#ef4444", bg: "#fee2e2", text: "#991b1b", icon: AlertTriangle },
    Erro: { border: "#6b7280", bg: "#f3f4f6", text: "#374151", icon: AlertTriangle },
    "N/A": { border: "#6b7280", bg: "#f3f4f6", text: "#374151", icon: Info },
};

// ─── Skeleton component ───────────────────────────────────────────────────────
function Skeleton({ className = "" }: { className?: string }) {
    return (
        <div
            className={`rounded animate-pulse bg-gray-700 ${className}`}
            style={{ animation: "shimmer 1.5s infinite" }}
        />
    );
}

// ─── KPI card ────────────────────────────────────────────────────────────────
function KpiCard({
    icon: Icon,
    label,
    value,
    sub,
    color = "#FFD700",
    tooltip,
}: {
    icon: React.ElementType;
    label: string;
    value: string | number;
    sub?: string;
    color?: string;
    tooltip?: string;
}) {
    return (
        <div
            className="flex items-start gap-3 p-3 rounded-lg relative"
            style={{ background: "#1e1e1e", border: "1px solid #333" }}
        >
            <div
                className="p-2 rounded-lg flex-shrink-0"
                style={{ background: "#2a2a2a" }}
            >
                <Icon size={16} style={{ color }} />
            </div>
            <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1 mb-0.5">
                    <div className="text-xs text-gray-400">{label}</div>
                    {tooltip && (
                        <div className="relative group cursor-pointer flex-shrink-0">
                            <span
                                className="text-gray-600 hover:text-gray-300 transition-colors"
                                style={{ fontSize: "10px", fontWeight: "bold", lineHeight: 1 }}
                            >
                                ⓘ
                            </span>
                            <div
                                className="absolute bottom-full right-0 mb-1 z-50 hidden group-hover:block"
                                style={{ minWidth: "160px", maxWidth: "220px" }}
                            >
                                <div
                                    className="text-xs text-gray-200 rounded-lg px-2.5 py-2 shadow-xl"
                                    style={{ background: "#111", border: "1px solid #444", lineHeight: "1.4" }}
                                >
                                    {tooltip}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <div className="font-bold text-white text-sm">{value}</div>
                {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
            </div>
        </div>
    );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function ConsultaPage() {
    const [params] = useSearchParams();
    const navigate = useNavigate();
    const rotaId = params.get("rota_id") || "";

    const [data, setData] = useState<ConsultaData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [elapsed, setElapsed] = useState(0);
    const [dataSource, setDataSource] = useState<"snapshot" | "realtime" | null>(null);

    // Elapsed timer while loading (shows how long the real-time API is taking)
    useEffect(() => {
        if (!loading) return;
        const t = setInterval(() => setElapsed((e) => e + 1), 1000);
        return () => clearInterval(t);
    }, [loading]);

    const fetchRealtime = () => {
        if (!rotaId) {
            setError("Nenhuma rota selecionada. Volte ao painel.");
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        setElapsed(0);

        api.getConsulta(rotaId)
            .then((d) => {
                setData(d);
                setDataSource("realtime");
                setLoading(false);
            })
            .catch((err: Error) => {
                if (err.message === "Unauthorized") navigate("/login");
                setError("Falha ao consultar a rota. Tente novamente.");
                setLoading(false);
            });
    };

    const fetchData = () => fetchRealtime();

    // On mount: try snapshot first for fast initial display
    useEffect(() => {
        if (!rotaId) {
            setError("Nenhuma rota selecionada. Volte ao painel.");
            setLoading(false);
            return;
        }
        api.getSnapshot(rotaId)
            .then((snap) => {
                // Populate a minimal ConsultaData from the snapshot
                setData((prev) => prev ?? {
                    rota_id: snap.rota_id,
                    status: snap.status,
                    atraso_min: snap.atraso_min ?? 0,
                    incidente_principal: snap.ocorrencia_principal
                        ? { categoria: snap.ocorrencia_principal, descricao: "" }
                        : null,
                    duracao_normal_min: 0,
                    duracao_transito_min: 0,
                    distancia_km: 0,
                    velocidade_atual_kmh: 0,
                    velocidade_livre_kmh: 0,
                    pct_congestionado: 0,
                    jam_factor_avg: 0,
                    jam_factor_max: 0,
                    confianca_pct: 0,
                    confianca: "",
                    incidentes: [],
                    route_pts: [],
                    fontes: [],
                    consultado_em: snap.ciclo_ts,
                });
                setDataSource("snapshot");
                fetchRealtime();            // sempre busca dados completos (route_pts)
            })
            .catch(() => {
                // Snapshot failed — fall through to full real-time consult
                fetchRealtime();
            });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [rotaId]);

    const handleDownloadCSV = () => {
        if (!data) return;

        const escapeCSV = (val: any) => {
            if (val == null) return '""';
            const str = String(val);
            return `"${str.replace(/"/g, '""')}"`;
        };

        const headers = [
            "ID", "Status", "Origem", "Destino",
            "Atraso (min)", "Duracao Normal (min)", "Duracao c/ Transito (min)",
            "Distancia (km)", "Vel Atual (km/h)", "Congestionado (%)",
            "Jam Avg", "Jam Max", "Confianca (%)"
        ];

        const row = [
            escapeCSV(data.rota_id),
            escapeCSV(data.status),
            escapeCSV(data.hub_origem || data.origem || ''),
            escapeCSV(data.hub_destino || data.destino || ''),
            data.atraso_min || 0,
            data.duracao_normal_min || 0,
            data.duracao_transito_min || 0,
            (data.distancia_km || 0).toFixed(2),
            (data.velocidade_atual_kmh || 0).toFixed(1),
            (data.pct_congestionado || 0).toFixed(1),
            (data.jam_factor_avg || 0).toFixed(2),
            (data.jam_factor_max || 0).toFixed(2),
            data.confianca_pct || 0
        ];

        const csvContent = "\uFEFF" + headers.join(";") + "\n" + row.join(";");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `visao_geral_${data.rota_id}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleDownloadJSON = () => {
        if (!data) return;
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `visao_geral_${data.rota_id}.json`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const theme = data ? (STATUS_THEME[data.status] || STATUS_THEME["N/A"]) : STATUS_THEME["N/A"];
    const StatusIcon = theme.icon;

    return (
        <div
            className="min-h-screen flex flex-col"
            style={{ background: "#1a1a1a", fontFamily: "Arial, sans-serif" }}
        >
            {/* ── Header ─────────────────────────────────────────────────── */}
            <div
                className="flex items-center justify-between px-5 py-3 flex-shrink-0"
                style={{ background: "#111", borderBottom: "3px solid #FFD700" }}
            >
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate("/painel")}
                        className="flex items-center gap-2 text-sm font-bold transition-colors hover:text-yellow-300"
                        style={{ color: "#FFD700" }}
                    >
                        <ArrowLeft size={18} />
                        Painel
                    </button>
                    <div className="w-px h-6 bg-gray-600" />
                    <RadarIcon size={40} />
                    <div>
                        <div className="text-xs text-gray-400 uppercase tracking-widest">
                            Consulta Individual
                        </div>
                        <div className="font-black text-white text-lg leading-tight">
                            {loading ? (
                                <Skeleton className="w-48 h-5 mt-1" />
                            ) : data ? (
                                <>
                                    <span style={{ color: "#FFD700" }}>{data.rota_id}</span>
                                    {" · "}
                                    <span className="text-gray-300 text-base font-semibold">
                                        {data.hub_origem} → {data.hub_destino}
                                    </span>
                                </>
                            ) : (
                                <span className="text-gray-400">Rota não encontrada</span>
                            )}
                        </div>
                    </div>
                </div>

                {data && (
                    <div className="flex items-center gap-2">
                        {dataSource === "snapshot" && (
                            <span className="text-xs px-2 py-0.5 rounded font-medium" style={{ background: "#1e3a5f", color: "#93c5fd" }}>
                                Dados do ciclo
                            </span>
                        )}
                        {dataSource === "realtime" && (
                            <span className="text-xs px-2 py-0.5 rounded font-medium" style={{ background: "#14532d", color: "#86efac" }}>
                                Tempo real
                            </span>
                        )}
                        {data.cache_hit && (
                            <span className="text-xs text-gray-500 italic">cache</span>
                        )}
                        <button
                            onClick={handleDownloadCSV}
                            title="Exportar como CSV (Excel)"
                            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-bold transition-colors"
                            style={{ background: "#1a361a", color: "#4ade80", border: "1px solid #22c55e44" }}
                        >
                            <Download size={12} />
                            Excel
                        </button>
                        <button
                            onClick={handleDownloadJSON}
                            title="Exportar dados puros (JSON)"
                            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-bold transition-colors"
                            style={{ background: "#2a2a2a", color: "#9ca3af", border: "1px solid #444" }}
                        >
                            <Download size={12} />
                            JSON
                        </button>
                        <button
                            onClick={fetchRealtime}
                            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-bold transition-colors"
                            style={{ background: "#2a2a2a", color: "#FFD700", border: "1px solid #444" }}
                        >
                            <RefreshCw size={12} />
                            Atualizar
                        </button>
                    </div>
                )}
            </div>

            {/* ── Body: Split layout ─────────────────────────────────────── */}
            <div className="flex flex-1 overflow-hidden" style={{ minHeight: 0 }}>

                {/* ── Sidebar ───────────────────────────────────────────── */}
                <div
                    className="flex flex-col overflow-y-auto flex-shrink-0"
                    style={{
                        width: "340px",
                        background: "#212121",
                        borderRight: "1px solid #333",
                        padding: "16px",
                        gap: "12px",
                    }}
                >
                    {/* Loading state */}
                    {loading && (
                        <>
                            <div
                                className="p-4 rounded-xl text-center"
                                style={{ background: "#1e1e1e", border: "1px solid #333" }}
                            >
                                <div className="flex items-center justify-center gap-2 mb-2">
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    >
                                        <Activity size={20} style={{ color: "#FFD700" }} />
                                    </motion.div>
                                    <span className="font-bold text-yellow-400 text-sm">
                                        Consultando APIs em tempo real…
                                    </span>
                                </div>
                                <div className="text-xs text-gray-500">
                                    Google Routes + HERE Traffic · {elapsed}s
                                </div>
                                <div className="mt-3 h-1 rounded-full overflow-hidden bg-gray-700">
                                    <motion.div
                                        className="h-full rounded-full"
                                        style={{ background: "#FFD700" }}
                                        animate={{ x: ["-100%", "100%"] }}
                                        transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                                    />
                                </div>
                            </div>
                            <Skeleton className="h-14 w-full" />
                            <div className="grid grid-cols-2 gap-2">
                                {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-16" />)}
                            </div>
                            <Skeleton className="h-24 w-full" />
                            <Skeleton className="h-10 w-full" />
                        </>
                    )}

                    {/* Error state */}
                    {!loading && error && (
                        <div
                            className="p-4 rounded-xl text-center"
                            style={{ background: "#1e1e1e", border: "1px solid #ef4444" }}
                        >
                            <AlertTriangle size={32} className="text-red-400 mx-auto mb-2" />
                            <p className="text-red-300 text-sm font-bold mb-3">{error}</p>
                            <button
                                onClick={fetchData}
                                className="text-xs px-4 py-2 rounded-lg font-bold transition-colors"
                                style={{ background: "#ef4444", color: "white" }}
                            >
                                Tentar novamente
                            </button>
                        </div>
                    )}

                    {/* Data loaded */}
                    <AnimatePresence>
                        {!loading && data && (
                            <motion.div
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.4 }}
                                className="flex flex-col gap-3"
                            >
                                {/* Status pill */}
                                <div
                                    className="flex items-center gap-3 p-4 rounded-xl"
                                    style={{
                                        background: theme.bg + "18",
                                        border: `2px solid ${theme.border}`,
                                    }}
                                >
                                    <StatusIcon size={28} style={{ color: theme.border }} />
                                    <div>
                                        <div className="text-xs text-gray-400 uppercase tracking-widest">
                                            Status do Tráfego
                                        </div>
                                        <div
                                            className="text-xl font-black"
                                            style={{ color: theme.border }}
                                        >
                                            {data.status}
                                        </div>
                                        {data.incidente_principal && (
                                            <div className="text-xs text-gray-400 mt-0.5">
                                                {data.incidente_principal.categoria}
                                                {data.incidente_principal.descricao && ` — ${data.incidente_principal.descricao}`}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Rota coords block */}
                                <div
                                    className="p-3 rounded-xl flex flex-col gap-2"
                                    style={{ background: "#1e1e1e", border: "1px solid #333" }}
                                >
                                    <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">
                                        Rota
                                    </div>
                                    {/* Origem */}
                                    <div className="flex items-start gap-2">
                                        <span className="mt-0.5 w-3 h-3 rounded-full flex-shrink-0" style={{ background: "#22c55e" }} />
                                        <div>
                                            <div className="text-xs font-mono text-gray-300 leading-tight">
                                                {data.origem || '—'}
                                            </div>
                                            <div className="text-xs text-gray-500 leading-tight mt-0.5">
                                                {data.hub_origem || ''}
                                            </div>
                                        </div>
                                    </div>
                                    {/* Destino */}
                                    <div className="flex items-start gap-2">
                                        <span className="mt-0.5 w-3 h-3 rounded-full flex-shrink-0" style={{ background: "#ef4444" }} />
                                        <div>
                                            <div className="text-xs font-mono text-gray-300 leading-tight">
                                                {data.destino || '—'}
                                            </div>
                                            <div className="text-xs text-gray-500 leading-tight mt-0.5">
                                                {data.hub_destino || ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* KPIs grid */}
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest px-1">
                                    Métricas da Rota
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <KpiCard
                                        icon={Clock}
                                        label="Atraso"
                                        value={data.atraso_min > 0 ? `+${data.atraso_min} min` : "Sem atraso"}
                                        color={data.atraso_min > 0 ? "#ef4444" : "#22c55e"}
                                        tooltip="Tempo extra estimado devido ao trânsito atual, comparando a duração normal com a duração real."
                                    />
                                    <KpiCard
                                        icon={Navigation}
                                        label="Distância"
                                        value={`${data.distancia_km.toFixed(1)} km`}
                                        color="#60a5fa"
                                        tooltip="Distância total do trajeto de origem a destino, em quilômetros."
                                    />
                                    <KpiCard
                                        icon={Clock}
                                        label="Duração Normal"
                                        value={`${data.duracao_normal_min} min`}
                                        color="#a78bfa"
                                        tooltip="Duração estimada da viagem em condições ideais de tráfego, sem congestionamento."
                                    />
                                    <KpiCard
                                        icon={TrendingUp}
                                        label="c/ Trânsito"
                                        value={`${data.duracao_transito_min} min`}
                                        color={data.duracao_transito_min > data.duracao_normal_min ? "#f97316" : "#22c55e"}
                                        tooltip="Duração total estimada levando em conta as condições de trânsito em tempo real."
                                    />
                                    <KpiCard
                                        icon={Wind}
                                        label="Vel. Atual"
                                        value={`${data.velocidade_atual_kmh.toFixed(0)} km/h`}
                                        sub={`livre: ${data.velocidade_livre_kmh.toFixed(0)} km/h`}
                                        color="#34d399"
                                        tooltip="Velocidade média atual dos veículos na rota (HERE Traffic). 'Livre' é a velocidade sem congestionamento."
                                    />
                                    <KpiCard
                                        icon={Gauge}
                                        label="Congestionado"
                                        value={`${data.pct_congestionado.toFixed(0)}%`}
                                        color={data.pct_congestionado > 50 ? "#ef4444" : "#f97316"}
                                        tooltip="Percentual da rota que está com algum nível de congestionamento no momento."
                                    />
                                    <KpiCard
                                        icon={Activity}
                                        label="Jam Avg / Max"
                                        value={`${data.jam_factor_avg.toFixed(1)} / ${data.jam_factor_max.toFixed(1)}`}
                                        color="#fb923c"
                                        tooltip="Fator de congestionamento médio e máximo na rota (escala 0–10). Acima de 6 = Moderado, acima de 8 = Intenso/Parado."
                                    />
                                    <KpiCard
                                        icon={Zap}
                                        label="Confiança"
                                        value={`${data.confianca_pct}%`}
                                        sub={data.confianca}
                                        color="#FFD700"
                                        tooltip="Nível de confiabilidade dos dados de trânsito agregados (Google + HERE). Alta = dados mais precisos; Baixa = possível variação nos resultados."
                                    />
                                </div>

                                {/* Incidentes */}
                                {data.incidentes && data.incidentes.length > 0 && (
                                    <div>
                                        <div className="text-xs font-bold text-gray-500 uppercase tracking-widest px-1 mb-2">
                                            Incidentes HERE ({data.incidentes.length})
                                        </div>
                                        <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto pr-1">
                                            {data.incidentes.map((inc, i) => (
                                                <div
                                                    key={i}
                                                    className="flex items-start gap-2 p-2.5 rounded-lg text-xs"
                                                    style={{ background: "#1e1e1e", border: "1px solid #333" }}
                                                >
                                                    <span
                                                        className="w-2 h-2 rounded-full flex-shrink-0 mt-0.5"
                                                        style={{
                                                            background:
                                                                inc.severidade === "critical" ? "#ef4444" :
                                                                    inc.severidade === "major" ? "#f97316" : "#eab308",
                                                        }}
                                                    />
                                                    <div>
                                                        <div className="font-bold text-gray-300">
                                                            {inc.tipo || "Incidente"}
                                                        </div>
                                                        {inc.descricao && (
                                                            <div className="text-gray-500 mt-0.5">{inc.descricao}</div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Navigation links */}
                                <div className="flex gap-2">
                                    {data.link_waze && (
                                        <a
                                            href={data.link_waze}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-xs font-bold transition-opacity hover:opacity-80"
                                            style={{ background: "#00d4ff22", color: "#00d4ff", border: "1px solid #00d4ff44" }}
                                        >
                                            <MapPin size={13} /> Waze
                                            <ExternalLink size={10} className="opacity-60" />
                                        </a>
                                    )}
                                    {data.link_gmaps && (
                                        <a
                                            href={data.link_gmaps}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-xs font-bold transition-opacity hover:opacity-80"
                                            style={{ background: "#4285f422", color: "#4285f4", border: "1px solid #4285f444" }}
                                        >
                                            <Navigation size={13} /> Google Maps
                                            <ExternalLink size={10} className="opacity-60" />
                                        </a>
                                    )}
                                </div>

                                {/* Fontes */}
                                <div
                                    className="p-3 rounded-lg"
                                    style={{ background: "#1e1e1e", border: "1px solid #333" }}
                                >
                                    <div className="text-xs text-gray-500 uppercase tracking-widest mb-1.5">
                                        Fontes utilizadas
                                    </div>
                                    {data.fontes.length > 0 ? (
                                        data.fontes.map((f, i) => (
                                            <div key={i} className="flex items-center gap-1.5 text-xs text-gray-300">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                                                {f}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-xs text-gray-500">Nenhuma fonte OK</div>
                                    )}
                                    {data.consultado_em && (
                                        <div className="text-xs text-gray-600 mt-2">
                                            Consultado em: {toLocalBRT(data.consultado_em)} (Brasília)
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* ── Map canvas ────────────────────────────────────────── */}
                <div className="flex-1 relative" style={{ minHeight: 0 }}>
                    {loading && (
                        <div
                            className="absolute inset-0 flex flex-col items-center justify-center gap-4"
                            style={{ background: "#1a1a1a", zIndex: 10 }}
                        >
                            <motion.div
                                animate={{ scale: [1, 1.1, 1], opacity: [0.6, 1, 0.6] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            >
                                <MapPin size={64} style={{ color: "#FFD700" }} />
                            </motion.div>
                            <div className="text-gray-400 text-sm">
                                Aguardando dados da rota para renderizar o mapa…
                            </div>
                        </div>
                    )}

                    {!loading && error && (
                        <div
                            className="absolute inset-0 flex items-center justify-center"
                            style={{ background: "#1a1a1a" }}
                        >
                            <div className="text-gray-500 text-sm">Mapa indisponível</div>
                        </div>
                    )}

                    {!loading && data && (
                        <React.Suspense
                            fallback={
                                <div className="w-full h-full flex items-center justify-center" style={{ background: "#1a1a1a" }}>
                                    <div className="text-gray-400 text-sm">Carregando mapa…</div>
                                </div>
                            }
                        >
                            <MapView
                                routePts={data.route_pts || []}
                                flowPts={data.flow_pts || []}
                                viaCoords={data.via_coords || []}
                                status={data.status}
                                hubOrigem={data.hub_origem || "Origem"}
                                hubDestino={data.hub_destino || "Destino"}
                                incidentes={data.incidentes || []}
                            />
                        </React.Suspense>
                    )}
                </div>
            </div>
        </div>
    );
}
