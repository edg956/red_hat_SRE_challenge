import pytest

from red_hat.parsers import DockerfileParser, RepositoryListParser


@pytest.fixture
def dockerfile_parser():
    return DockerfileParser()


class TestRepositoryListParser:
    def test_only_matching_lines(self, repository_list: str):
        parser = RepositoryListParser()

        r = parser.parse(repository_list)

        assert len(r) == 3

        expected_lines = (line.split() for line in repository_list.splitlines()[:3])

        for (repo_url, sha), (expected_repo_url, expected_sha) in zip(r, expected_lines):
            assert repo_url == expected_repo_url
            assert sha == expected_sha


class TestDockerfileParser:
    def test_only_4_different_statements_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert len(r) == 2

    def test_only_two_from_statements_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert len(r) == 2
        assert r[0] == ("docker/image:latest", "as", "base")
        assert r[1] == ("base",)
