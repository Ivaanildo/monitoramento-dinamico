import React, { useEffect, useRef } from "react";
import {
    MapContainer,
    TileLayer,
    Polyline,
    Tooltip,
    Marker,
    Popup,
    useMap,
} from "react-leaflet";
import L from "leaflet";
import { renderToString } from "react-dom/server";
import { AlertTriangle, HardHat, Car, CloudRain, AlertCircle } from "lucide-react";

// ─── Auto-fit bounds ──────────────────────────────────────────────────────────
function BoundsFitter({ pts }: { pts: [number, number][] }) {
    const map = useMap();
    const fitted = useRef(false);
    useEffect(() => {
        if (!fitted.current && pts.length > 1) {
            map.fitBounds(pts, { padding: [48, 48] });
            fitted.current = true;
        } else if (!fitted.current && pts.length === 1) {
            map.setView(pts[0], 13);
            fitted.current = true;
        }
    }, [map, pts]);
    return null;
}

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Incidente {
    lat?: number;
    lng?: number;
    tipo?: string;
    descricao?: string;
    severidade?: string;
    categoria?: string;
}

export interface MapViewProps {
    routePts: { lat: number; lng: number }[];
    flowPts?: { lat: number; lng: number; jam: number }[];
    status: string;
    hubOrigem?: string;
    hubDestino?: string;
    incidentes?: Incidente[];
}

// ─── Heatmap Segment Generators ────────────────────────────────────────────────
function jamColor(jam: number): string {
    if (jam >= 8) return "#ef4444"; // Intenso/Parado (Vermelho)
    if (jam >= 6) return "#f97316"; // Moderado/Pesado (Laranja)
    if (jam >= 3) return "#eab308"; // Leve (Amarelo)
    return "#22c55e"; // Livre (Verde)
}

function jamLabel(jam: number): string {
    if (jam >= 8) return "Intenso / Parado";
    if (jam >= 6) return "Moderado";
    if (jam >= 3) return "Leve";
    return "Normal";
}

function jamEmoji(jam: number): string {
    if (jam >= 8) return "🔴";
    if (jam >= 6) return "🟠";
    if (jam >= 3) return "🟡";
    return "🟢";
}

function buildSegments(latlngs: [number, number][], flowPts: { lat: number; lng: number; jam: number }[], defaultColor: string) {
    if (!flowPts || flowPts.length === 0) {
        return [{ positions: latlngs, color: defaultColor, label: "Normal", jam: 0 }];
    }

    const segments: { positions: [number, number][], color: string, label: string, jam: number }[] = [];
    if (!latlngs || latlngs.length === 0) {
        return segments;
    }

    let currentPositions: [number, number][] = [latlngs[0]];

    const getNearestFlow = (lat: number, lng: number) => {
        let bestJam = 0;
        let bestD = Infinity;
        for (const fp of flowPts) {
            const d = (fp.lat - lat) ** 2 + (fp.lng - lng) ** 2;
            if (d < bestD) {
                bestD = d;
                bestJam = fp.jam;
            }
        }
        return bestJam;
    };

    let currentJam = getNearestFlow(
        (latlngs[0][0] + (latlngs[1]?.[0] || latlngs[0][0])) / 2,
        (latlngs[0][1] + (latlngs[1]?.[1] || latlngs[0][1])) / 2
    );
    let currentColor = jamColor(currentJam);

    for (let i = 0; i < latlngs.length - 1; i++) {
        const p1 = latlngs[i];
        const p2 = latlngs[i + 1];

        const midLat = (p1[0] + p2[0]) / 2;
        const midLng = (p1[1] + p2[1]) / 2;

        const segJam = getNearestFlow(midLat, midLng);
        const segColor = jamColor(segJam);

        if (segColor === currentColor) {
            currentPositions.push(p2);
        } else {
            segments.push({ positions: currentPositions, color: currentColor, label: jamLabel(currentJam), jam: currentJam });
            currentColor = segColor;
            currentJam = segJam;
            currentPositions = [p1, p2]; // Overlap with previous point to connect smoothly
        }
    }

    if (currentPositions.length > 1) {
        segments.push({ positions: currentPositions, color: currentColor, label: jamLabel(currentJam), jam: currentJam });
    }

    return segments;
}

