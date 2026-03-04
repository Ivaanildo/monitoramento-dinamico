import React from "react";
import { useVersionCheck } from "../hooks/useVersionCheck";

export function VersionIndicator() {
  const { status, message, reload } = useVersionCheck();

  if (status === "ok") return null;

  const isUpdate = status === "update";
  const isError = status === "error";

  return (
    <div
      className="relative group flex-shrink-0"
      title={message}
      role="status"
      aria-label={message}
    >
      <button
        type="button"
        onClick={isUpdate ? reload : undefined}
        className={`
          w-2 h-2 rounded-full transition-opacity hover:opacity-100
          ${isUpdate ? "cursor-pointer" : "cursor-default"}
          ${isError ? "opacity-50" : "opacity-90"}
        `}
        style={{
          background: isUpdate ? "#fbbf24" : "#6b7280",
        }}
        aria-label={message}
      />
      <div
        className="absolute bottom-full right-0 mb-1 px-2 py-1 rounded text-xs whitespace-nowrap
          opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50
          shadow-lg"
        style={{
          background: "#111",
          border: "1px solid #444",
          color: "#e5e5e5",
        }}
      >
        {message}
        {isUpdate && " Clique para recarregar."}
      </div>
    </div>
  );
}
