import typing as T
import re


REPOSITORY_URL_REGEX = r"(/[a-zA-Z0-9-_]+){2}(.git)?$"


def extract_repository_from_url(url: str) -> T.Tuple:
    regex = re.compile(REPOSITORY_URL_REGEX)
    remove_suffix = ".git"
    r = regex.search(url)

    if not r:
        raise ValueError

    match = r.group()
    if match.endswith(remove_suffix):
        match = match[:-len(remove_suffix)]

    parts = match.split("/")[-2:]

    return tuple(parts)
