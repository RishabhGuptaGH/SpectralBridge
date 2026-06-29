import { useEffect, useState } from "react";
import { api, type StatsOut } from "../api";

export default function Stats() {
  const [s, setS] = useState<StatsOut | null>(null);

  useEffect(() => {
    api.stats().then(setS).catch(() => setS(null));
  }, []);

  if (!s) return null;

  const items = [
    { label: "Problems indexed", value: s.total.toLocaleString() },
    { label: "Codeforces", value: s.codeforces.toLocaleString() },
    { label: "LeetCode", value: s.leetcode.toLocaleString() },
    { label: "LSA dimensions", value: s.lsa_dimensions },
    { label: "Fused vector dims", value: s.fused_dimensions },
    { label: "Distinct tags", value: s.tag_count },
    {
      label: "Rating span",
      value: s.rating_min != null && s.rating_max != null
        ? `${Math.round(s.rating_min)}–${Math.round(s.rating_max)}`
        : "—",
    },
  ];

  return (
    <section className="mx-auto max-w-6xl px-5 py-8">
      <div className="panel grid grid-cols-2 gap-px overflow-hidden sm:grid-cols-4 lg:grid-cols-7">
        {items.map((it) => (
          <div key={it.label} className="bg-canvas-panel/60 px-4 py-4 text-center">
            <div className="font-mono text-lg font-bold text-accent-bright md:text-xl">{it.value}</div>
            <div className="meta mt-0.5 uppercase tracking-wider text-ink-faint">{it.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
