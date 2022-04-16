# Dockerfile image extractor
This tool checks the Dockerfiles of the repositories on the list it's configured to analyze and returns all of the base images used.

## How does it work?
This program uses Github's API to query for a repository's tree and search for files (github `blob`s) with the word `dockerfile` in it.
It then searches for the raw version of that file on the repository to parse it and find its `FROM` instructions and gather the list of images.

Since this is subject to Github's API rate limits, it's better to pass in some credentials to authenticate against github and reach limits of up to 5000 requests per hour. Without that, the program can only perform 60 requests per hour. Read on [rate limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#requests-from-personal-accounts) for more information.

Since the specification of the task talked about the input list reaching hundreds (not explicitly thousands) of lines, I considered it safe not to add any kind of rate limiting on the client, on the assumption that this job wouldn't be run enough times to go over the limit (5000 requests per hour).

This program also allows to choose between running the task sequentially (single threaded) or multithreaded. The former poses less of a risk regarding rate limits. The later, unless using only one thread, will have more chances if the app is ran more often with big input lists.

## Configuration
This program can be configured by two means: either setting the values in the file under `config/config.yml` (or whatever path is set in the environment variable `DOCKERFILE_EXTRACTOR_CONFIG_PATH`) or by setting them as environment variables (same name, but in uppercase letters).

The following table contains the available configuration
| Name | Type | Description |
|:--:|:--:|:---------:|
| repository_list_url | string | The url that contains the list of repositories and their commit hashes |
| github_access_id | string | The access ID or username to use for github's API basic auth |
| github_access_secret | string | The access secret or PAT to use for github's API basic auth |
| extractor_class | string | The name of the class that implements the process of extracting docker images from Dockerfiles. Can be one of [`SequentialExtractorService`, `ThreadedExtractorService`]   |
| thread_pool_size | int | Positive integer that sets the maximum number of threads to spawn when using `ThreadedExtractorService` |

## Extractor services comparison
On an input list of about twelve different, valid, repositories, the results of running `time python app.py` were the following:
| Service | Attempt number | Time |
|:-------:|:--------------:|:----:|
| SequentialExtractorService | 1 | 8.25s |
| SequentialExtractorService | 2 | 5.56s |
| ThreadedExtractorService | 1 | 2.24s |
| ThreadedExtractorService | 2 | 2.14s |
