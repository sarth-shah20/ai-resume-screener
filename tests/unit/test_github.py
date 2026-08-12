import pytest
from src.services.github_service import canonical_repository

def test_accepts_canonical_github_repository():
    assert canonical_repository("https://github.com/owner/repo") == ("owner", "repo")

@pytest.mark.parametrize("url", ["http://github.com/a/b", "https://evil.test/a/b", "https://github.com/a/b/issues", "https://github.com/a/b?x=1"])
def test_rejects_unbounded_urls(url):
    with pytest.raises(ValueError):
        canonical_repository(url)
