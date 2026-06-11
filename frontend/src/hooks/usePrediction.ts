import { useState } from "react";
import { postPredict, PredictRequest, PredictionResponse } from "../api/client";

export function usePrediction() {
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function predict(req: PredictRequest) {
    setLoading(true);
    setError(null);
    try {
      const r = await postPredict(req);
      setResult(r);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return { result, loading, error, predict };
}
