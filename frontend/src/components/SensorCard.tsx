import { motion } from "framer-motion";
import { cn } from "../lib/utils";

interface SensorCardProps {
  label: string;
  value: number;
  unit: string;
  icon: React.ElementType;
  colorClass?: string;
  trend?: "up" | "down" | "stable";
}

export function SensorCard({ label, value, unit, icon: Icon, colorClass = "text-bss-accent", trend = "stable" }: SensorCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.02 }}
      className="glass rounded-xl p-4 flex flex-col justify-between relative overflow-hidden group"
    >
      <div className="absolute -inset-1 opacity-0 group-hover:opacity-20 transition-opacity blur-lg bg-gradient-to-br from-bss-accent/50 to-bss-cyan/50 rounded-xl" />
      <div className="flex items-center justify-between mb-2 z-10">
        <div className="flex items-center gap-2">
          <Icon className={cn("h-5 w-5", colorClass)} />
          <span className="text-sm font-medium text-bss-muted">{label}</span>
        </div>
        {trend === "up" && <span className="text-bss-red text-xs font-bold">▲</span>}
        {trend === "down" && <span className="text-bss-green text-xs font-bold">▼</span>}
        {trend === "stable" && <span className="text-bss-muted text-xs font-bold">—</span>}
      </div>
      <div className="flex items-baseline gap-1 z-10">
        <span className="text-2xl font-bold tracking-tight text-bss-text">
          {typeof value === "number" ? value.toFixed(1) : value}
        </span>
        <span className="text-sm font-medium text-bss-muted">{unit}</span>
      </div>
    </motion.div>
  );
}
