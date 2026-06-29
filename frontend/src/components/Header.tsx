interface HeaderProps {
  stats?: { total: number } | null;
}

export default function Header({ stats }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas-base/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
        <a href="#top" className="group flex cursor-pointer items-center gap-2.5">
          <img src="/bridge.svg" alt="" className="h-7 w-7 transition-transform group-hover:scale-105" />
          <div className="leading-tight">
            <div className="font-bold tracking-tight text-ink">
              Spectral<span className="accent-text">Bridge</span>
            </div>
            <div className="meta text-ink-faint">algorithmic_recommender</div>
          </div>
        </a>

        <nav className="hidden items-center gap-7 text-sm text-ink-muted md:flex">
          <a href="#engine" className="cursor-pointer transition-colors hover:text-ink">Engine</a>
          <a href="#explore" className="cursor-pointer transition-colors hover:text-ink">Explore</a>
          <a href="#how" className="cursor-pointer transition-colors hover:text-ink">How it works</a>
        </nav>

        <div className="flex items-center gap-2 rounded-full border border-line bg-canvas-inset px-3 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-glowPulse" />
          <span className="meta text-ink-muted">
            {stats ? `${stats.total.toLocaleString()} problems` : "live"}
          </span>
        </div>
      </div>
    </header>
  );
}
