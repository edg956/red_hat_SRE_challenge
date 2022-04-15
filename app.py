from config import Config, setup
from red_hat import (
    ExtractorService,
    GithubClient,
    RepositoryListClient,
    RepositoryListParser,
    extractor_factory,
)


def run(settings: Config):
    gh_client = GithubClient(config=settings)
    rl_client = RepositoryListClient(config=settings)
    extractor_service: ExtractorService = extractor_factory(config=settings)

    repos = rl_client.list_of_repositories(RepositoryListParser())

    data = extractor_service.extract_images_from(repos, gh_client)

    return data


if __name__ == '__main__':
    settings = setup()
    d = run(settings)

    print(d)
