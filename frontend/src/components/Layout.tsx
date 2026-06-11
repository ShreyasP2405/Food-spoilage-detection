import { ReactNode } from "react";
import { Banana, Activity, Sliders, FastForward, Upload } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";

type Tab = "manual" | "live" | "fast" | "upload";

interface LayoutProps {
  children: ReactNode;
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  modelKind: string;
  modelVersion: string;
}

export function Layout({ children, activeTab, setActiveTab, modelKind, modelVersion }: LayoutProps) {
  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: "manual", label: "Manual Input", icon: Sliders },
    { id: "live", label: "Live Sensors", icon: Activity },
    { id: "fast", label: "Simulation", icon: FastForward },
    { id: "upload", label: "Batch Upload", icon: Upload },
  ];

  return (
    <div className="flex h-screen w-full bg-bss-bg text-bss-text overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r border-white/5 bg-[#111827]/40 backdrop-blur-xl z-20">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-gradient-to-br from-bss-yellow to-bss-accent p-2 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.3)]">
            <Banana className="h-6 w-6 text-bss-bg" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">FoodSense AI</h1>
            <p className="text-[10px] uppercase tracking-wider text-bss-cyan font-semibold">Spoilage Detection</p>
          </div>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-2">
          {tabs.map(({ id, label, icon: Icon }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all duration-300 relative group",
                  isActive ? "text-white bg-white/10" : "text-bss-muted hover:text-white hover:bg-white/5"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-white/10 rounded-lg border border-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  />
                )}
                <Icon className={cn("h-5 w-5 z-10 transition-colors", isActive ? "text-bss-cyan" : "text-bss-muted group-hover:text-white")} />
                <span className="z-10 font-medium">{label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-4 m-4 rounded-xl border border-white/10 bg-black/20 text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-bss-muted font-medium">Model Status</span>
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bss-green opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-bss-green"></span>
              </span>
              <span className="text-bss-green font-medium">Online</span>
            </div>
          </div>
          <div className="flex justify-between items-center font-mono text-[10px] text-bss-muted">
            <span>{modelKind}</span>
            <span>v{modelVersion}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-bss-accent/10 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-bss-cyan/10 blur-[120px] pointer-events-none" />
        
        {/* Top Header */}
        <header className="h-20 border-b border-white/5 bg-transparent flex items-center justify-between px-8 z-10">
          <h2 className="text-xl font-semibold text-white tracking-tight">
            {tabs.find((t) => t.id === activeTab)?.label}
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium text-white">System Monitor</div>
              <div className="text-xs text-bss-muted font-mono">{new Date().toLocaleDateString()}</div>
            </div>
          </div>
        </header>

        {/* Scrollable Page Content */}
        <div className="flex-1 overflow-y-auto p-8 z-10">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
