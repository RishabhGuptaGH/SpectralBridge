import { useEffect, useState } from "react";
import { api, type ProblemOut } from "../api";
import { difficultyColor, platformColor, platformLabel } from "../utils";

export default function Explore() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProblemOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    api.random(9).then(setResults).catch(() => setResults([]));
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setTouched(false);
      api.random(9).then(setResults).catch(() => setResults([]));
      return;
    }
    setTouched(true);
    setLoading(true);
    const id = setTimeout(() => {
      api
        .search(q, 18)
        .then(setResults)
        .catch(() => setResults([]))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(id);
  }, [query]);

  return (
    <section id="explore" className="mx-auto max-w-6xl px-5 py-16">
      <div className="mb-7 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h2 className="text-2xl font-bold text-ink md:text-3xl">Explore the corpus</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Browse indexed problems. Paste any URL above to get cross-platform bridges.
          </p>
        </div>
        <div className="panel flex w-full items-center gap-2 px-3 py-2 md:w-80">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-ink-faint">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="search problems…"
            className="meta min-w-0 flex-1 bg-transparent text-ink placeholder:text-ink-faint focus:outline-none"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 py-6 meta text-ink-muted">
          <svg className="h-4 w-4 animate-spin text-accent" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4z" />
          </svg>
          searching
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((p) => (
          <a
            key={p.id}
            href={p.url}
            target="_blank"
            rel="noreferrer"
            className="group panel flex cursor-pointer flex-col p-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/40"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className={`tag-chip ${platformColor(p.platform)}`}>{platformLabel(p.platform)}</span>
              {p.difficulty && (
                <span className={`tag-chip ${difficultyColor(p.difficulty)}`}>{p.difficulty}</span>
              )}
            </div>
            <span className="line-clamp-2 text-sm font-semibold text-ink transition-colors group-hover:text-accent-bright">
              {p.title}
            </span>
            <div className="mt-2 flex flex-wrap gap-1">
              {p.tags.slice(0, 4).map((t) => (
                <span key={t} className="tag-chip">{t}</span>
              ))}
            </div>
            <span className="meta mt-auto pt-3 text-ink-faint">
              {touched ? "open" : `rating ${p.rating ?? "—"}`}
            </span>
          </a>
        ))}
      </div>

      {!loading && results.length === 0 && (
        <p className="py-10 text-center text-sm text-ink-muted">No problems match &ldquo;{query}&rdquo;.</p>
      )}
    </section>
  );
}
