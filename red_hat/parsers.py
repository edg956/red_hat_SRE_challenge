import abc


class Parser(abc.ABC):
    @abc.abstractmethod
    def parse(self, content: str):
        pass


class RepositoryListParser(Parser):
    def parse(self, content: str):
        pass


class DockerfileParser(Parser):
    def parse(self, content: str):
        pass
