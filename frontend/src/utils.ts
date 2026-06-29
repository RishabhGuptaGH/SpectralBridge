import type { RecommendationOut } from "./api";

export function platformLabel(p: string): string {
  return p === "leetcode" ? "LeetCode" : "Codeforces";
}

export function platformColor(p: string): string {
  // Codeforces = blue-slate (its brand is blue/gray); LeetCode = amber (its brand is orange)
  return p === "leetcode"
    ? "border-warn-deep/40 bg-warn/10 text-warn-bright"
    : "border-bridge-deep/40 bg-bridge/10 text-bridge";
}

export function difficultyColor(d: string): string {
  switch (d) {
    case "Easy":
      return "border-accent/40 bg-accent/10 text-accent-bright";
    case "Medium":
      return "border-warn-deep/40 bg-warn/10 text-warn-bright";
    case "Hard":
      return "border-danger/40 bg-danger/10 text-danger";
    default:
      return "border-line bg-canvas-inset text-ink-muted";
  }
}

/** Relative relevance score so the best match fills the bar, preserving order. */
export function relevancePct(recs: RecommendationOut[]): number[] {
  if (recs.length === 0) return [];
  const sims = recs.map((r) => r.similarity);
  const max = Math.max(...sims);
  const min = Math.min(...sims);
  const span = max - min || 1;
  return sims.map((s) => Math.round((55 + 45 * ((s - min) / span)) * 100) / 100);
}

export function matchTier(sim: number): string {
  if (sim >= 0.85) return "Near-identical logic";
  if (sim >= 0.55) return "Strong match";
  if (sim >= 0.25) return "Good match";
  return "Related concept";
}

export function reasonLabel(reason: string): string {
  switch (reason) {
    case "bridge":
      return "Optimal difficulty window (100-300 pts easier)";
    case "bridge-relaxed":
      return "Same-level practice (widened window)";
    default:
      return "Closest available by similarity";
  }
}
