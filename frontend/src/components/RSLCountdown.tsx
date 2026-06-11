import { Status } from "../api/client";
import { Hourglass } from "lucide-react";
import { motion } from "framer-motion";

const COLOR: Record<Status, string> = {
  green: "text-bss-green",
  yellow: "text-bss-yellow",
  red: "text-bss-red",
};

export function RSLCountdown({
  rslDays,
  status,
}: {
  rslDays: number | null;
  status: Status | null;
}) {
  if (rslDays === null || status === null) {
    return (
      <div className="flex flex-col items-center gap-4 text-bss-muted">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        >
          <Hourglass className="h-10 w-10 opacity-50" />
        </motion.div>
        <div className="text-xs uppercase tracking-[0.2em] font-bold opacity-70">Calibrating Sensors</div>
      </div>
    );
  }
  
  const days = Math.max(0, rslDays);
  const wholeDays = Math.floor(days);
  const hours = Math.round((days - wholeDays) * 24);
  
  return (
    <div className="flex flex-col items-center text-center relative">
      <div className="absolute inset-0 bg-gradient-radial from-white/5 to-transparent blur-xl" />
      <motion.div 
        key={days}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className={`text-8xl font-black tabular-nums tracking-tighter ${COLOR[status]} drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]`}
      >
        {days.toFixed(1)}
      </motion.div>
      <div className="mt-2 text-sm font-bold tracking-[0.2em] uppercase text-white/80">
        Days Remaining
      </div>
      <div className="mt-2 text-xs font-mono text-bss-muted bg-black/40 px-3 py-1 rounded-full border border-white/5">
        ~ {wholeDays}d {hours}h until spoilage limit
      </div>
    </div>
  );
}
