"""Phase 3 - Structural graph embedding via Spectral Graph Theory.

Builds an adjacency matrix from *specificity-weighted* tag overlap, computes the
graph Laplacian ``L = D - A`` and extracts a low-dimensional embedding from the
eigenvectors of its smallest non-zero eigenvalues.

Two engineering defences against the *Graph Sparsity* reality check are baked
in here:

* **Specificity (IDF) weighting** - generic tags (implementation, math, ...)
  are excluded and the remaining tags are weighted by inverse document
  frequency so a rare, informative tag ("heavy-light decomposition") contributes
  far more to an edge than a common one.

* **Semantic backbone edges** - after the tag-overlap graph is built, any
  disconnected components are stitched together using the top-k LSA nearest
  neighbours. This guarantees a connected graph so the eigen-decomposition
  always yields a meaningful global embedding instead of degenerate per-component
  constant vectors.
"""
from __future__ import annotations

import warnings

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.csgraph import connected_components

from ..config import settings


class SpectralEmbedder:
    def __init__(self, dims: int | None = None, rating_window: int | None = None,
                 tag_overlap: float | None = None):
        self.dims = dims or settings.spectral_dims
        self.rating_window = rating_window or settings.graph_rating_window
        self.tag_overlap = tag_overlap or settings.graph_tag_overlap
        self.eigvecs: np.ndarray | None = None
        self.eigvals: np.ndarray | None = None
        self.dim: int = 0

    # ------------------------------------------------------------ public API
    def fit(self, tag_lists: list[list[str]], ratings: list[float | None],
            semantic_matrix: np.ndarray, k_backbone: int = 5) -> np.ndarray:
        """Return the spectral embedding matrix of shape (N, dims).

        Parameters
        ----------
        tag_lists   : graph-relevant tags per problem (generic tags already removed)
        ratings     : unified rating per problem (None allowed)
        semantic_matrix : normalized LSA matrix, used to build backbone edges
        k_backbone  : number of semantic-NN edges used to connect components
        """
        n = len(tag_lists)
        A = self._build_adjacency(tag_lists, ratings)
        A = self._add_backbone_edges(A, semantic_matrix, k_backbone)
        L = self._laplacian(A)
        vecs, vals = self._eigendecompose(L)
        self.eigvecs = vecs
        self.eigvals = vals
        self.dim = vecs.shape[1]
        return self._row_sign_normalize(vecs)

    # --------------------------------------------------------- adjacency
    def _build_adjacency(self, tag_lists, ratings) -> sp.csr_matrix:
        n = len(tag_lists)
        # IDF-weighted tag presence. tag -> (index, idf)
        df: dict[str, int] = {}
        for tags in tag_lists:
            for t in set(tags):
                df[t] = df.get(t, 0) + 1
        vocab = {t: i for i, t in enumerate(sorted(df))}

        rows, cols, data = [], [], []
        for i, tags in enumerate(tag_lists):
            seen = set()
            for t in tags:
                if t in vocab and t not in seen:
                    idf = np.log((1.0 + n) / (1.0 + df[t])) + 1.0
                    rows.append(i)
                    cols.append(vocab[t])
                    data.append(idf)
                    seen.add(t)
        T = sp.csr_matrix(
            (np.asarray(data, dtype=np.float64), (rows, cols)),
            shape=(n, len(vocab)),
        )
        # weighted overlap (shared tag idf mass) between every pair
        overlap = (T @ T.T).tocsr()
        # normalize each row's self-overlap to use weighted-cosine threshold
        diag = overlap.diagonal().copy()
        diag[diag == 0] = 1.0

        ratings = np.asarray([r if r is not None else np.nan for r in ratings])
        A = overlap.tolil()
        overlap = overlap.tocoo()
        for i, j, w in zip(overlap.row, overlap.col, overlap.data):
            if i >= j:
                continue
            # weighted cosine similarity of tag sets
            denom = np.sqrt(diag[i] * diag[j])
            sim = w / denom if denom else 0.0
            if sim < self.tag_overlap:
                continue
            ri, rj = ratings[i], ratings[j]
            if np.isnan(ri) or np.isnan(rj):
                continue
            if abs(ri - rj) > self.rating_window:
                continue
            A[i, j] = 1.0
            A[j, i] = 1.0
        A.setdiag(0)
        return A.tocsr()

    def _add_backbone_edges(self, A: sp.csr_matrix, semantic: np.ndarray,
                            k: int) -> sp.csr_matrix:
        """Connect disjoint components using semantic k-NN edges."""
        n_components, labels = connected_components(csgraph=A, directed=False)
        if n_components <= 1:
            return A

        A = A.tolil()
        # cosine similarity (semantic rows are already L2-normalized)
        sim = semantic @ semantic.T
        np.fill_diagonal(sim, -1.0)

        # For each component representative, link to nearest node in another comp.
        comp_of = labels
        for src in range(semantic.shape[0]):
            order = np.argsort(-sim[src])
            linked = 0
            for dst in order:
                if comp_of[dst] == comp_of[src]:
                    continue
                A[src, dst] = max(A[src, dst], 1.0)
                A[dst, src] = max(A[dst, src], 1.0)
                comp_of[dst] = comp_of[src]  # merge lazily
                linked += 1
                if linked >= k:
                    break
        return A.tocsr()

    # ------------------------------------------------------------- laplacian
    @staticmethod
    def _laplacian(A: sp.csr_matrix) -> sp.csr_matrix:
        degree = np.asarray(A.sum(axis=1)).ravel()
        D = sp.diags(degree, format="csr")
        return (D - A).tocsr()

    # ------------------------------------------------------- eigendecompose
    def _eigendecompose(self, L: sp.csr_matrix):
        n = L.shape[0]
        k = min(self.dims + 1, n - 1)  # +1 to drop the trivial zero eigenvalue
        k = max(2, k)
        try:
            # shift-invert mode reliably targets the smallest eigenvalues
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vals, vecs = spla.eigsh(L, k=k, sigma=-1e-5, which="LM")
        except (spla.ArpackNoConvergence, RuntimeError, ValueError):
            # robust dense fallback for small graphs
            vals, vecs = np.linalg.eigh(L.toarray())

        order = np.argsort(vals)
        vals = vals[order]
        vecs = vecs[:, order]

        # drop the first trivial eigenvector (eigenvalue ~ 0, constant vector)
        vecs = vecs[:, 1:1 + self.dims]
        vals = vals[1:1 + self.dims]
        # pad if graph too small to yield dims vectors
        if vecs.shape[1] < self.dims:
            pad = np.zeros((n, self.dims - vecs.shape[1]))
            vecs = np.hstack([vecs, pad])
        return vecs, vals

    @staticmethod
    def _row_sign_normalize(vecs: np.ndarray) -> np.ndarray:
        # sign flip for determinism (largest-magnitude entry positive)
        for j in range(vecs.shape[1]):
            col = vecs[:, j]
            idx = np.argmax(np.abs(col))
            if col[idx] < 0:
                vecs[:, j] = -col
        return vecs
