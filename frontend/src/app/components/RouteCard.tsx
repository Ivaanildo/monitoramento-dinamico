import React, { useState } from "react";
import { ArrowRight, ArrowLeft, Map } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

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
        border: "#10b981", // Emerald 500
        bgLight: "#ecfdf5", // Emerald 50
        text: "#047857", // Emerald 700
    },
    Moderado: {
        border: "#f59e0b", // Amber 500
        bgLight: "#fffbeb", // Amber 50
        text: "#b45309", // Amber 700
    },
    Intenso: {
        border: "#ef4444", // Red 500
        bgLight: "#fef2f2", // Red 50
        text: "#b91c1c", // Red 700
    },
    Parado: {
        border: "#7c3aed", // Violet 600
        bgLight: "#f5f3ff", // Violet 50
        text: "#5b21b6", // Violet 800
    },
    Erro: {
        border: "#991b1b",
        bgLight: "#fef2f2",
        text: "#7f1d1d",
    },
    "N/A": {
        border: "#9ca3af",
        bgLight: "#f3f4f6",
        text: "#4b5563",
    }
};

export function RouteCard(props: RouteCardProps) {
    const {
        id, via, trecho, status, ocorrencia, relato,
        atraso_min = 0, confianca_pct = 0, onVerObs,
        incidentes = [], duracao_normal_min = 0, duracao_transito_min = 0, jam_factor_max = 0,
    } = props;

    const [isFlipped, setIsFlipped] = useState(false);
    const theme = STATUS_THEME[status] || STATUS_THEME.Normal;

    // Format delay pill conditionally
    const hasDelay = atraso_min > 0;

    // Clean via text (e.g., if there are multiple)
    const displayVia = via || "Rodovia";

    // Get occurrence display
    const displayOcorrencia = ocorrencia || "Sem ocorrência";
    const hasOcorrencia = !!ocorrencia;

    return (
        <div
            className="flex flex-col flex-1 rounded-lg shadow-sm bg-white overflow-hidden p-4 relative border border-gray-100 min-h-[160px] w-full"
            style={{ borderLeft: `5px solid ${theme.border}` }}
        >
            <AnimatePresence mode="wait">
                {!isFlipped ? (
                    <motion.div
                        key="ladoA"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2 }}
                        className="flex flex-col h-full w-full"
                    >
                        <div className="flex justify-between items-start mb-3">
                            <h3 className="font-bold text-gray-800 text-lg truncate pr-2">
                                {displayVia}
                            </h3>
                            <div
                                className="px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap uppercase tracking-wide"
                                style={{ backgroundColor: theme.bgLight, color: theme.text }}
                            >
                                {status}
                            </div>
                        </div>

                        <p className="text-gray-600 text-sm mb-4 line-clamp-2 min-h-[40px]">
                            {trecho}
                        </p>

                        <div className="flex flex-wrap gap-2 mb-4">
                            {hasDelay && (
                                <div className="flex items-center gap-1 text-xs font-bold px-2 py-1 rounded" style={{ backgroundColor: "#fee2e2", color: "#b91c1c" }}>
                                    <span className="text-[10px] text-red-500">•</span> ATRASO +{atraso_min} min
                                </div>
                            )}

                            <div
                                className="flex items-center gap-1 text-xs font-bold px-2 py-1 rounded"
                                style={hasOcorrencia
                                    ? { backgroundColor: "#fff7ed", color: "#c2410c" }
                                    : { backgroundColor: "#f3f4f6", color: "#9ca3af" }
                                }
                            >
                                {displayOcorrencia}
                            </div>
                        </div>

                        <div className="flex justify-between items-end mt-auto pt-2">
                            <div className="text-xs text-gray-400 font-medium tracking-wide">
                                conf. {confianca_pct}%
                            </div>

                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => onVerObs && onVerObs(id)}
                                    className="text-xs text-[#FFD700] hover:text-yellow-600 font-bold flex items-center gap-1 transition-colors"
                                >
                                    <Map size={12} /> visão geral
                                </button>
                                <button
                                    onClick={() => setIsFlipped(true)}
                                    className="text-xs text-gray-400 hover:text-gray-600 font-medium flex items-center gap-1 transition-colors group"
                                >
                                    ver obs.
                                    <ArrowRight size={12} className="group-hover:translate-x-1 transition-transform" />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key="ladoB"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2 }}
                        className="flex flex-col h-full w-full"
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="font-bold text-gray-800 text-lg truncate pr-2">
                                Observação
                            </h3>
                            <div
                                className="px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap uppercase tracking-wide bg-gray-100 text-gray-600"
                            >
                                Detalhes
                            </div>
                        </div>

                        {/* Pills de métricas */}
                        <div className="flex flex-wrap gap-1.5 mb-2">
                            {duracao_normal_min > 0 && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                    Normal: {duracao_normal_min} min
                                </span>
                            )}
                            {duracao_transito_min > 0 && (
                                <span
                                    className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                                    style={{
                                        backgroundColor: duracao_transito_min > duracao_normal_min ? "#fff7ed" : "#f0fdf4",
                                        color: duracao_transito_min > duracao_normal_min ? "#c2410c" : "#15803d",
                                    }}
                                >
                                    Atual: {duracao_transito_min} min
                                </span>
                            )}
                            {jam_factor_max > 0 && (
                                <span
                                    className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                                    style={{
                                        backgroundColor: jam_factor_max >= 8 ? "#fef2f2" : jam_factor_max >= 5 ? "#fff7ed" : "#f3f4f6",
                                        color: jam_factor_max >= 8 ? "#b91c1c" : jam_factor_max >= 5 ? "#c2410c" : "#6b7280",
                                    }}
                                >
                                    Jam: {jam_factor_max.toFixed(1)}
                                </span>
                            )}
                        </div>

                        {/* Texto relato multi-linha */}
                        <div className="flex-1 overflow-y-auto mb-2 pr-1 scrollbar-thin scrollbar-thumb-gray-300">
                            {relato ? (
                                <div className="text-sm border-l-2 border-gray-200 pl-3 py-1 space-y-0.5">
                                    {relato.split('\n').map((line, i) => (
                                        <p
                                            key={i}
                                            className={i === 0 ? "font-bold text-gray-800" : "text-gray-600 text-xs"}
                                        >
                                            {line}
                                        </p>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500 text-sm italic border-l-2 border-gray-200 pl-3 py-1">
                                    Nenhuma observação reportada para este trecho no momento.
                                </p>
                            )}
                        </div>

                        {/* Mini-lista de incidentes */}
                        {incidentes.length > 0 && (
                            <div className="mb-2">
                                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">
                                    Incidentes ({incidentes.length})
                                </div>
                                <div className="flex flex-col gap-1">
                                    {incidentes.slice(0, 3).map((inc, i) => {
                                        const sevCode = inc.severidade_codigo || inc.severidade;
                                        return (
                                        <div key={i} className="flex flex-col">
                                            <div className="flex items-center gap-1.5 text-[11px]">
                                                <span
                                                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                                                    style={{
                                                        background:
                                                            sevCode === "critical" ? "#ef4444" :
                                                            sevCode === "major" ? "#f97316" : "#eab308",
                                                    }}
                                                />
                                                <span className="text-gray-700 font-medium truncate">
                                                    {inc.categoria || "Incidente"}
                                                </span>
                                                {inc.rodovia_afetada && (
                                                    <span className="text-gray-500 text-[10px]">{inc.rodovia_afetada}</span>
                                                )}
                                                {inc.road_closed && (
                                                    <span className="text-[9px] font-bold px-1 py-px rounded bg-red-100 text-red-700">
                                                        FECHADA
                                                    </span>
                                                )}
                                            </div>
                                            {inc.descricao && (
                                                <span className="text-gray-400 text-[10px] truncate pl-3 block">
                                                    {inc.descricao.length > 80 ? inc.descricao.slice(0, 80) + "..." : inc.descricao}
                                                </span>
                                            )}
                                        </div>
                                        );
                                    })}
                                    {incidentes.length > 3 && (
                                        <span className="text-[10px] text-gray-400 italic">
                                            +{incidentes.length - 3} mais
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="flex justify-between items-end mt-auto pt-2 border-t border-gray-100">
                            <div />
                            <button
                                onClick={() => setIsFlipped(false)}
                                className="text-xs text-gray-400 hover:text-gray-600 font-medium flex items-center gap-1 transition-colors group"
                            >
                                <ArrowLeft size={12} className="group-hover:-translate-x-1 transition-transform" />
                                voltar
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
