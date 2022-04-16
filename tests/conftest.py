import pytest

from config import setup


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def settings():
    return setup()
