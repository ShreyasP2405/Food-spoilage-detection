import { useMemo, useState } from "react";
import { Play, Square, RotateCcw, Activity } from "lucide-react";
import { useStream } from "../hooks/useWebSocket";
import { TrafficLight } from "./TrafficLight";
import { RSLCountdown } from "./RSLCountdown";
import { SensorChart, ChartPoint } from "./SensorChart";
import { EnvironmentControls } from "./EnvironmentControls";
import { SensorCard } from "./SensorCard";
import { motion } from "framer-motion";
import { Droplets, Thermometer, Wind, Zap } from "lucide-react";

export function SimulationPanel() {
  const [tempC, setTempC] = useState(22);
  const [rh, setRh] = useState(70);
  const [ripe, setRipe] = useState(2.0);
  const [running, setRunning] = useState(false);

  const { frames, latest, connected, reset } = useStream({
    enabled: running,
    temp_c: tempC,
    humidity_pct: rh,
    initial_ripeness: ripe,
  });

  const chartData: ChartPoint[] = useMemo(
    () =>
      frames.map((f) => ({
        t_hours: f.reading.timestamp_h,
        temp_c: f.reading.temp_c,
        humidity_pct: f.reading.humidity_pct,
        co2_ppm: f.reading.co2_ppm,
        ethylene_ppm: f.reading.ethylene_ppm,
        methane_ppm: f.reading.methane_ppm,
        rsl_days: f.prediction.rsl_days,
      })),
    [frames]
  );

  const rows = [
    { label: "Temperature", value: tempC, setValue: setTempC, min: -5, max: 40, step: 0.5, unit: "°C" },
    { label: "Humidity", value: rh, setValue: setRh, min: 30, max: 100, step: 1, unit: "%" },
    { label: "Initial ripeness", value: ripe, setValue: setRipe, min: 1, max: 5, step: 0.1, unit: "" },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Live Sensors Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SensorCard 
          label="Temperature" 
          value={latest?.reading.temp_c ?? tempC} 
          unit="°C" 
          icon={Thermometer} 
          colorClass="text-bss-red" 
        />
        <SensorCard 
          label="Humidity" 
          value={latest?.reading.humidity_pct ?? rh} 
          unit="%" 
          icon={Droplets} 
          colorClass="text-bss-accent" 
        />
        <SensorCard 
          label="CO₂ Level" 
          value={latest?.reading.co2_ppm ?? 400} 
          unit="ppm" 
          icon={Wind} 
          colorClass="text-bss-muted" 
          trend={running ? "up" : "stable"}
        />
        <SensorCard 
          label="Ethylene" 
          value={latest?.reading.ethylene_ppm ?? 0.1} 
          unit="ppm" 
          icon={Zap} 
          colorClass="text-bss-yellow" 
          trend={running ? "up" : "stable"}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* Main Simulation Area */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6 flex flex-col border border-white/10"
        >
          <div className="mb-6 flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-bss-cyan" />
              <h3 className="text-xl font-bold text-white tracking-tight">Live Simulation Hub</h3>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-black/30 rounded-full border border-white/5">
              <span className={`relative flex h-2.5 w-2.5 ${connected ? '' : 'hidden'}`}>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bss-green opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-bss-green"></span>
              </span>
              <span className={`h-2.5 w-2.5 rounded-full ${!connected ? 'bg-bss-muted' : 'hidden'}`}></span>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${connected ? "text-bss-green" : "text-bss-muted"}`}>
                {connected ? "Receiving Data" : "Idle"}
              </span>
            </div>
          </div>

          <EnvironmentControls rows={rows} />

          <div className="mt-8 flex gap-3">
            {!running ? (
              <button
                onClick={() => { reset(); setRunning(true); }}
                className="flex-1 flex justify-center items-center gap-2 rounded-xl bg-bss-green/20 border border-bss-green/50 px-4 py-3 font-bold text-bss-green hover:bg-bss-green/30 transition-colors shadow-[0_0_15px_rgba(34,197,94,0.1)] hover:shadow-[0_0_20px_rgba(34,197,94,0.2)]"
              >
                <Play className="h-5 w-5 fill-current" /> Start Simulation
              </button>
            ) : (
              <button
                onClick={() => setRunning(false)}
                className="flex-1 flex justify-center items-center gap-2 rounded-xl bg-bss-red/20 border border-bss-red/50 px-4 py-3 font-bold text-bss-red hover:bg-bss-red/30 transition-colors shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_20px_rgba(239,68,68,0.2)]"
              >
                <Square className="h-5 w-5 fill-current" /> Stop Simulation
              </button>
            )}
            <button
              onClick={reset}
              className="flex justify-center items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-6 py-3 font-bold text-white hover:bg-white/10 transition-colors"
            >
              <RotateCcw className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-8 flex-1 min-h-[300px]">
            <SensorChart data={chartData} />
          </div>
        </motion.div>

        {/* Status Area */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex flex-col gap-6"
        >
          <div className="glass rounded-2xl p-6 flex flex-col items-center border border-white/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
            <h3 className="text-xs font-semibold text-bss-muted uppercase tracking-widest mb-6 w-full text-center">Live Spoilage Status</h3>
            
            <TrafficLight status={latest?.prediction.status ?? null} />
            
            <div className="w-full mt-8 mb-4">
              <RSLCountdown
                rslDays={latest?.prediction.rsl_days ?? null}
                status={latest?.prediction.status ?? null}
              />
            </div>

            {latest?.prediction.reason && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 w-full rounded-xl bg-black/40 border border-white/5 p-4 text-center text-sm text-bss-text font-medium shadow-inner"
              >
                {latest.prediction.reason}
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}