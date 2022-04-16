import typing as T

import pytest

from red_hat import services


class DummyClient:
    def __init__(self, responses: T.Dict[str, T.List] = None):
        self._responses = responses

    def _return_response(self, fn_name):
        r = self._responses[fn_name].pop(0)

        if callable(r):
            return r()
        return r

    def list_repository_files(self, *args, **kwargs):
        if self._responses and 'list_repository_files' in self._responses:
            return self._return_response('list_repository_files')

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
        if self._responses and 'get_dockerfile' in self._responses:
            return self._return_response('get_dockerfile')

        return [
            ("python:3.9-slim",),
            tuple(),
            ("alpine:latest", "as", "base")
        ]


def failure_fn():
        raise Exception("Dummy exception")


@pytest.fixture
def client():
    return DummyClient()


@pytest.fixture
def fail_client():
    return DummyClient(responses={
        'get_dockerfile': [
            [("python:3.9-slim",)],
            failure_fn,
        ]
    })


class TestServices:
    def test_extract_paths_from_repository(self, client):
        r = services.search_for_dockerfile('dummy-owner', 'dummy-repo', 'not-sha', client)
        assert len(r) == 5

        assert "dockerfiles/docker.py" not in r
        assert "some/deep/dockerfiles/directory/Docker.py" not in r

        assert r[0] == "Dockerfile"

    def test_extract_from_dockerfile(self, client):
        r, _ = services.extract_from_paths('dummy-owner', 'dummy-repo', 'not-sha', ['dockerfiles', ''], client)

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

    def test_extract_from_paths_returns_errors_and_data(self, fail_client):
        r, err = services.extract_from_paths('dummy-owner', 'dummy-repo', 'not-sha', ['Dockerfile', 'UnreachableDockerfile'], fail_client)

        assert 'Dockerfile' in r
        images = r['Dockerfile']
        assert len(images) == 1
        assert images[0] == 'python:3.9-slim'

        assert 'UnreachableDockerfile' in err
        error = err['UnreachableDockerfile']
        assert error == "Dummy exception"


@pytest.fixture
def extractor_client():
    return DummyClient(responses={
        'list_repository_files': [
            [
                "some/deep/dockerfiles/directory/Dockerfile",
                "dockerfiles/docker.py",
                "some/deep/dockerfiles/directory/Docker.py",
            ]
        ],
        'get_dockerfile': [
            [
                ("python:3.9-slim",),
                tuple(),
                ("alpine:latest", "as", "base")
            ]
        ]
    })


@pytest.fixture
def fail_extractor_client():
    return DummyClient(responses={
        'list_repository_files': [
            [
                "some/deep/dockerfiles/directory/Dockerfile",
                "dockerfiles/Dockerfile.Failure",
            ]
        ],
        'get_dockerfile': [
            [
                ("python:3.9-slim",),
            ],
            failure_fn
        ]
    })


@pytest.fixture
def dummy_repo():
    return [("https://github.com/dummy/code.git", "sha")]


class TestSequentialExtractor:
    def test_happy_path(self, dummy_repo, settings, extractor_client):
        url, sha = dummy_repo[0]

        r = services.SequentialExtractorService.extract_images_from(dummy_repo, settings, extractor_client)

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

    def test_error_request_for_repository_tree(self, dummy_repo, settings, fail_extractor_client):
        fail_extractor_client._responses['list_repository_files'] = [failure_fn]
        url, sha = dummy_repo[0]

        r = services.SequentialExtractorService.extract_images_from(dummy_repo, settings, fail_extractor_client)

        ref = f"{url}:{sha}"

        assert "errors" in r
        errors = r["errors"]

        assert ref in errors
        err = errors[ref]

        assert err == 'Dummy exception'


    def test_error_request_for_dockerfiles(self, dummy_repo, settings, fail_extractor_client):
        url, sha = dummy_repo[0]

        r = services.SequentialExtractorService.extract_images_from(dummy_repo, settings, fail_extractor_client)

        ref = f"{url}:{sha}"

        assert "errors" in r
        errors = r["errors"]

        assert ref in errors
        files = errors[ref]

        assert len(files) == 1
        assert "dockerfiles/Dockerfile.Failure" in files
        error = files["dockerfiles/Dockerfile.Failure"]

        assert error == "Dummy exception"

        assert "data" in r
        data = r["data"]

        assert ref in data
        files = data[ref]

        assert len(files) == 1
        assert "some/deep/dockerfiles/directory/Dockerfile" in files
        images = files["some/deep/dockerfiles/directory/Dockerfile"]

        assert len(images) == 1
        assert "python:3.9-slim" in images


class TestThreadedExtractor:
    def test_happy_path(self, dummy_repo, settings, extractor_client):
        url, sha = dummy_repo[0]

        r = services.ThreadedExtractorService.extract_images_from(dummy_repo, settings, extractor_client)

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

    def test_error_request_for_dockerfiles(self, dummy_repo, settings, fail_extractor_client):
        url, sha = dummy_repo[0]

        r = services.ThreadedExtractorService.extract_images_from(dummy_repo, settings, fail_extractor_client)

        ref = f"{url}:{sha}"

        assert "errors" in r
        errors = r["errors"]

        assert ref in errors
        files = errors[ref]

        assert len(files) == 1
        assert "dockerfiles/Dockerfile.Failure" in files
        error = files["dockerfiles/Dockerfile.Failure"]

        assert error == "Dummy exception"

        assert "data" in r
        data = r["data"]

        assert ref in data
        files = data[ref]

        assert len(files) == 1
        assert "some/deep/dockerfiles/directory/Dockerfile" in files
        images = files["some/deep/dockerfiles/directory/Dockerfile"]

        assert len(images) == 1
        assert "python:3.9-slim" in images

    def test_error_request_for_repository_tree(self, dummy_repo, settings, fail_extractor_client):
        fail_extractor_client._responses['list_repository_files'] = [failure_fn]
        url, sha = dummy_repo[0]

        r = services.ThreadedExtractorService.extract_images_from(dummy_repo, settings, fail_extractor_client)

        ref = f"{url}:{sha}"

        assert "errors" in r
        errors = r["errors"]

        assert ref in errors
        err = errors[ref]

        assert err == 'Dummy exception'
