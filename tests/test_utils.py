import pytest

from red_hat.utils import extract_repository_from_url


@pytest.fixture
def bad_repository():
    return [
        "https://github.com/django"
    ]


@pytest.mark.parametrize(
    "url,expected_owner,expected_repo",
    [
        ("https://github.com/django/django", "django", "django"),
        ("https://github.com/django/django.git", "django", "django"),
        ("https://github.com/org/test", "org", "test"),
    ]
)
def test_extract_repository_info_from_correct_urls(url, expected_owner, expected_repo):
    owner, repo = extract_repository_from_url(url)

    assert owner == expected_owner
    assert repo == expected_repo


@pytest.mark.parametrize(
    "url,exception",
    [
        ("https://github.com/django", ValueError),
        ("https://google.com", ValueError)
    ]
)
def test_extract_repository_info_from_wrong_urls(url, exception):
    with pytest.raises(exception):
        extract_repository_from_url(url)
