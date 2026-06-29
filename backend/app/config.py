from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
ARTIFACTS_DIR = BACKEND_ROOT / "artifacts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPECTRALBRIDGE_", env_file=".env", extra="ignore")

    # --- Paths ---
    db_path: Path = DATA_DIR / "problems.db"
    artifacts_dir: Path = ARTIFACTS_DIR
    fallback_dataset_path: Path = DATA_DIR / "fallback_dataset.json"

    # --- ML hyperparameters ---
    lsa_components: int = 150
    tag_boost: int = 6            # how many times algorithmic tags are repeated in the corpus
    spectral_dims: int = 64       # number of structural eigenvectors used as embedding
    graph_rating_window: int = 200  # max rating gap allowed for a structural edge
    graph_tag_overlap: float = 0.6  # min weighted tag-overlap score for a structural edge

    # --- Bridge recommendation filter ---
    bridge_lower: int = 100       # candidate must be >= target_rating - (this) ... easier
    bridge_upper: int = 300       # candidate must be <= target_rating - (this) ... not too easy
    bridge_top_k: int = 3

    # --- Scraping / runtime ---
    use_fallback_only: bool = False  # when True, never hit external APIs (safe for hosted demo)
    http_timeout: float = 20.0
    cf_api_base: str = "https://codeforces.com/api"
    lc_graphql_url: str = "https://leetcode.com/graphql"


settings = Settings()
settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
