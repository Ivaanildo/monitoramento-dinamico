import React from "react";
import { motion } from "motion/react";

interface GaugeChartProps {
  value: number;
  max: number;
  color: string;
  title: string;
  trackColor?: string;
}

export function GaugeChart({
  value,
  max,
  color,
  title,
  trackColor = "#e2e8f0",
}: GaugeChartProps) {
  const cx = 100;
  const cy = 92;
  const radius = 65;
  const percentage = max > 0 ? Math.min(value / max, 1) : 0;

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const getPoint = (angleDeg: number) => {
    const angle = toRad(angleDeg);
    return {
      x: cx + radius * Math.cos(angle),
      y: cy - radius * Math.sin(angle),
    };
  };

  const startPoint = getPoint(180);
  const endPoint = getPoint(0);
  const gaugePath = `M ${startPoint.x} ${startPoint.y} A ${radius} ${radius} 0 0 1 ${endPoint.x} ${endPoint.y}`;
  const arcLength = Math.PI * radius;
  const activeAngle = 180 - percentage * 180;
  const activePoint = getPoint(activeAngle);

  return (
    <div className="surface-panel rounded-[30px] p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Distribuicao</p>
          <h3 className="mt-2 text-base font-semibold tracking-[-0.02em] text-slate-950">{title}</h3>
        </div>
        <span className="rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em]" style={{ background: `${color}18`, color }}>
          {Math.round(percentage * 100)}%
        </span>
      </div>

      <div className="mt-5 flex items-center justify-center">
        <svg viewBox="20 16 160 100" className="w-full max-w-[240px]">
          <path d={gaugePath} fill="none" stroke={trackColor} strokeWidth="14" strokeLinecap="round" />

          <motion.path
            d={gaugePath}
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset: arcLength * (1 - percentage) }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          />

          <circle cx={activePoint.x} cy={activePoint.y} r="6.5" fill={color} />

          <text
            x={cx}
            y={cy + 6}
            textAnchor="middle"
            fill="#0f172a"
            fontSize="30"
            fontWeight="800"
            style={{ letterSpacing: "-0.04em" }}
          >
            {value}
          </text>
          <text
            x={cx}
            y={cy + 24}
            textAnchor="middle"
            fill="#64748b"
            fontSize="11"
            fontWeight="600"
            style={{ letterSpacing: "0.12em", textTransform: "uppercase" }}
          >
            de {max}
          </text>
        </svg>
      </div>
    </div>
  );
}
