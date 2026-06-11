import { useState } from "react";
import { TrafficLight } from "./TrafficLight";
import { RSLCountdown } from "./RSLCountdown";
import { EnvironmentControls } from "./EnvironmentControls";
import { usePrediction } from "../hooks/usePrediction";
import { motion } from "framer-motion";
import { Activity, AlertCircle } from "lucide-react";

export function ManualInputPanel() {
  const [tempC, setTempC] = useState(22);
  const [rh, setRh] = useState(70);
  const [co2, setCo2] = useState(1500);
  const [eth, setEth] = useState(1.5);
  const [ch4, setCh4] = useState(0);
  const [hours, setHours] = useState(96);
  const [ripe, setRipe] = useState(3);

  const { result, loading, error, predict } = usePrediction();

  const onPredict = () =>
    predict({
      temp_c: tempC,
      humidity_pct: rh,
      co2_ppm: co2,
      ethylene_ppm: eth,
      methane_ppm: ch4,
      hours_since_harvest: hours,
      ripeness_estimate: ripe,
    });

  const rows = [
    { label: "Temperature", hint: "Optimal 13-14°C; chilling injury below 13°C", value: tempC, setValue: setTempC, min: -5, max: 40, step: 0.5, unit: "°C" },
    { label: "Humidity", hint: "Optimal 90-95% RH", value: rh, setValue: setRh, min: 30, max: 100, step: 1, unit: "%" },
    { label: "CO₂", hint: "Rises during respiration; toxic above 70,000 ppm", value: co2, setValue: setCo2, min: 300, max: 10000, step: 50, unit: "ppm" },
    { label: "Ethylene", hint: "Climacteric peak ~7.4 µL/kg/h ripe banana", value: eth, setValue: setEth, min: 0, max: 50, step: 0.1, unit: "ppm" },
    { label: "Methane", hint: "Anaerobic decomposition byproduct", value: ch4, setValue: setCh4, min: 0, max: 100, step: 0.1, unit: "ppm" },
    { label: "Harvest Age", value: hours, setValue: setHours, min: 0, max: 720, step: 1, unit: "h" },
    { label: "Ripeness (1-7)", hint: "1 (all green) … 7 (overripe)", value: ripe, setValue: setRipe, min: 1, max: 7, step: 1, unit: "" },
  ];

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_400px]">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6 relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-bss-accent to-bss-cyan" />
        <div className="flex items-center gap-3 mb-6">
          <Activity className="h-5 w-5 text-bss-cyan" />
          <h3 className="text-xl font-bold tracking-tight text-white">Environment Sensors</h3>
        </div>
        
        <EnvironmentControls rows={rows} />
        
        <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-6">
          <div className="flex-1">
            {error && (
              <div className="flex items-center gap-2 text-sm text-bss-red font-medium">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onPredict}
            disabled={loading}
            className="relative overflow-hidden group rounded-xl px-8 py-3 font-bold text-white shadow-lg bg-bss-accent hover:bg-bss-accent/90 disabled:opacity-50 transition-colors"
          >
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out" />
            <span className="relative flex items-center gap-2">
              {loading ? (
                <>
                  <span className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                  Analyzing...
                </>
              ) : (
                "Run Prediction Model"
              )}
            </span>
          </motion.button>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
        className="flex flex-col gap-6"
      >
        <div className="glass rounded-2xl p-6 relative overflow-hidden flex flex-col items-center border border-white/10">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
          <h3 className="text-sm font-semibold text-bss-muted uppercase tracking-widest mb-6 w-full text-center">Prediction Results</h3>
          
          <TrafficLight status={result?.status ?? null} />
          
          <div className="w-full mt-8 mb-4">
            <RSLCountdown rslDays={result?.rsl_days ?? null} status={result?.status ?? null} />
          </div>

          {result?.reason && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 w-full rounded-xl bg-black/40 border border-white/5 p-4 text-center text-sm text-bss-text font-medium leading-relaxed shadow-inner"
            >
              {result.reason}
            </motion.div>
          )}
        </div>

        {result && result.contributing_factors.length > 0 && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass rounded-2xl p-5 border border-white/5"
          >
            <h4 className="text-xs font-semibold text-bss-muted uppercase tracking-widest mb-4">AI Insights</h4>
            <ul className="w-full space-y-2">
              {result.contributing_factors.map((f) => (
                <li key={f.name} className="flex justify-between items-center gap-3 rounded-lg bg-black/30 border border-white/5 px-3 py-2 group hover:bg-black/40 transition-colors">
                  <span className="font-mono text-xs text-bss-text group-hover:text-white transition-colors">{f.name}</span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      f.severity === "critical"
                        ? "bg-bss-red/10 text-bss-red border border-bss-red/20"
                        : f.severity === "warning"
                        ? "bg-bss-yellow/10 text-bss-yellow border border-bss-yellow/20"
                        : "bg-bss-accent/10 text-bss-accent border border-bss-accent/20"
                    }`}
                  >
                    {f.severity}
                  </span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
