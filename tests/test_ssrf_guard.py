import httpx
import pytest

from app.services.ssrf_guard import UnsafeUrlError, assert_safe_url


def test_redirect_join_produces_a_plain_url_string():
    # Regression test: a prior version called a non-existent `.human_repr()` method here,
    # which broke every redirect (e.g. https://wikipedia.org/ -> https://www.wikipedia.org/).
    joined = str(httpx.URL("https://example.com/start").join("https://www.example.com/landing"))
    assert joined == "https://www.example.com/landing"
    assert_safe_url(joined)

    relative_joined = str(httpx.URL("https://example.com/a/b").join("/c"))
    assert relative_joined == "https://example.com/c"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://127.0.0.1:8080/admin",
        "http://10.1.2.3/",
        "http://172.16.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata endpoint
        "http://[::1]/",
        "http://0.0.0.0/",
        "http://localhost/",
    ],
)
def test_blocks_non_public_addresses(url):
    with pytest.raises(UnsafeUrlError):
        assert_safe_url(url)


@pytest.mark.parametrize("url", ["ftp://example.com/", "file:///etc/passwd", "gopher://example.com/"])
def test_blocks_non_http_schemes(url):
    with pytest.raises(UnsafeUrlError):
        assert_safe_url(url)


def test_blocks_missing_hostname():
    with pytest.raises(UnsafeUrlError):
        assert_safe_url("http:///no-host")
