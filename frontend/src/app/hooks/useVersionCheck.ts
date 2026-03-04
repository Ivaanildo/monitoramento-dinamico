import { useState, useEffect, useCallback } from "react";

export type VersionStatus = "ok" | "update" | "error";

interface VersionState {
  status: VersionStatus;
  message?: string;
}

const CHECK_INTERVAL_MS = 5 * 60 * 1000; // 5 min

export function useVersionCheck() {
  const [state, setState] = useState<VersionState>({ status: "ok" });
  const [initialBuildTime, setInitialBuildTime] = useState<number | null>(null);

  const check = useCallback(async () => {
    try {
      const res = await fetch("/version.json?t=" + Date.now(), {
        cache: "no-store",
        headers: { "Cache-Control": "no-cache" },
      });
      if (!res.ok) throw new Error("Version check failed");
      const data = (await res.json()) as { buildTime?: number };
      const buildTime = Number(data?.buildTime ?? 0);

      if (initialBuildTime === null) {
        setInitialBuildTime(buildTime);
        setState({ status: "ok" });
        return;
      }

      if (buildTime > initialBuildTime) {
        setState({
          status: "update",
          message: "Nova versão disponível. Recarregue a página.",
        });
      } else {
        setState({ status: "ok" });
      }
    } catch {
      setState({
        status: "error",
        message: "Verificação de atualização indisponível",
      });
    }
  }, [initialBuildTime]);

  useEffect(() => {
    check();
  }, []);

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "visible") check();
    };
    document.addEventListener("visibilitychange", onVisibility);
    const interval = setInterval(check, CHECK_INTERVAL_MS);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      clearInterval(interval);
    };
  }, [check]);

  return { ...state, reload: () => window.location.reload() };
}
