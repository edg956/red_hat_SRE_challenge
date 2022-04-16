import abc
from concurrent import futures
import logging
import typing as T
import os
import queue

from config import Config

from red_hat import GithubClient
from red_hat.parsers import DockerfileParser
from red_hat.utils import extract_repository_from_url

logger = logging.getLogger(__name__)


def search_for_dockerfile(owner: str, repo_name: str, sha: str, client: GithubClient) -> T.List:
    paths = client.list_repository_files(owner, repo_name, sha)
    return list(filter(lambda x: "dockerfile" in os.path.basename(x).lower(), paths))


def extract_from_paths(owner: str, repo_name: str, sha: str, paths: str, client: GithubClient) -> T.Dict:
    result = {}
    for path in paths:
        result[path] = extract_from_dockerfile(owner, repo_name, sha, path, client)
    return result


def extract_from_dockerfile(owner: str, repo_name: str, sha: str, path: str, client: GithubClient) -> T.Dict:
    statements = client.get_dockerfile(owner, repo_name, sha, path, parser=DockerfileParser())

    return list(
        map(
            lambda x: x[0],
            filter(
                lambda x: len(x) > 0,
                statements
            )
        )
    )


class ExtractorService(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def extract_images_from(cls, repos: T.Iterable[T.Tuple], config: Config, client: GithubClient) -> T.Dict:
        pass


class SequentialExtractorService(abc.ABC):
    @classmethod
    def extract_images_from(cls, repos: T.Iterable[T.Tuple], config: Config, client: GithubClient) -> T.Dict:
        data = {}
        errors = {}

        for repo, sha in repos:
            key = f"{repo}:{sha}"
            owner, repo_name = extract_repository_from_url(repo)
            try:
                paths = search_for_dockerfile(owner, repo_name, sha, client)
            except Exception as e:
                logger.exception(e)
                errors[key] = {
                    "error": str(e),
                }
                continue

            try:
                images = extract_from_paths(owner, repo_name, sha, paths, client)
            except Exception as e:
                logger.exception(e)
                errors[key] = {
                    "error": str(e),
                    "paths": paths,
                }
                continue

            data[key] = images

        return {"data": data, "errors": errors}


class ThreadedExtractorService:
    @classmethod
    def extract_images_from(cls, repos: T.Iterable[T.Tuple], config: Config, client: GithubClient) -> T.Dict:
        def extract_paths(repo, sha):
            owner, repo_name = extract_repository_from_url(repo)
            try:
                paths = search_for_dockerfile(owner, repo_name, sha, client)
            except Exception as e:
                error = (repo, sha, str(e), None)
                return error
            
            return (repo, sha, paths)

        def extract_dockerfiles(future):
            item = future.result()

            repo, sha, paths = item

            try:
                owner, repo_name = extract_repository_from_url(repo)
                images = extract_from_paths(owner, repo_name, sha, paths, client)
            except Exception as e:
                return ('error', (repo, sha, str(e), paths))

            return ('result', (repo, sha, images))

        # Launch threads
        results = []
        with futures.ThreadPoolExecutor(config.thread_pool_size) as executor:
            for repo, sha in repos:
                r = executor.submit(extract_paths, repo, sha)
                results.append(executor.submit(extract_dockerfiles, r))

        # Collect results and errors through queues
        data = {}
        errors = {}

        for result in results:
            type_, output = result.result()

            if type_ == 'result':
                repo, sha, images = output
                data[f"{repo}:{sha}"] = images
            else:
                repo, sha, exc, paths = output
                errors[f"{repo}:{sha}"] = {"error": exc}
                if paths:
                    errors[f"{repo}:{sha}"]["paths"] = paths

        return {"data": data, "errors": errors}


def extractor_factory(config: Config) -> ExtractorService:
    services_map = {
        "SequentialExtractorService": SequentialExtractorService,
        "ThreadedExtractorService": ThreadedExtractorService,
    }

    assert config.extractor_class in services_map, (
        f"Extractor service class {config.extractor_class} not found in module {__file__}"
    )

    return services_map[config.extractor_class]
