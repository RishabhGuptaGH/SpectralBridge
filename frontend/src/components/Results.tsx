import type { ProblemOut, RecommendationOut, RecommendResponse } from "../api";
import {
  difficultyColor,
  matchTier,
  platformColor,
  platformLabel,
  reasonLabel,
  relevancePct,
} from "../utils";

interface ResultsProps {
  data: RecommendResponse;
}

export default function Results({ data }: ResultsProps) {
  const { target, recommendations, note } = data;
  const pcts = relevancePct(recommendations);

  return (
    <section className="mx-auto max-w-5xl animate-rise px-5 py-8">
      <SectionLabel>you&apos;re stuck on</SectionLabel>
      <TargetCard target={target} />

      <div className="mb-4 mt-12 flex items-center justify-between gap-3">
        <SectionLabel>recommended bridges</SectionLabel>
        <span className="meta text-ink-faint">easier · same logic · cross-platform</span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {recommendations.map((r, i) => (
          <BridgeCard key={r.id} rec={r} pct={pcts[i]} rank={i + 1} />
        ))}
      </div>

      {note && (
        <p className="mt-5 rounded-lg border border-warn-deep/30 bg-warn/5 px-4 py-2.5 font-mono text-[11px] text-warn-bright/90">
          {note}
        </p>
      )}
    </section>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-5 flex items-center gap-3">
      <span className="meta uppercase tracking-[0.2em] text-accent">{children}</span>
      <div className="h-px flex-1 bg-gradient-to-r from-line to-transparent" />
    </div>
  );
}

function TargetCard({ target }: { target: ProblemOut }) {
  return (
    <div className="panel-raised relative overflow-hidden p-5 md:p-6">
      <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-accent/5 blur-3xl" />
      <div className="relative flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <div className="mb-2.5 flex flex-wrap items-center gap-2">
            <span className={`tag-chip ${platformColor(target.platform)}`}>{platformLabel(target.platform)}</span>
            {target.difficulty && (
              <span className={`tag-chip ${difficultyColor(target.difficulty)}`}>{target.difficulty}</span>
            )}
            {target.rating != null && (
              <span className="tag-chip">rating {Math.round(target.rating)}</span>
            )}
          </div>
          <h2 className="truncate text-xl font-bold text-ink md:text-2xl">{target.title}</h2>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {target.tags.slice(0, 8).map((t) => (
              <span key={t} className="tag-chip">{t}</span>
            ))}
          </div>
        </div>
        <a href={target.url} target="_blank" rel="noreferrer" className="btn-ghost shrink-0 self-start">
          open problem
          <ArrowIcon />
        </a>
      </div>
    </div>
  );
}

function BridgeCard({
  rec,
  pct,
  rank,
}: {
  rec: RecommendationOut;
  pct: number;
  rank: number;
}) {
  return (
    <a
      href={rec.url}
      target="_blank"
      rel="noreferrer"
      className="group panel flex cursor-pointer flex-col p-5 transition-all duration-200 hover:-translate-y-1 hover:border-accent/40 hover:shadow-glow"
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-accent/40 bg-accent/10 font-mono text-xs font-bold text-accent-bright">
          {rank}
        </span>
        <span className={`tag-chip ${platformColor(rec.platform)}`}>{platformLabel(rec.platform)}</span>
      </div>

      <h3 className="line-clamp-2 font-semibold leading-snug text-ink transition-colors group-hover:text-accent-bright">
        {rec.title}
      </h3>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {rec.difficulty && (
          <span className={`tag-chip ${difficultyColor(rec.difficulty)}`}>{rec.difficulty}</span>
        )}
        {rec.rating != null && <span className="tag-chip">{Math.round(rec.rating)}</span>}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {rec.tags.slice(0, 5).map((t) => (
          <span key={t} className="tag-chip">{t}</span>
        ))}
      </div>

      {/* relevance meter */}
      <div className="mt-auto pt-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="meta text-ink-muted">{matchTier(rec.similarity)}</span>
          <span className="meta text-ink-faint">{pct}%</span>
        </div>
        <div className="h-1 w-full overflow-hidden rounded-full bg-canvas-inset">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent-deep to-accent-bright transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-2 meta leading-snug text-ink-faint">{reasonLabel(rec.reason)}</p>
      </div>
    </a>
  );
}

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M7 17 17 7M7 7h10v10" />
    </svg>
  );
}
