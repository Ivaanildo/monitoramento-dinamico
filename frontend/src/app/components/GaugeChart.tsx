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
  trackColor = "#444",
}: GaugeChartProps) {
  const cx = 100;
  const cy = 90;
  const r = 65;

  const toRad = (deg: number) => (deg * Math.PI) / 180;

  const getPt = (angleDeg: number) => {
    const a = toRad(angleDeg);
    return {
      x: cx + r * Math.cos(a),
      y: cy - r * Math.sin(a),
    };
  };

  // Background: full semicircle from 180° to 0°
  const bgStart = getPt(180);
  const bgEnd = getPt(0);
  const bgPath = `M ${bgStart.x} ${bgStart.y} A ${r} ${r} 0 0 1 ${bgEnd.x} ${bgEnd.y}`;

  // Real arc length of the semicircle
  const arcLength = Math.PI * r;

  const percentage = max > 0 ? Math.min(value / max, 1) : 0;

  // Needle/dot at the end of value arc
  const endAngleDeg = 180 - percentage * 180;
  const valEnd = getPt(endAngleDeg);
  const needleX = percentage < 0.005 ? bgStart.x : valEnd.x;
  const needleY = percentage < 0.005 ? bgStart.y : valEnd.y;

  return (
    <div
      className="rounded-xl overflow-hidden shadow-lg flex flex-col"
      style={{
        background: "#2a2a2a",
        border: "2px solid #FFD700",
      }}
    >
      {/* Title */}
      <div
        className="px-4 py-2 text-center"
        style={{
          background: "#1e1e1e",
          borderBottom: "2px solid #FFD700",
        }}
      >
        <span
          className="text-sm font-bold tracking-wide"
          style={{ color: "#FFD700" }}
        >
          {title}
        </span>
      </div>

      {/* Gauge SVG */}
      <div className="flex-1 flex items-center justify-center p-4">
        <svg
          viewBox="20 20 160 90"
          className="w-full"
          style={{ maxWidth: 240 }}
        >
          {/* Background track */}
          <path
            d={bgPath}
            fill="none"
            stroke={trackColor}
            strokeWidth="14"
            strokeLinecap="round"
          />

          {/* Value arc */}
          <motion.path
            d={bgPath}
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset: arcLength * (1 - percentage) }}
            transition={{ duration: 1, ease: "easeOut" }}
          />

          {/* End dot */}
          {percentage >= 0.005 && (
            <circle cx={needleX} cy={needleY} r="7" fill={color} />
          )}

          {/* Center value */}
          <text
            x={cx}
            y={cy + 8}
            textAnchor="middle"
            fill="white"
            fontSize="26"
            fontWeight="bold"
            fontFamily="monospace"
          >
            {value}
          </text>
        </svg>
      </div>
    </div>
  );
}
