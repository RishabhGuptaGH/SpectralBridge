export interface ProblemOut {
  id: string;
  platform: string;
  title: string;
  url: string;
  tags: string[];
  difficulty: string;
  rating: number | null;
}

export interface RecommendationOut {
  id: string;
  platform: string;
  title: string;
  url: string;
  tags: string[];
  difficulty: string;
  rating: number | null;
  similarity: number;
  reason: string;
}

export interface TargetOut {
  id: string;
  platform: string;
  title: string;
  url: string;
  tags: string[];
  difficulty: string;
  rating: number | null;
}

export interface RecommendResponse {
  target: TargetOut;
  recommendations: RecommendationOut[];
  note: string | null;
}

export interface StatsOut {
  total: number;
  codeforces: number;
  leetcode: number;
  lsa_dimensions: number;
  fused_dimensions: number;
  rating_min: number | null;
  rating_max: number | null;
  tag_count: number;
}

export interface TagCount {
  tag: string;
  count: number;
}

const BASE = "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail: unknown = `${res.status} ${res.statusText}`;
    try {
      detail = await res.json();
    } catch {
      /* keep status text */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export const api = {
  recommend: (url: string, topK = 3) =>
    http<RecommendResponse>("/recommend", {
      method: "POST",
      body: JSON.stringify({ url, top_k: topK }),
    }),
  search: (q: string, limit = 12) =>
    http<ProblemOut[]>(`/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  random: (limit = 6) => http<ProblemOut[]>(`/random?limit=${limit}`),
  stats: () => http<StatsOut>("/stats"),
  tags: () => http<TagCount[]>("/tags"),
};
