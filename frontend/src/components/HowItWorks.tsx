const PIPELINE = [
  {
    n: "01",
    title: "Unified corpus",
    body: "Codeforces + LeetCode problems are scraped, tags canonicalized to one vocabulary, and ratings normalized (R_lc − 400).",
    math: "Rᵤ = { R_cf · CF , R_lc − 400 · LC }",
  },
  {
    n: "02",
    title: "Semantic · LSA",
    body: "Tags are boosted and injected into a TF-IDF matrix, reduced with Truncated SVD into a 150-dim latent concept space.",
    math: "X ≈ U_k Σ_k V_kᵀ",
  },
  {
    n: "03",
    title: "Structural · Spectral",
    body: "An IDF-weighted tag-overlap graph is built; the Laplacian L = D − A yields a structural embedding from its smallest eigenvectors.",
    math: "L = D − A ,  f = eigvec(λ_min)",
  },
  {
    n: "04",
    title: "Fusion + bridge",
    body: "Semantic + structural vectors concatenate (L2-normalized), ranked by cosine, filtered 100–300 pts easier — one per platform.",
    math: "target − 300 ≤ R ≤ target − 100",
  },
];

const DEFENSES = [
  {
    title: "The story problem",
    problem: "Codeforces buries simple algorithms under elaborate stories. TF-IDF clusters by flavour, not algorithm.",
    fix: "Tags are boosted ×6 and story vocabulary maps to algorithmic tokens (maze → graph), so the latent space tracks logic, not nouns.",
  },
  {
    title: "Graph sparsity",
    problem: "Overlapping tags are inconsistent; broad tags create disconnected components that break eigen-decomposition.",
    fix: "Generic tags are excluded, tags are IDF-weighted, and semantic k-NN backbone edges stitch components into one connected graph.",
  },
  {
    title: "API rate limits",
    problem: "LeetCode's GraphQL endpoint aggressively blocks scrapers; cold starts could fail.",
    fix: "Exponential backoff + jitter, SQLite caching, and a bundled 9k-problem dataset keep the hosted demo fully functional offline.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how" className="mx-auto max-w-6xl px-5 py-16">
      <div className="mb-10 text-center">
        <h2 className="text-2xl font-bold text-ink md:text-3xl">How the engine works</h2>
        <p className="mx-auto mt-2 max-w-2xl text-sm text-ink-muted">
          A four-phase statistical-ML pipeline fusing language and graph structure to reason about
          algorithmic similarity across platforms.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {PIPELINE.map((s, i) => (
          <div key={s.n} className="panel p-5">
            <div className="mb-3 flex items-center gap-2">
              <span className="meta font-bold text-accent">{s.n}</span>
              {i < PIPELINE.length - 1 && <span className="text-ink-faint">→</span>}
            </div>
            <h3 className="mb-2 font-semibold text-ink">{s.title}</h3>
            <p className="text-sm leading-relaxed text-ink-muted">{s.body}</p>
            <code className="mt-3 block rounded-md border border-line bg-canvas-base px-2.5 py-1.5 font-mono text-[11px] text-bridge">
              {s.math}
            </code>
          </div>
        ))}
      </div>

      <div className="mt-12">
        <h3 className="mb-5 text-center text-lg font-semibold text-ink">
          Engineering reality checks &mdash; and how they&apos;re solved
        </h3>
        <div className="grid gap-4 md:grid-cols-3">
          {DEFENSES.map((d) => (
            <div key={d.title} className="panel p-5">
              <div className="mb-2 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-danger" />
                <h4 className="font-semibold text-ink">{d.title}</h4>
              </div>
              <p className="mb-3 text-sm leading-relaxed text-ink-muted">
                <span className="text-danger">Problem.</span> {d.problem}
              </p>
              <p className="text-sm leading-relaxed text-ink">
                <span className="text-accent-bright">Solution.</span> {d.fix}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
