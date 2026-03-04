import React from "react";

interface StatusTickerProps {
  messages: string[];
}

function segmentStyle(msg: string): { bg: string; color: string } {
  const m = msg.toUpperCase();
  if (m.includes("INTENSO")) return { bg: "rgba(239, 68, 68, 0.2)", color: "#fbbf24" };
  if (m.includes("MODERADO")) return { bg: "rgba(249, 115, 22, 0.2)", color: "#fbbf24" };
  if (m.includes("FLUXO NORMAL") || m.includes("NORMAL")) return { bg: "rgba(34, 197, 94, 0.15)", color: "#86efac" };
  return { bg: "rgba(107, 114, 128, 0.15)", color: "#e5e5e5" };
}

export function StatusTicker({ messages }: StatusTickerProps) {
  const isAlert = messages.some((m) => m.includes("INTENSO") || m.includes("moderado"));

  return (
    <div
      className="flex items-center overflow-hidden"
      style={{
        background: "#111",
        borderTop: "1px solid #333",
        borderBottom: "1px solid #333",
        height: 36,
      }}
    >
      {/* Status icon */}
      <div
        className="flex-shrink-0 flex items-center gap-2 px-3 h-full border-r border-gray-700"
        style={{ background: "#0f0f0f" }}
      >
        <div
          className="w-5 h-5 rounded-sm flex items-center justify-center"
          style={{
            background: isAlert ? "#f97316" : "#22c55e",
            border: `2px solid ${isAlert ? "#ea580c" : "#16a34a"}`,
          }}
        >
          <svg width="12" height="10" viewBox="0 0 12 10" fill="none">
            <path
              d="M1 5L4.5 8.5L11 1"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* Scrolling wrapper */}
      <div className="overflow-hidden flex-1 h-full flex items-center">
        <div className="ticker-wrapper">
          <span className="ticker-text" style={{ fontFamily: "monospace", fontSize: 13, letterSpacing: "0.05em" }}>
            {messages.map((msg, i) => {
              const { bg, color } = segmentStyle(msg);
              return (
                <React.Fragment key={i}>
                  {i > 0 && <span className="ticker-sep"> ✦ </span>}
                  <span
                    className="ticker-segment"
                    style={{
                      background: bg,
                      color,
                      padding: "2px 8px",
                      borderRadius: 4,
                      marginRight: 4,
                    }}
                  >
                    {msg}
                  </span>
                </React.Fragment>
              );
            })}
          </span>
        </div>
      </div>

      <style>{`
        .ticker-wrapper {
          display: flex;
          width: 100%;
          overflow: hidden;
        }
        .ticker-text {
          display: inline-flex;
          align-items: center;
          white-space: nowrap;
          animation: ticker-scroll 60s linear infinite;
          padding-left: 100%;
        }
        .ticker-segment {
          display: inline-block;
        }
        .ticker-sep {
          color: #6b7280;
          margin: 0 4px;
        }
        @keyframes ticker-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-100%); }
        }
      `}</style>
    </div>
  );
}
