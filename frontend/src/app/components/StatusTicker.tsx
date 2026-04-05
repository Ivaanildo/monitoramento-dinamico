import React from "react";
import { RadioTower } from "lucide-react";

interface StatusTickerProps {
  messages: string[];
}

function segmentStyle(message: string): { background: string; color: string } {
  const normalized = message.toUpperCase();

  if (normalized.includes("PARADO") || normalized.includes("INTENSO")) {
    return { background: "rgba(220, 38, 38, 0.12)", color: "#b91c1c" };
  }
  if (normalized.includes("MODERADO")) {
    return { background: "rgba(249, 115, 22, 0.12)", color: "#c2410c" };
  }
  if (normalized.includes("NORMAL")) {
    return { background: "rgba(34, 197, 94, 0.12)", color: "#15803d" };
  }

  return { background: "rgba(15, 23, 42, 0.08)", color: "#475569" };
}

export function StatusTicker({ messages }: StatusTickerProps) {
  const loopMessages = messages.length > 1 ? [...messages, ...messages] : messages;
  const duration = Math.max(26, loopMessages.join(" ").length / 4.5);

  return (
    <div className="glass-panel flex items-center overflow-hidden rounded-[26px] px-3 py-2">
      <div className="flex flex-shrink-0 items-center gap-3 rounded-full bg-slate-950 px-4 py-2 text-white shadow-[0_12px_24px_rgba(15,23,42,0.16)]">
        <span className="relative flex h-3 w-3 items-center justify-center">
          <span className="absolute inline-flex h-3 w-3 animate-ping rounded-full bg-emerald-400/70" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
        </span>
        <RadioTower className="h-4 w-4" />
        <span className="text-[11px] font-bold uppercase tracking-[0.18em]">Radar dinamico</span>
      </div>

      <div className="ml-3 flex-1 overflow-hidden">
        <div className="ticker-track">
          <div className="ticker-inner" style={{ animationDuration: `${duration}s` }}>
            {loopMessages.map((message, index) => {
              const style = segmentStyle(message);
              return (
                <React.Fragment key={`${message}-${index}`}>
                  <span className="ticker-separator">+</span>
                  <span className="ticker-pill" style={{ background: style.background, color: style.color }}>
                    {message}
                  </span>
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      <style>{`
        .ticker-track {
          display: flex;
          width: 100%;
          overflow: hidden;
        }

        .ticker-inner {
          display: inline-flex;
          align-items: center;
          white-space: nowrap;
          will-change: transform;
          padding-left: 100%;
          animation: monitoramento-ticker linear infinite;
        }

        .ticker-pill {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 0.45rem 0.85rem;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          margin-right: 0.45rem;
        }

        .ticker-separator {
          color: #94a3b8;
          font-size: 0.75rem;
          font-weight: 800;
          margin: 0 0.4rem 0 0.1rem;
        }

        @keyframes monitoramento-ticker {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-100%);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .ticker-inner {
            animation: none !important;
            padding-left: 0;
            flex-wrap: wrap;
          }
        }
      `}</style>
    </div>
  );
}
