from app.ml.preprocessing import (
    normalize_tag, normalize_tags, graph_tags, clean_text,
    inject_algorithmic_tokens, build_corpus,
)


def test_normalize_synonyms():
    assert normalize_tag("dfs and similar") == "dfs"
    assert normalize_tag("Depth-First Search") == "dfs"
    assert normalize_tag("Dynamic Programming") == "dynamic-programming"
    assert normalize_tag("Union Find") == "disjoint-set"


def test_normalize_tags_dedup_and_order():
    assert normalize_tags(["dp", "Dynamic Programming", "DFS"]) == [
        "dynamic-programming", "dfs"]


def test_graph_tags_drop_generic():
    gt = graph_tags(["implementation", "dfs", "math"])
    assert "dfs" in gt and "implementation" not in gt and "math" not in gt


def test_clean_text_strips_code_and_math():
    raw = "Given `x` solve ```python\nprint(1)\n``` and $a+b$ cows."
    cleaned = clean_text(raw)
    assert "print" not in cleaned
    assert "$" not in cleaned
    assert "cows" in cleaned


def test_inject_algorithmic_tokens():
    out = inject_algorithmic_tokens("the maze has a shortest path and a cycle")
    assert "graph" in out
    assert "bfs shortest-path" in out
    assert "dfs" in out


def test_build_corpus_boosts_tags():
    corpus = build_corpus("Farmer John walks cows in a maze", ["binary search", "dp"])
    # tags repeated -> dominant
    assert corpus.count("binary-search") >= 6
    assert corpus.count("dynamic-programming") >= 6
    # story vocabulary still translated
    assert "graph" in corpus  # 'maze' -> graph
