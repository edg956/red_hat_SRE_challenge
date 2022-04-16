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
    errors = {}
    for path in paths:
        try:
            result[path] = extract_from_dockerfile(owner, repo_name, sha, path, client)
        except Exception as e:
            logger.exception(e)
            errors[path] = str(e)

    return result, errors


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
                errors[key] = str(e)
                continue

            images, err = extract_from_paths(owner, repo_name, sha, paths, client)

            if err:
                if key not in errors:
                    errors[key] = {}
                for path in err:
                    errors[key][path] = err[path]

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
                error = (repo, sha, e)
                return error

            return (repo, sha, paths)

        def extract_dockerfiles(future):
            item = future.result()

            repo, sha, paths = item

            if isinstance(paths, Exception):
                return (repo, sha, {}, str(paths))

            owner, repo_name = extract_repository_from_url(repo)
            images, err = extract_from_paths(owner, repo_name, sha, paths, client)

            return (repo, sha, images, err)

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
            repo, sha, images, err = result.result()

            key = f"{repo}:{sha}"

            if key not in data:
                data[key] = {}
            data[key] = images

            if err:
                if key not in errors:
                    errors[key] = {}

                if isinstance(err, dict):
                    for path in err:
                        errors[key][path] = err[path]
                else:
                    errors[key] = err

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
