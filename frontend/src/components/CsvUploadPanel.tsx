import { useEffect, useMemo, useRef, useState } from "react";
import { Upload, FileSpreadsheet, Download, AlertCircle, CheckCircle2, ChevronRight, Activity, Play, Square, RotateCcw } from "lucide-react";
import { postPredictCsv, CsvPredictionResponse, CsvPredictionRow, Status } from "../api/client";
import { TrafficLight } from "./TrafficLight";
import { RSLCountdown } from "./RSLCountdown";
import { SensorChart, ChartPoint } from "./SensorChart";
import { motion, AnimatePresence } from "framer-motion";

const STATUS_COLOR: Record<Status, string> = {
  green: "text-bss-green",
  yellow: "text-bss-yellow",
  red: "text-bss-red",
};

export function CsvUploadPanel() {
  const [result, setResult] = useState<CsvPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentIndex(0);
    setIsPlaying(false);
    try {
      const r = await postPredictCsv(file);
      setResult(r);
      setCurrentIndex(0);
      setIsPlaying(true); // Auto-start simulation
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
    } finally {
      setLoading(false);
    }
  }

  function downloadAnnotated() {
    if (!result) return;
    const blob = new Blob([result.annotated_csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `annotated_${result.filename}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Simulation logic
  useEffect(() => {
    if (!isPlaying || !result) return;
    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= result.rows.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1000); // 1 second per tick
    return () => clearInterval(interval);
  }, [isPlaying, result]);

  const selectedRow = result?.rows[currentIndex] ?? null;

  const chartData: ChartPoint[] = useMemo(() => {
    if (!result) return [];
    return [...result.rows.slice(0, currentIndex + 1)]
      .sort((a, b) => a.hours_since_harvest - b.hours_since_harvest)
      .map((r) => ({
        t_hours: r.hours_since_harvest,
        temp_c: r.temp_c,
        humidity_pct: r.humidity_pct,
        co2_ppm: r.co2_ppm,
        ethylene_ppm: r.ethylene_ppm,
        methane_ppm: r.methane_ppm,
        rsl_days: r.predicted_rsl_days,
      }));
  }, [result, currentIndex]);

  const totalCount = result ? result.status_counts.green + result.status_counts.yellow + result.status_counts.red : 0;
  const pct = (n: number) => (totalCount ? ((n / totalCount) * 100).toFixed(1) : "0.0");

  return (
    <div className="flex flex-col gap-6">
      <AnimatePresence mode="wait">
        {!result && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const f = e.dataTransfer.files?.[0];
              if (f) handleFile(f);
            }}
            className={`glass rounded-2xl border-2 p-16 text-center transition-all duration-300 ${
              drag ? "border-bss-cyan bg-bss-cyan/10" : "border-dashed border-white/20 hover:border-white/40 hover:bg-white/5"
            }`}
          >
            <motion.div 
              animate={{ y: drag ? -10 : 0, scale: drag ? 1.1 : 1 }}
              className="mx-auto mb-6 h-20 w-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-bss-cyan border-t-transparent" />
              ) : (
                <Upload className={`h-8 w-8 ${drag ? "text-bss-cyan" : "text-bss-muted"}`} />
              )}
            </motion.div>
            <h3 className="mb-2 text-2xl font-bold tracking-tight text-white">Upload Batch Sensor Data</h3>
            <p className="mx-auto mb-8 max-w-lg text-sm text-bss-muted leading-relaxed">
              Drag and drop your CSV file here. The AI engine will process multiple readings simultaneously to predict remaining shelf life and classification status.
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="rounded-xl bg-bss-accent px-8 py-3 font-bold text-white shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] hover:bg-bss-accent/90 disabled:opacity-50 transition-all"
              disabled={loading}
            >
              {loading ? "Processing Dataset..." : "Browse Files"}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-4 rounded-xl bg-bss-red/10 p-5 text-bss-red ring-1 ring-bss-red/30 backdrop-blur-md"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
          <div>
            <div className="font-bold text-base">Dataset Processing Failed</div>
            <div className="mt-1 text-sm text-bss-red/80">{error}</div>
            <button
              onClick={() => { setError(null); setResult(null); setCurrentIndex(0); setIsPlaying(false); }}
              className="mt-3 rounded-lg bg-black/40 px-4 py-1.5 text-xs font-bold text-white hover:bg-black/60 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </motion.div>
      )}

      {result && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-6"
        >
          <div className="glass rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4 border border-white/10">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                <FileSpreadsheet className="h-6 w-6 text-bss-accent" />
              </div>
              <div>
                <div className="font-bold text-lg text-white tracking-tight">{result.filename}</div>
                <div className="text-xs text-bss-muted font-mono mt-1">
                  {result.n_rows.toLocaleString()} Records Processed • Engine: {result.model_kind} v{result.model_version}
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={downloadAnnotated}
                className="flex items-center gap-2 rounded-xl bg-bss-accent/20 border border-bss-accent/50 px-4 py-2.5 text-sm font-bold text-bss-accent hover:bg-bss-accent/30 transition-colors shadow-[0_0_15px_rgba(59,130,246,0.1)]"
              >
                <Download className="h-4 w-4" /> Export Results
              </button>
              <button
                onClick={() => { setResult(null); setCurrentIndex(0); setIsPlaying(false); }}
                className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm font-bold text-white hover:bg-white/10 transition-colors"
              >
                New Upload
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(["green", "yellow", "red"] as Status[]).map((s) => (
              <div key={s} className="glass rounded-2xl p-5 border border-white/5 relative overflow-hidden">
                <div className={`absolute top-0 left-0 w-1 h-full ${s === 'green' ? 'bg-bss-green' : s === 'yellow' ? 'bg-bss-yellow' : 'bg-bss-red'}`} />
                <div className="flex items-center justify-between text-xs font-bold text-bss-muted uppercase tracking-wider">
                  <span>Status: {s === 'green' ? 'Raw' : s === 'yellow' ? 'Ripe' : 'Rotten'}</span>
                  <CheckCircle2 className={`h-4 w-4 ${STATUS_COLOR[s]}`} />
                </div>
                <div className={`mt-3 text-4xl font-black tabular-nums tracking-tighter ${STATUS_COLOR[s]}`}>
                  {result.status_counts[s].toLocaleString()}
                </div>
                <div className="mt-2 text-xs font-mono text-white/50 bg-black/30 w-max px-2 py-0.5 rounded">
                  {pct(result.status_counts[s])}% of dataset
                </div>
              </div>
            ))}
          </div>

          <div className="glass rounded-2xl p-6 border border-white/10">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
              <h4 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                <Activity className="h-4 w-4 text-bss-cyan" /> Live Simulation
              </h4>
              <div className="flex gap-2">
                {!isPlaying ? (
                  <button
                    onClick={() => {
                      if (currentIndex >= result.rows.length - 1) setCurrentIndex(0);
                      setIsPlaying(true);
                    }}
                    className="flex items-center gap-2 rounded-xl bg-bss-green/20 border border-bss-green/50 px-3 py-1.5 text-xs font-bold text-bss-green hover:bg-bss-green/30 transition-colors shadow-[0_0_10px_rgba(34,197,94,0.1)]"
                  >
                    <Play className="h-3 w-3 fill-current" /> Play Simulation
                  </button>
                ) : (
                  <button
                    onClick={() => setIsPlaying(false)}
                    className="flex items-center gap-2 rounded-xl bg-bss-red/20 border border-bss-red/50 px-3 py-1.5 text-xs font-bold text-bss-red hover:bg-bss-red/30 transition-colors shadow-[0_0_10px_rgba(239,68,68,0.1)]"
                  >
                    <Square className="h-3 w-3 fill-current" /> Pause
                  </button>
                )}
                <button
                  onClick={() => { setIsPlaying(false); setCurrentIndex(0); }}
                  className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-3 py-1.5 text-xs font-bold text-white hover:bg-white/10 transition-colors"
                >
                  <RotateCcw className="h-3 w-3" /> Reset
                </button>
              </div>
            </div>
            <SensorChart data={chartData} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
            <div className="glass rounded-2xl border border-white/10 overflow-hidden flex flex-col h-[600px]">
              <div className="p-4 border-b border-white/10 bg-black/20 flex justify-between items-center">
                <span className="text-sm font-bold text-white">Batch Analysis</span>
                <span className="text-xs font-mono text-bss-muted bg-black/40 px-2 py-1 rounded">
                  {result.rows.length} rows loaded
                </span>
              </div>
              <div className="flex-1 overflow-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-[#0B1020] text-bss-muted font-bold tracking-wider uppercase border-b border-white/10 shadow-md">
                    <tr>
                      <th className="px-4 py-3">ID</th>
                      <th className="px-3 py-3">Temp</th>
                      <th className="px-3 py-3">RH%</th>
                      <th className="px-3 py-3">CO₂</th>
                      <th className="px-3 py-3">C₂H₄</th>
                      <th className="px-3 py-3">RSL</th>
                      <th className="px-4 py-3">State</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono">
                    {result.rows.map((row, idx) => {
                      const sel = currentIndex === idx;
                      return (
                        <tr
                          key={row.row_index}
                          onClick={() => { setCurrentIndex(idx); setIsPlaying(false); }}
                          className={`cursor-pointer transition-colors ${
                            sel ? "bg-white/10 ring-1 ring-white/20" : "hover:bg-white/5"
                          }`}
                        >
                          <td className="px-4 py-2.5 text-white/50">{row.row_index}</td>
                          <td className="px-3 py-2.5 text-white">{row.temp_c.toFixed(1)}°</td>
                          <td className="px-3 py-2.5 text-white">{row.humidity_pct.toFixed(0)}</td>
                          <td className="px-3 py-2.5 text-white">{row.co2_ppm.toFixed(0)}</td>
                          <td className="px-3 py-2.5 text-white">{row.ethylene_ppm.toFixed(2)}</td>
                          <td className={`px-3 py-2.5 font-bold ${STATUS_COLOR[row.predicted_status]}`}>
                            {row.predicted_rsl_days.toFixed(1)}d
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${
                              row.predicted_status === 'green' ? 'bg-bss-green/10 text-bss-green border border-bss-green/20' : 
                              row.predicted_status === 'yellow' ? 'bg-bss-yellow/10 text-bss-yellow border border-bss-yellow/20' : 
                              'bg-bss-red/10 text-bss-red border border-bss-red/20'
                            }`}>
                              {row.predicted_status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="glass rounded-2xl p-6 border border-white/10 flex flex-col items-center">
              <div className="w-full flex items-center justify-between mb-8">
                <h3 className="text-sm font-bold text-white tracking-tight">Record Inspector</h3>
                <span className="text-xs font-mono text-bss-accent bg-bss-accent/10 border border-bss-accent/20 px-2 py-0.5 rounded">
                  #{selectedRow?.row_index ?? '---'}
                </span>
              </div>
              
              <TrafficLight status={selectedRow?.predicted_status ?? null} />
              
              <div className="w-full mt-10 mb-6">
                <RSLCountdown
                  rslDays={selectedRow?.predicted_rsl_days ?? null}
                  status={selectedRow?.predicted_status ?? null}
                />
              </div>

              {selectedRow?.prediction_reason && (
                <div className="w-full rounded-xl bg-black/40 border border-white/5 p-4 text-center text-sm text-bss-text font-medium shadow-inner mb-6">
                  {selectedRow.prediction_reason}
                </div>
              )}

              {selectedRow && (
                <div className="w-full mt-auto space-y-2">
                  <div className="flex justify-between items-center p-2 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-xs text-bss-muted font-bold tracking-wider uppercase">Confidence</span>
                    <span className="font-mono text-sm text-white">{(selectedRow.prediction_confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-xs text-bss-muted font-bold tracking-wider uppercase">Age</span>
                    <span className="font-mono text-sm text-white">{selectedRow.hours_since_harvest.toFixed(1)}h</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <div className="text-xs text-bss-muted font-bold uppercase tracking-wider">{label}</div>
      <div className="mt-1 text-xl font-bold tabular-nums text-white">{value}</div>
    </div>
  );
}
