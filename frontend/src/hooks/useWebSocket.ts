import { useEffect, useRef, useState } from "react";

export interface StreamFrame {
  reading: {
    timestamp_h: number;
    temp_c: number;
    humidity_pct: number;
    co2_ppm: number;
    ethylene_ppm: number;
    methane_ppm: number;
    hours_since_harvest: number;
    ripeness_estimate: number;
  };
  prediction: {
    rsl_days: number;
    status: "green" | "yellow" | "red";
    reason: string;
    confidence: number;
    model_version: string;
    contributing_factors: { name: string; severity: string; detail: string }[];
  };
}

export function useStream(opts: {
  enabled: boolean;
  temp_c: number;
  humidity_pct: number;
  initial_ripeness: number;
}) {
  const [frames, setFrames] = useState<StreamFrame[]>([]);
  const [latest, setLatest] = useState<StreamFrame | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!opts.enabled) {
      wsRef.current?.close();
      wsRef.current = null;
      setConnected(false);
      return;
    }
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${window.location.host}/ws/stream?temp_c=${opts.temp_c}&humidity_pct=${opts.humidity_pct}&initial_ripeness=${opts.initial_ripeness}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const f = JSON.parse(ev.data) as StreamFrame;
        setLatest(f);
        setFrames((prev) => {
          const next = [...prev, f];
          if (next.length > 200) next.shift();
          return next;
        });
      } catch (_) {
        /* ignore */
      }
    };
    return () => {
      ws.close();
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.enabled, opts.temp_c, opts.humidity_pct, opts.initial_ripeness]);

  function reset() {
    setFrames([]);
    setLatest(null);
  }

  return { frames, latest, connected, reset };
}
