import { useEffect, useMemo, useState } from "react";
import { getSimulate, SimulateTimelinePoint } from "../api/client";
import { TrafficLight } from "./TrafficLight";
import { RSLCountdown } from "./RSLCountdown";
import { SensorChart, ChartPoint } from "./SensorChart";
import { EnvironmentControls } from "./EnvironmentControls";
import { motion } from "framer-motion";
import { FastForward, AlertCircle, RefreshCw } from "lucide-react";

export function TimeSlider() {
  const [tempC, setTempC] = useState(22);
  const [rh, setRh] = useState(70);
  const [ripe, setRipe] = useState(2.0);
  const [hours, setHours] = useState(24 * 14);
  const [timeline, setTimeline] = useState<SimulateTimelinePoint[]>([]);
  const [pos, setPos] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSim() {
    setLoading(true); setError(null);
    try {
      const r = await getSimulate({ temp_c: tempC, humidity_pct: rh, hours, initial_ripeness: ripe });
      setTimeline(r.timeline);
      setPos(0);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { runSim(); /* eslint-disable-next-line */ }, []);

  const chartData: ChartPoint[] = useMemo(
    () =>
      timeline.slice(0, pos + 1).map((p) => ({
        t_hours: p.t_hours,
        temp_c: p.temp_c,
        humidity_pct: p.humidity_pct,
        co2_ppm: p.co2_ppm,
        ethylene_ppm: p.ethylene_ppm,
        rsl_days: p.rsl_days,
      })),
    [timeline, pos]
  );

  const current = timeline[pos] ?? null;

  const rows = [
    { label: "Temperature", value: tempC, setValue: setTempC, min: -5, max: 40, step: 0.5, unit: "°C" },
    { label: "Humidity", value: rh, setValue: setRh, min: 30, max: 100, step: 1, unit: "%" },
    { label: "Initial ripeness", value: ripe, setValue: setRipe, min: 1, max: 5, step: 0.1, unit: "" },
    { label: "Time Horizon", value: hours, setValue: setHours, min: 24, max: 24 * 30, step: 24, unit: "h" },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 flex flex-col border border-white/10"
      >
        <div className="mb-6 flex items-center gap-3 border-b border-white/10 pb-4">
          <FastForward className="h-5 w-5 text-bss-cyan" />
          <h3 className="text-xl font-bold text-white tracking-tight">Timeline Simulation</h3>
        </div>

        <EnvironmentControls rows={rows} />
        
        <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-6">
          <div className="flex-1">
            {error && (
              <div className="flex items-center gap-2 text-sm text-bss-red font-medium">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>
          <button
            onClick={runSim}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-bss-accent px-6 py-3 font-bold text-white hover:bg-bss-accent/90 disabled:opacity-50 transition-colors shadow-[0_0_15px_rgba(59,130,246,0.3)]"
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <FastForward className="h-5 w-5 fill-current" />
            )}
            {loading ? "Generating Timeline..." : "Generate Timeline"}
          </button>
        </div>

        <div className="mt-8 flex-1 min-h-[300px]">
          <SensorChart data={chartData} />
        </div>

        <div className="mt-8 bg-black/20 p-6 rounded-xl border border-white/5">
          <div className="relative h-2 rounded-full bg-gray-800 overflow-hidden mb-4">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-bss-cyan to-bss-accent transition-all duration-100"
              style={{ width: `${(pos / Math.max(1, timeline.length - 1)) * 100}%` }}
            />
            <input
              type="range"
              min={0}
              max={Math.max(0, timeline.length - 1)}
              step={1}
              value={pos}
              onChange={(e) => setPos(Number(e.target.value))}
              className="absolute inset-0 w-full opacity-0 cursor-pointer"
            />
          </div>
          <div className="flex justify-between text-xs font-mono font-bold tracking-wider uppercase text-bss-muted">
            <span className="text-white">Start</span>
            <span className="text-bss-cyan px-3 py-1 bg-bss-cyan/10 rounded-full border border-bss-cyan/20">
              Current: {current ? current.t_hours.toFixed(1) : 0}h
            </span>
            <span className="text-white">+{(hours / 24).toFixed(0)}d End</span>
          </div>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col gap-6"
      >
        <div className="glass rounded-2xl p-6 flex flex-col items-center border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
          <h3 className="text-xs font-semibold text-bss-muted uppercase tracking-widest mb-6 w-full text-center">Snapshot Status</h3>
          
          <TrafficLight status={current?.status ?? null} />
          
          <div className="w-full mt-8 mb-4">
            <RSLCountdown rslDays={current?.rsl_days ?? null} status={current?.status ?? null} />
          </div>

          {current && (
            <div className="mt-4 w-full grid grid-cols-3 gap-2">
              <div className="flex flex-col items-center p-2 rounded-lg bg-white/5 border border-white/5">
                <span className="text-[10px] text-bss-muted uppercase tracking-widest font-bold mb-1">Temp</span>
                <span className="text-xs font-mono text-white">{current.temp_c.toFixed(1)}°</span>
              </div>
              <div className="flex flex-col items-center p-2 rounded-lg bg-white/5 border border-white/5">
                <span className="text-[10px] text-bss-muted uppercase tracking-widest font-bold mb-1">RH</span>
                <span className="text-xs font-mono text-white">{current.humidity_pct.toFixed(0)}%</span>
              </div>
              <div className="flex flex-col items-center p-2 rounded-lg bg-white/5 border border-white/5">
                <span className="text-[10px] text-bss-muted uppercase tracking-widest font-bold mb-1">CO₂</span>
                <span className="text-xs font-mono text-white">{current.co2_ppm.toFixed(0)}</span>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
