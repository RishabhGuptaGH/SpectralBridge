export default function Footer() {
  return (
    <footer className="border-t border-line py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-5 text-center">
        <div className="flex items-center gap-2">
          <img src="/bridge.svg" alt="" className="h-6 w-6" />
          <span className="font-bold text-ink">
            Spectral<span className="accent-text">Bridge</span>
          </span>
        </div>
        <p className="max-w-xl meta leading-relaxed text-ink-faint">
          A statistical-ML recommender bridging Codeforces &amp; LeetCode with Latent Semantic
          Analysis and Spectral Graph Theory.
        </p>
        <p className="meta text-ink-faint/70">
          FastAPI · TF-IDF + TruncatedSVD · Graph Laplacian eigenmaps · React
        </p>
      </div>
    </footer>
  );
}
