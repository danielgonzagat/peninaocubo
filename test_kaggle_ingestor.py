import pytest

from penin.ingest.kaggle_ingestor import SAFE_QUERY_PATTERN


@pytest.mark.parametrize(
    "query",
    [
        "simple query",
        "owner/dataset",
        "numbers 123",
        "punctuation, with. dash- and/slash",
    ],
)
def test_safe_query_pattern_allows_common_queries(query):
    assert SAFE_QUERY_PATTERN.fullmatch(query)


@pytest.mark.parametrize("query", ["bad_query", "semi;colon", "pipe|query", "../etc/passwd"])
def test_safe_query_pattern_blocks_unsafe_queries(query):
    assert not SAFE_QUERY_PATTERN.fullmatch(query)
