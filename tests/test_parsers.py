import pytest

from red_hat.parsers import DockerfileParser, RepositoryListParser


@pytest.fixture
def dockerfile():
    return (
        "FROM docker/image:latest as base\n"
        "COPY dependencies.yml .\n"
        "RUN package update && \\\n"
        "    package install\n"
        "\n\n"
        "from base\n"
        "Copy src .\n"
        "RUN runtime build\n"
        "ENTRYPOINT binary"
    )


@pytest.fixture
def dockerfile_parser():
    return DockerfileParser()


@pytest.fixture
def repository_list():
    return (
        "https://github.com/app-sre/qontract-reconcile.git 30af65af14a2dce962df923446afff24dd8f123e\n"
        "https://github.com/app-sre/container-images.git c260deaf135fc0efaab365ea234a5b86b3ead404\n"
        "https://github.com/some-user/some-repo c260deaf135fc0efaab365ea234a5b86b3ead404\n"
        "https://google.com c260deaf135fc0efaab365ea234a5b86b3ead404\n"
        "https://github.com/some-org/some-repo \n"
        "c260deaf135fc0efaab365ea234a5b86b3ead404\n"
        "github.com/ c260deaf135fc0efaab365ea234a5b86b3ead404\n"
        "    https://github.com/another-user/some-repo     c260deaf135fc0efaab365ea234a5b86b3ead404    \n"
        "https://github.com/another-user/some-repo     c260deaf135fc0efaab365ea234a5b86b3ead404\n"
    )


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

        assert len(r) == 4

    def test_only_two_from_statements_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert "FROM" in r
        statements = r["FROM"]

        assert len(statements) == 2
        assert statements[0] == ("docker/image:latest", "as", "base")
        assert statements[1] == ("base",)

    def test_only_two_copy_statements_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert "COPY" in r
        statements = r["COPY"]

        assert len(statements) == 2
        assert statements[0] == ("dependencies.yml", ".")
        assert statements[1] == ("src", ".")

    def test_only_two_run_statements_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert "RUN" in r
        statements = r["RUN"]

        assert len(statements) == 2
        assert statements[0] == ("package", "update", "&&", "package", "install")
        assert statements[1] == ("runtime", "build")

    def test_only_one_entrypoint_statement_declared(self, dockerfile_parser: DockerfileParser, dockerfile: str):
        r = dockerfile_parser.parse(dockerfile)

        assert "ENTRYPOINT" in r
        statements = r["ENTRYPOINT"]

        assert len(statements) == 1
        assert statements[0] == ("binary",)
