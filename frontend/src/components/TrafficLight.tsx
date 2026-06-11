import { Status } from "../api/client";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

const COLOR: Record<Status, { fill: string; ring: string; label: string; glow: string }> = {
  green: { fill: "bg-bss-green", ring: "ring-bss-green/30", label: "Raw", glow: "shadow-[0_0_20px_rgba(34,197,94,0.6)]" },
  yellow: { fill: "bg-bss-yellow", ring: "ring-bss-yellow/30", label: "Ripe", glow: "shadow-[0_0_20px_rgba(234,179,8,0.6)]" },
  red: { fill: "bg-bss-red", ring: "ring-bss-red/30", label: "Rotten", glow: "shadow-[0_0_20px_rgba(239,68,68,0.6)]" },
};

export function TrafficLight({ status }: { status: Status | null }) {
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex flex-col gap-3 rounded-2xl glass p-5 relative overflow-hidden">
        {/* Inner subtle glow */}
        <div className="absolute inset-0 bg-white/5 pointer-events-none" />
        
        {(["red", "yellow", "green"] as Status[]).map((s) => {
          const active = status === s;
          return (
            <div key={s} className="relative flex justify-center items-center h-16 w-16">
              {active && (
                <motion.div
                  layoutId="activeGlow"
                  className={cn("absolute inset-0 rounded-full blur-md opacity-50", COLOR[s].fill)}
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <div
                className={cn(
                  "relative h-12 w-12 rounded-full transition-all duration-500 z-10 border-2",
                  active 
                    ? `${COLOR[s].fill} border-white/20 animate-soft-pulse ring-8 ${COLOR[s].ring} ${COLOR[s].glow}` 
                    : "bg-[#1F2937] border-black/50 shadow-inner"
                )}
              />
            </div>
          );
        })}
      </div>
      
      <div className="h-6">
        {status ? (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-bold tracking-wider uppercase"
            style={{ color: status === 'green' ? '#22C55E' : status === 'yellow' ? '#EAB308' : '#EF4444' }}
          >
            {COLOR[status].label}
          </motion.div>
        ) : (
          <div className="text-sm font-medium text-bss-muted tracking-wider uppercase">Awaiting Data</div>
        )}
      </div>
    </div>
  );
}
