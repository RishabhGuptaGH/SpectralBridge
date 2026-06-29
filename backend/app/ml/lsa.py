"""Phase 2 - Semantic encoding via Latent Semantic Analysis.

TF-IDF over a tag-boosted corpus, reduced with Truncated SVD (LSA).

    X ~= U_k Sigma_k V_k^T

Each problem becomes a dense semantic vector in the latent concept space.
"""
from __future__ import annotations

import joblib
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from ..config import settings


class LSAEncoder:
    """TF-IDF + TruncatedSVD with L2 normalization of the latent vectors."""

    def __init__(self, n_components: int | None = None):
        self.n_components = n_components or settings.lsa_components
        self.vectorizer: TfidfVectorizer | None = None
        self.svd: TruncatedSVD | None = None
        self.dim: int = 0

    # ------------------------------------------------------------------ fit
    def fit(self, documents: list[str]) -> np.ndarray:
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            sublinear_tf=True,
            dtype=np.float32,
        )
        tfidf = self.vectorizer.fit_transform(documents)

        # SVD needs k <= min(n_docs, n_features) - 1
        max_k = max(2, min(tfidf.shape) - 1)
        k = min(self.n_components, max_k)
        self.svd = TruncatedSVD(n_components=k, random_state=42)
        latent = self.svd.fit_transform(tfidf)

        latent = self._safe_normalize(latent)
        self.dim = latent.shape[1]
        return latent

    # ------------------------------------------------------------- transform
    def transform(self, documents: list[str]) -> np.ndarray:
        if self.vectorizer is None or self.svd is None:
            raise RuntimeError("LSAEncoder is not fitted")
        tfidf = self.vectorizer.transform(documents)
        latent = self.svd.transform(tfidf)
        return self._safe_normalize(latent)

    @staticmethod
    def _safe_normalize(matrix: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(matrix, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        return normalize(matrix)  # L2 row normalization

    # ------------------------------------------------------------- persistence
    def save(self, path):
        path = str(path)
        joblib.dump(
            {"vectorizer": self.vectorizer, "svd": self.svd, "dim": self.dim},
            path,
        )

    @classmethod
    def load(cls, path) -> "LSAEncoder":
        data = joblib.load(str(path))
        enc = cls.__new__(cls)
        enc.vectorizer = data["vectorizer"]
        enc.svd = data["svd"]
        enc.dim = data["dim"]
        enc.n_components = enc.dim
        return enc