// ─── Icon factories ────────────────────────────────────────────────────────────
function makeDivIcon(color: string, label: string): L.DivIcon {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 42" width="32" height="42">
      <path d="M16 0C7.163 0 0 7.163 0 16c0 10 16 26 16 26s16-16 16-26C32 7.163 24.837 0 16 0z"
        fill="${color}" stroke="white" stroke-width="2"/>
      <text x="16" y="21" text-anchor="middle" fill="white" font-size="12"
        font-family="Arial,sans-serif" font-weight="bold">${label}</text>
    </svg>`;
    return L.divIcon({ html: svg, className: "", iconSize: [32, 42], iconAnchor: [16, 42], popupAnchor: [0, -44] });
}

function makeLucideIcon(inc: Incidente): L.DivIcon {
    const txt = (inc.categoria || inc.tipo || "").toLowerCase();

    let IconComp = AlertCircle;
    let color = "#ef4444";
    let shortName = "Alerta";

    if (txt.includes("interdi") || txt.includes("fechad") || txt.includes("closed")) {
        IconComp = AlertTriangle;
        color = "#991b1b";
        shortName = "Interdição";
    } else if (txt.includes("obra") || txt.includes("pista") || txt.includes("roadworks")) {
        IconComp = HardHat;
        color = "#f97316";
        shortName = "Obras";
    } else if (txt.includes("acidente") || txt.includes("colisão") || txt.includes("accident")) {
        IconComp = Car;
        color = "#ef4444";
        shortName = "Acidente";
    } else if (txt.includes("clima") || txt.includes("weather") || txt.includes("climática")) {
        IconComp = CloudRain;
        color = "#3b82f6";
        shortName = "Clima";
    } else if (txt.includes("tráfego") || txt.includes("congestion") || txt.includes("engarrafamento")) {
        IconComp = Car;
        color = "#eab308";
        shortName = "Trânsito";
    } else if (txt.includes("ocorrência")) {
        IconComp = AlertCircle;
        color = "#eab308";
        shortName = "Ocorrência";
    }

    if (inc.severidade === "critical") color = "#ef4444";
    else if (inc.severidade === "major") color = "#f97316";

    // Build the icon using modern React and Tailwind
    const iconHtml = renderToString(
        <div style={{
            display: "inline-flex", alignItems: "center", gap: "6px",
            background: "#ffffff",
            borderLeft: `4px solid ${color}`,
            borderRadius: "0 20px 20px 0",
            padding: "5px 12px 5px 8px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.28)",
            whiteSpace: "nowrap",
            fontFamily: "Arial, sans-serif"
        }}>
            <IconComp size={16} style={{ color }} strokeWidth={2.5} />
            <span style={{ fontSize: "11px", fontWeight: "bold", color }}>
                {shortName}
            </span>
        </div>
    );

    return L.divIcon({
        html: iconHtml,
        className: "bg-transparent border-none",
        iconAnchor: [0, 16],
        popupAnchor: [0, -20]
    });
}

function statusColor(s: string): string {
    if (s === "Intenso" || s === "Parado") return "#ef4444";
    if (s === "Moderado") return "#f97316";
    if (s === "Erro" || s === "Sem dados" || s === "N/A") return "#3b82f6"; // Blue offline default
    return "#22c55e";
}

export interface MapViewProps {
    routePts?: any[]; // Allow any, so we can parse objects or arrays
    flowPts?: { lat: number; lng: number; jam: number }[];
    status: string;
    hubOrigem: string;
    hubDestino: string;
    incidentes?: any[];
    viaCoords?: { lat: number; lng: number }[];
}

export function MapView({ routePts = [], flowPts = [], status, hubOrigem, hubDestino, incidentes = [], viaCoords = [] }: MapViewProps) {
    // Parse route points robustly (Python might send [[lat, lng], ...])
    const latlngs: [number, number][] = routePts.map((p: any) => {
        if (Array.isArray(p)) return [p[0], p[1]] as [number, number];
        return [p.lat, p.lng] as [number, number];
    }).filter(ll => ll[0] !== undefined && ll[1] !== undefined);

    // default center: Brazil
    const center: [number, number] = latlngs.length > 0
        ? latlngs[Math.floor(latlngs.length / 2)]
        : [-15.7, -47.9];

    const defaultColor = statusColor(status);
    const originPt = latlngs[0];
    const destPt = latlngs[latlngs.length - 1];

    // Build the segments using heatmap logic
    const segments = buildSegments(latlngs, flowPts, defaultColor);

    // Icons created at render time
    const originIcon = makeDivIcon("#22c55e", "O");
    const destIcon = makeDivIcon("#ef4444", "D");

    return (
        <MapContainer
            center={center}
            zoom={latlngs.length === 0 ? 5 : 12}
            style={{ height: "100%", width: "100%", borderRadius: "0.75rem" }}
            zoomControl={true}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            {latlngs.length > 1 && (
                <>
                    <BoundsFitter pts={latlngs} />

                    {/* Shadow outline */}
                    <Polyline
                        positions={latlngs}
                        pathOptions={{ color: "#000", weight: 8, opacity: 0.15 }}
                    />

                    {/* Segmented active heatmapping */}
                    {segments.map((seg, idx) => (
                        <Polyline
                            key={idx}
                            positions={seg.positions}
                            pathOptions={{ color: seg.color, weight: 5, opacity: 0.85 }}
                        >
                            <Tooltip sticky>
                                <div style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", lineHeight: "1.5" }}>
                                    <strong style={{ color: seg.color }}>{jamEmoji(seg.jam)} {seg.label}</strong>
                                    <div style={{ color: "#555" }}>Jam Factor: {seg.jam.toFixed(1)} / 10</div>
                                </div>
                            </Tooltip>
                        </Polyline>
                    ))}
                </>
            )}

            {originPt && (
                <Marker position={originPt} icon={originIcon}>
                    <Popup>{hubOrigem || "Origem"}</Popup>
                </Marker>
            )}

            {viaCoords && viaCoords.map((pt, idx) => (
                <Marker key={`via-${idx}`} position={[pt.lat, pt.lng]} icon={makeDivIcon("#9ca3af", `${idx + 1}`)}>
                    <Popup>Ponto Intermediário {idx + 1}</Popup>
                </Marker>
            ))}

            {destPt && originPt && destPt[0] !== originPt[0] && (
                <Marker position={destPt} icon={destIcon}>
                    <Popup>{hubDestino || "Destino"}</Popup>
                </Marker>
            )}

            {incidentes.map((inc, i) => {
                const lat = (inc as { lat?: number; latitude?: number }).lat ?? (inc as { latitude?: number }).latitude;
                const lng = (inc as { lng?: number; longitude?: number }).lng ?? (inc as { longitude?: number }).longitude;
                if (!lat || !lng) return null;
                const incIcon = makeLucideIcon(inc);
                return (
                    <Marker key={i} position={[lat, lng]} icon={incIcon}>
                        <Popup>
                            <strong>{inc.tipo || "Incidente"}</strong>
                            {inc.descricao && <><br />{inc.descricao}</>}
                            <div className="text-xs text-gray-500 mt-2 uppercase tracking-wide font-bold">
                                {inc.categoria || "Aviso"}
                            </div>
                        </Popup>
                    </Marker>
                );
            })}
        </MapContainer>
    );
}
