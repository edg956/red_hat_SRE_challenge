import abc
import logging
import typing as T
import os

from ratelimit import limits
from config import Config

from red_hat import GithubClient
from red_hat.parsers import DockerfileParser
from red_hat.utils import extract_repository_from_url

logger = logging.getLogger(__name__)


class ExtractorService(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def extract_images_from(cls, repos: T.Iterable[T.Tuple], client: GithubClient) -> T.Dict:
        pass


class SecuentialExtractorService(abc.ABC):
    @classmethod
    def extract_images_from(cls, repos: T.Iterable[T.Tuple], client: GithubClient) -> T.Dict:
        data = {}
        errors = {}

        for repo, sha in repos:
            owner, repo_name = extract_repository_from_url(repo)
            try:
                paths = search_for_dockerfile(owner, repo_name, sha, client)
            except Exception as e:
                logger.exception(e)
                errors[repo] = {
                    "error": str(e),
                    "sha": sha,
                }
                continue

            try:
                images = extract_from_dockerfile(owner, repo_name, sha, paths, client)
            except Exception as e:
                logger.exception(e)
                errors[repo] = {
                    "error": str(e),
                    "sha": sha,
                    "paths": paths,
                }
                continue

            data[f"{repo}:{sha}"] = images

        return {"data": data, "errors": errors}


def search_for_dockerfile(owner: str, repo_name: str, sha: str, client: GithubClient) -> T.List:
    paths = client.list_repository_files(owner, repo_name, sha)
    return list(filter(lambda x: "dockerfile" in os.path.basename(x).lower(), paths))


def extract_from_dockerfile(owner: str, repo_name: str, sha: str, paths: str, client: GithubClient) -> T.Dict:
    result = {}
    for path in paths:
        statements = client.get_dockerfile(owner, repo_name, sha, path, parser=DockerfileParser())

        result[path] = list(
            map(
                lambda x: x[0],
                filter(
                    lambda x: len(x) > 0,
                    statements
                )
            )
        )
    return result


def extractor_factory(config: Config) -> ExtractorService:
    services_map = {
        "SecuentialExtractorService": SecuentialExtractorService
    }

    assert config.extractor_class in services_map, (
        f"Extractor service class {config.extractor_class} not found in module {__file__}"
    )

    return services_map[config.extractor_class]
