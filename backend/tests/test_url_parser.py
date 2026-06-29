from app.url_parser import parse_url


def test_codeforces_problemset_url():
    platform, pid = parse_url("https://codeforces.com/problemset/problem/1200/A")
    assert platform == "codeforces"
    assert pid == "cf:1200/A"


def test_codeforces_contest_url():
    platform, pid = parse_url("https://codeforces.com/contest/580/problem/C")
    assert platform == "codeforces"
    assert pid == "cf:580/C"


def test_codeforces_lowercase_index_normalized():
    _, pid = parse_url("https://codeforces.com/contest/580/problem/c")
    assert pid == "cf:580/C"


def test_leetcode_url():
    platform, pid = parse_url("https://leetcode.com/problems/two-sum/")
    assert platform == "leetcode"
    assert pid == "lc:two-sum"


def test_leetcode_description_url():
    _, pid = parse_url("https://leetcode.com/problems/word-break/description/")
    assert pid == "lc:word-break"


def test_bare_id_accepted():
    assert parse_url("cf:1200/A")[1] == "cf:1200/A"
    assert parse_url("lc:two-sum")[1] == "lc:two-sum"


def test_garbage_returns_none():
    assert parse_url("https://example.com/") == (None, None)
    assert parse_url("") == (None, None)
