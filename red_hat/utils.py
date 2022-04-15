import typing as T
import re


REPOSITORY_URL_REGEX = r"(/[a-zA-Z0-9-_]+){2}(.git)?$"


def extract_repository_from_url(url: str) -> T.Tuple:
    regex = re.compile(REPOSITORY_URL_REGEX)

    r = regex.search(url)

    if not r:
        raise ValueError

    parts = r.group().split("/")[-2:]

    return tuple(parts)
