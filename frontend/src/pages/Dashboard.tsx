import { useEffect, useState } from "react";
import { ManualInputPanel } from "../components/ManualInputPanel";
import { SimulationPanel } from "../components/SimulationPanel";
import { TimeSlider } from "../components/TimeSlider";
import { CsvUploadPanel } from "../components/CsvUploadPanel";
import { Layout } from "../components/Layout";
import { getHealth } from "../api/client";
import { AnimatePresence, motion } from "framer-motion";

type Tab = "manual" | "live" | "fast" | "upload";

export function Dashboard() {
  const [tab, setTab] = useState<Tab>("manual");
  const [modelKind, setModelKind] = useState<string>("...");
  const [modelVersion, setModelVersion] = useState<string>("0.0.0");

  useEffect(() => {
    getHealth()
      .then((h) => {
        setModelKind(h.model_kind);
        setModelVersion(h.model_version);
      })
      .catch(() => setModelKind("offline"));
  }, []);

  return (
    <Layout activeTab={tab} setActiveTab={setTab} modelKind={modelKind} modelVersion={modelVersion}>
      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="w-full h-full"
        >
          {tab === "manual" && <ManualInputPanel />}
          {tab === "live" && <SimulationPanel />}
          {tab === "fast" && <TimeSlider />}
          {tab === "upload" && <CsvUploadPanel />}
        </motion.div>
      </AnimatePresence>
    </Layout>
  );
}
