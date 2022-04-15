import typing as T

from requests import Session

from config import Config
from parsers import Parser


REPOSITORY_URL_TEMPLATE = "https://api.github.com/repos/{owner}/{name}/git/trees/{sha}?recursive={recursive}"
BLOB_TYPE = "blob"


class HttpClient:
    def __init__(self, config: Config, client: Session = None):
        if client is None:
            client = Session()
        self.client = client
        self.config = config


class RepositoryListClient(HttpClient):
    def list_of_repositories(self, parser: Parser):
        if not self.config.repository_list_url:
            raise ValueError("No repository list url specified")

        r = self.client.get(self.config.repository_list_url)
        r.raise_for_status()

        return parser(r.text)


class GithubClient:
    def list_repository_files(
        self,
        owner: str,
        repository_name: str,
        sha: str,
        recursive: bool = True
    ) -> T.Iterable:
        """Uses github's Git Tree API to return a list of files
        
        There are some limitations to the simplistic approach of this function:
        The response can return an attribute `truncated: true` meaning that the
        size of the response reached the maximum and one should recursively inspect
        the trees received by the endpoint to obtain the remainder nodes.
        
        For the record, querying for Django's tree returns a full response (no truncation),
        so I am working on the assumption that the repositories analyzed by this tool have a
        smaller tree than Django.
        
        As an extra consideration:
        
            "We actually have a limit of 100,000 entries. If the recursive parameter is supplied,
            we will read and return a maximum of 7 MB worth of entries from git ls-tree."
        
        and:
            "This all said, keep in mind that 100,000 is the current limit, but it could change
            anytime in the future."
        
        from https://github.community/t/github-get-tree-api-limits-and-recursivity/1300
        
        So, in lieu of loading this tool with the task of recursively inspecting the subtree nodes,
        I take on this simplistic approach.
        """
        r = self.client.get(
            REPOSITORY_URL_TEMPLATE.format(
                owner=owner,
                name=repository_name,
                sha=sha,
                recursive=1 if recursive else 0
            )
        )

        r.raise_for_status()
        data = r.json()

        return (node['path'] for node in data["tree"] if node["type"] == BLOB_TYPE)
