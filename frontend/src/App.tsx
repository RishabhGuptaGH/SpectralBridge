import { useCallback, useEffect, useRef, useState } from "react";
import Background from "./components/Background";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Results from "./components/Results";
import Explore from "./components/Explore";
import HowItWorks from "./components/HowItWorks";
import Stats from "./components/Stats";
import Footer from "./components/Footer";
import { ApiError, api, type RecommendResponse } from "./api";

export default function App() {
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.stats().then((s) => setCount(s.total)).catch(() => setCount(null));
  }, []);

  const run = useCallback(async (url: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await api.recommend(url, 3);
      setData(res);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        const detail = e.detail as { message?: string; suggestions?: { id: string; title: string; url: string }[] };
        const sugg = detail?.suggestions;
        if (sugg && sugg.length) {
          setError(
            "Problem not found in the bundled dataset. Try one of the examples above, or browse the corpus below.",
          );
        } else {
          setError(detail?.message || "Problem not found in the dataset.");
        }
      } else {
        setError("Something went wrong while computing bridges. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen">
      <Background />
      <Header stats={count ? { total: count } : null} />

      <main>
        <Hero onSubmit={run} loading={loading} onExample={run} />

        <div ref={resultsRef} />
        {error && (
          <div className="mx-auto max-w-5xl px-5">
            <div className="animate-rise rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 font-mono text-[12px] text-danger">
              {error}
            </div>
          </div>
        )}
        {loading && <ResultsSkeleton />}
        {data && !loading && <Results data={data} />}

        <Stats />
        <HowItWorks />
        <Explore />
      </main>

      <Footer />
    </div>
  );
}

function ResultsSkeleton() {
  return (
    <section className="mx-auto max-w-5xl px-5 py-8">
      <div className="mb-6 h-4 w-40 animate-pulse rounded bg-canvas-inset" />
      <div className="panel-raised h-28 animate-pulse" />
      <div className="mb-4 mt-12 h-4 w-48 animate-pulse rounded bg-canvas-inset" />
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="panel h-56 animate-pulse" />
        ))}
      </div>
    </section>
  );
}
