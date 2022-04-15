import pytest

from red_hat import services

class DummyClient:
    def list_repository_files(self, *args, **kwargs):
        return [
            "Dockerfile",
            "dockerfile",
            "Dockerfile.test",
            "some_directory/Dockerfile",
            "some/deep/dockerfiles/directory/Dockerfile",
            "dockerfiles/docker.py",
            "some/deep/dockerfiles/directory/Docker.py",
        ]

    def get_dockerfile(self, *args, **kwargs):
        return [
            ("python:3.9-slim",),
            tuple(),
            ("alpine:latest", "as", "base")
        ]


@pytest.fixture
def client():
    return DummyClient()


class TestServices:
    def test_extract_paths_from_repository(self, client):
        r = services.search_for_dockerfile('dummy-owner', 'dummy-repo', 'not-sha', client)
        assert len(r) == 5

        assert "dockerfiles/docker.py" not in r
        assert "some/deep/dockerfiles/directory/Docker.py" not in r

        assert r[0] == "Dockerfile"

    def test_extract_from_dockerfile(self, client):
        r = services.extract_from_paths('dummy-owner', 'dummy-repo', 'not-sha', ['dockerfiles'], client)

        assert 'dockerfiles' in r
        images = r['dockerfiles']

        assert len(images) == 2
        assert images[0] == 'python:3.9-slim'
        assert images[1] == 'alpine:latest'

    def test_extract_from_dockerfile(self, client):
        r = services.extract_from_dockerfile('dummy-owner', 'dummy-repo', 'not-sha', 'dockerfiles', client)

        assert len(r) == 2
        assert r[0] == 'python:3.9-slim'
        assert r[1] == 'alpine:latest'


class ExtractorDummyClient:
    def list_repository_files(self, *args, **kwargs):
        return [
            "some/deep/dockerfiles/directory/Dockerfile",
            "dockerfiles/docker.py",
            "some/deep/dockerfiles/directory/Docker.py",
        ]

    def get_dockerfile(self, *args, **kwargs):
        return [
            ("python:3.9-slim",),
            tuple(),
            ("alpine:latest", "as", "base")
        ]


@pytest.fixture
def extractor_client():
    return ExtractorDummyClient()


@pytest.fixture
def dummy_repo():
    return [("https://github.com/dummy/code.git", "sha")]


class TestSecuentialExtractor:
    def test_happy_path(self, dummy_repo, extractor_client):
        url, sha = dummy_repo[0]

        r = services.SecuentialExtractorService.extract_images_from(dummy_repo, extractor_client)

        assert "errors" in r
        assert r["errors"] == {}

        assert "data" in r
        data = r["data"]

        ref = f"{url}:{sha}"
        assert ref in data
        files = data[ref]

        assert len(files) == 1
        assert "some/deep/dockerfiles/directory/Dockerfile" in files
        images = files["some/deep/dockerfiles/directory/Dockerfile"]

        assert len(images) == 2
        assert "python:3.9-slim" in images
        assert "alpine:latest" in images


class TestThreadedExtractor:
    def test_happy_path(self, dummy_repo, extractor_client):
        url, sha = dummy_repo[0]

        r = services.SecuentialThreadedService.extract_images_from(dummy_repo, extractor_client)

        assert "errors" in r
        assert r["errors"] == {}

        assert "data" in r
        data = r["data"]

        ref = f"{url}:{sha}"
        assert ref in data
        files = data[ref]

        assert len(files) == 1
        assert "some/deep/dockerfiles/directory/Dockerfile" in files
        images = files["some/deep/dockerfiles/directory/Dockerfile"]

        assert len(images) == 2
        assert "python:3.9-slim" in images
        assert "alpine:latest" in images

