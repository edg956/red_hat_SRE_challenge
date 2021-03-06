from dataclasses import dataclass
import typing as T
import os

from yaml import load, Loader


__all__ = [
    'Config',
    'setup'
]


CONFIG_PATH_ENVVAR = 'DOCKERFILE_EXTRACTOR_CONFIG_PATH'


@dataclass
class Config:
    repository_list_url: str
    extractor_class: str = "SequentialExtractorService"
    github_access_id: str = None
    github_access_secret: str = None
    thread_pool_size: int = 1


def setup(config_path: str = None) -> Config:
    config_path = os.environ.get(CONFIG_PATH_ENVVAR, 'config/config.yml')

    with open(config_path) as f:
        yaml_config = load(f, Loader=Loader)

    env_config = {env.lower(): os.environ[env] for env in os.environ if env.lower() in Config.__annotations__}

    return Config(**{**yaml_config, **env_config})
