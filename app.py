from config import Config, setup
from red_hat import GithubClient, DockerfileParser, RepositoryListParser


def run(settings: Config):
    client = GithubClient(config=settings)
    pass


if __name__ == '__main__':
    settings = setup()
    run(settings)
