from dataclasses import dataclass
import typing as T
import os

from yaml import load, Loader


__all__ = [
    'Config',
    'setup'
]


CONFIG_PATH_ENVVAR = 'CHECKER_CONFIG_PATH'


@dataclass
class Config:
    github_access_id: T.Optional[str]
    github_access_secret: T.Optional[str]
    repository_list_url: str
    extractor_class: str = "SecuentialExtractorService"


def setup(config_path: str = None) -> Config:
    config_path = os.environ.get(CONFIG_PATH_ENVVAR, 'config/config.yml')

    with open(config_path) as f:
        yaml_config = load(f, Loader=Loader)

    env_config = {env.lower(): os.environ[env] for env in os.environ if env.lower() in Config.__annotations__}

    return Config(**{**yaml_config, **env_config})
