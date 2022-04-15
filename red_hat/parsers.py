import abc
import typing as T
import re


REPOSITORY_LINE_REGEX = (
    r"^https://(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*"
    r"(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})\.[a-z]{2,}"
    r"/[a-zA-z-_0-9]+/[a-zA-z-_0-9]+(.git)? [A-Fa-f0-9]{40}$"
)

class Parser(abc.ABC):
    @abc.abstractmethod
    def parse(self, content: str) -> T.List[T.Tuple]:
        pass


class RepositoryListParser(Parser):
    def parse(self, content: str) -> T.List[T.Tuple]:
        regex = re.compile(REPOSITORY_LINE_REGEX)
        def filter_fn(el: str) -> bool:
            if not el:
                return False
            
            return bool(regex.match(el))

        return list(
            map(
                lambda x: tuple(x.split()),
                filter(
                    filter_fn,
                    content.splitlines()
                )
            )
        )


class DockerfileParser(Parser):
    """A very simplistic Dockerfile parser that only takes lines with the FROM instruction"""
    def parse(self, content: str) -> T.List[T.Tuple]:
        return list(
            map(
                lambda x: tuple(x.split()[1:]),
                filter(
                    lambda x: x.upper().startswith("FROM"),
                    content.splitlines()
                )
            )
        )
