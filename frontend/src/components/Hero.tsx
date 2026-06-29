import { useState, type FormEvent } from "react";

interface HeroProps {
  onSubmit: (url: string) => void;
  loading: boolean;
  onExample: (url: string) => void;
}

const EXAMPLES = [
  { label: "CF · Kefa and Park", url: "https://codeforces.com/contest/580/problem/C" },
  { label: "LC · Word Break", url: "https://leetcode.com/problems/word-break/" },
  { label: "CF · Spreadsheet", url: "https://codeforces.com/problemset/problem/1/B" },
  { label: "LC · Course Schedule", url: "https://leetcode.com/problems/course-schedule/" },
];

export default function Hero({ onSubmit, loading, onExample }: HeroProps) {
  const [value, setValue] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (value.trim()) onSubmit(value.trim());
  }

  return (
    <section id="top" className="relative mx-auto max-w-5xl px-5 pt-14 pb-6 text-center md:pt-20">
      <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-canvas-inset px-3.5 py-1.5">
        <span className="meta text-accent">~ spectralbridge</span>
        <span className="meta text-ink-faint">/ LSA × spectral graph theory</span>
      </div>

      <h1 className="text-balance text-4xl font-extrabold leading-[1.05] tracking-tight text-ink md:text-6xl">
        Stuck on a problem?
        <br />
        <span className="accent-text">Bridge to the next one.</span>
      </h1>

      <p className="mx-auto mt-5 max-w-2xl text-pretty text-base text-ink-muted md:text-lg">
        SpectralBridge maps any Codeforces or LeetCode problem into a unified vector space and
        returns <span className="text-ink">3 slightly-easier problems</span> built on the exact
        same algorithmic logic &mdash; one from each platform, guaranteed.
      </p>

      {/* Command-line style input */}
      <form onSubmit={submit} className="mx-auto mt-9 max-w-2xl text-left" id="engine">
        <div className="panel group flex items-stretch gap-0 overflow-hidden p-0 shadow-panel transition-all focus-within:border-accent/40 focus-within:shadow-glow">
          <div className="flex select-none items-center gap-2 pl-4 pr-2 text-ink-faint">
            <span className="meta text-accent">$</span>
          </div>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="paste a codeforces / leetcode problem URL"
            className="meta min-w-0 flex-1 bg-transparent py-3.5 text-[13px] text-ink placeholder:text-ink-faint focus:outline-none md:text-sm"
            autoComplete="off"
            spellCheck={false}
            aria-label="Problem URL"
          />
          <button type="submit" disabled={loading || !value.trim()} className="btn-primary my-1.5 mr-1.5">
            {loading ? (
              <>
                <Spinner /> bridging
              </>
            ) : (
              <>find bridges</>
            )}
          </button>
        </div>
      </form>

      <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
        <span className="meta text-ink-faint">try:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex.url}
            type="button"
            onClick={() => {
              setValue(ex.url);
              onExample(ex.url);
            }}
            className="cursor-pointer rounded-md border border-line bg-canvas-inset px-3 py-1 font-mono text-[11px] text-ink-muted transition-all hover:border-accent/40 hover:text-ink"
          >
            {ex.label}
          </button>
        ))}
      </div>
    </section>
  );
}

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4z" />
    </svg>
  );
}
