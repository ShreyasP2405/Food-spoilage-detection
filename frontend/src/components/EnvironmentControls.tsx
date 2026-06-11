import { Info } from "lucide-react";
import { cn } from "../lib/utils";

export interface SliderRow {
  label: string;
  hint?: string;
  value: number;
  setValue: (v: number) => void;
  min: number;
  max: number;
  step: number;
  unit: string;
}

export function Slider({ row }: { row: SliderRow }) {
  const percentage = ((row.value - row.min) / (row.max - row.min)) * 100;
  
  return (
    <label className="flex flex-col gap-2 p-3 rounded-lg bg-black/20 border border-white/5 hover:bg-black/30 transition-colors">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 font-medium text-bss-text">
          {row.label}
          {row.hint && (
            <span title={row.hint} className="cursor-help text-bss-muted hover:text-bss-cyan transition-colors">
              <Info className="h-3.5 w-3.5" />
            </span>
          )}
        </span>
        <span className="font-mono text-xs px-2 py-0.5 rounded bg-bss-accent/10 text-bss-accent border border-bss-accent/20">
          {row.value.toFixed(row.step >= 1 ? 0 : 1)} {row.unit}
        </span>
      </div>
      
      <div className="relative h-2 rounded-full bg-gray-800 overflow-hidden group-hover:bg-gray-700 transition-colors">
        <div 
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-bss-cyan to-bss-accent transition-all duration-150"
          style={{ width: `${percentage}%` }}
        />
        <input
          type="range"
          min={row.min}
          max={row.max}
          step={row.step}
          value={row.value}
          onChange={(e) => row.setValue(Number(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />
      </div>
      <div className="flex justify-between text-[10px] text-bss-muted font-mono px-1">
        <span>{row.min}</span>
        <span>{row.max}</span>
      </div>
    </label>
  );
}

export function EnvironmentControls({ rows }: { rows: SliderRow[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {rows.map((r) => (
        <Slider key={r.label} row={r} />
      ))}
    </div>
  );
}
