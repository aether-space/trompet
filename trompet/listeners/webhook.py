# encoding: utf-8

"""
    Listener for Webhooks like they are used by bitbucket and GitHub.

    See https://confluence.atlassian.com/display/BITBUCKET/Setting+Up+the+Bitbucket+POST+Service
    and https://help.github.com/articles/post-receive-hooks
"""

try:
    import json
except ImportError:
    import simplejson as json
import string
from itertools import islice
from hashlib import sha256

from twisted.web import http, resource

from trompet.listeners import registry


def short_commit_message(message):
    "Returns the first line of a commit message."
    lines = message.splitlines()
    shortmessage = lines[0]
    if len(lines) > 1:
        shortmessage += u"…"
    return shortmessage

def extract_bitbucket_commit(payload, commit_data):
    """Given the payload from a message from bitbucket's POST service,
    extract all relevant data and create a commit object. A commit
    object is a dictionary with the following keys:

    - author: The commit's author.
    - branch: The branch where the commit belongs to.
    - revision: Commit's (short) revision hash.
    - message: The complete commit message.
    - shortmessage: Only the first line of the commit message.
    - url: URL to the changeset on bitbucket

    """
    commit = {}
    for (data_key, key) in [("author", "author"),
                            ("branch", "branch"),
                            ("node", "revision"),
                            ("message", "message")]:
        commit[key] = commit_data[data_key]
    commit["url"] = "https://bitbucket.org%schangeset/%s" % (
        payload["repository"]["absolute_url"], commit_data["node"])
    commit["shortmessage"] = short_commit_message(commit["message"])
    return commit

def extract_github_commit(payload, commit_data):
    """Given the payload from a message from GitHub's Webhook, extract
    all relevant data and create a commit object. A commit object is a
    dictionary with the following keys:

    - author: The commit's author.
    - branch: The branch into which the commit was pushed.
    - revision: Commit's hash.
    - message: The complete commit message.
    - shortmessage: Only the first line of the commit message.
    - url: URL to the changeset on GitHub.
    """
    commit = {}
    commit["author"] = commit_data["author"]["name"]
    for (data_key, key) in [("id", "revision"),
                            ("message", "message"),
                            ("url", "url")]:
        commit[key] = commit_data[data_key]
    ref = payload["ref"]
    if ref.startswith("refs/heads/"):
        ref = ref[len("refs/heads/"):]
    commit["branch"] = ref
    commit["shortmessage"] = short_commit_message(commit["message"])
    return commit

class WebhookListener(resource.Resource):
    """
    Resource waiting for a push notification.
    """

    def __init__(self, project, observer, message_format, commit_extractor,
                 max_commits_per_push=None):
        resource.Resource.__init__(self)
        self.project = project
        self.observer = observer
        self.message_format = message_format
        self.extract_commit = commit_extractor
        self.max_commits_per_push = max_commits_per_push

    def render_POST(self, request):
        if "payload" not in request.args:
            request.setResponseCode(http.BAD_REQUEST)
            return ""
        commits = self._parse_payload(request)
        for commit in islice(commits, self.max_commits_per_push):
            message = self.message_format.safe_substitute(
                project=self.project, **commit)
            self.observer.notify(self.project, message)
        omitted_commits = sum(1 for _ in commits)
        if omitted_commits:
            self.observer.notify(
                self.project, "[%i commits omitted.]" % (omitted_commits, ))
        return ""

    def _parse_payload(self, request):
        """Parses the request's payload.

        Returns a generator that yields commits. Sets the response code to
        400 (bad request) if the payload is malformed.
        """
        try:
            payload = json.loads(request.args["payload"][0])
            for data in payload["commits"]:
                yield self.extract_commit(payload, data)
        except (KeyError, ValueError):
            request.setResponseCode(http.BAD_REQUEST)


class TravisCIWebhookListener(resource.Resource):
    """
    Resource waiting for a Travis CI push notification.
    """

    def __init__(self, project, observer, message_format, travis_token):
        resource.Resource.__init__(self)
        self.project = project
        self.observer = observer
        self.message_format = message_format
        self.travis_token = travis_token

    def render_POST(self, request):
        if "payload" not in request.args:
            request.setResponseCode(http.BAD_REQUEST)
            return ""

        hashed_token = request.getHeader("Authorization")
        repo_slug = request.getHeader("Travis-Repo-Slug")
        if not self._check_authorization(hashed_token, repo_slug):
            request.setResponseCode(http.UNAUTHORIZED)
            return ""

        try:
            payload = json.loads(request.args["payload"][0])
            buildinfo = self._extract_buildinfo(payload)
        except (KeyError, ValueError):
            request.setResponseCode(http.BAD_REQUEST)
            return ""

        message = self.message_format.safe_substitute(project=self.project,
                                                      **buildinfo)
        self.observer.notify(self.project, message)
        return ""

    def _check_authorization(self, hashed_token, repo_slug):
        if hashed_token is None or repo_slug is None:
            return False

        expected_hash = sha256(repo_slug + self.travis_token).hexdigest()
        return hashed_token == expected_hash

    def _extract_buildinfo(self, payload):
        """Given the payload from a message from Travis CI's Webhook, extract
        all relevant data and create an extended commit object. An extended
        commit object is a dictionary with the following keys:

        - author: The commit's author.
        - branch: The branch into which the commit was pushed.
        - revision: Commit's hash.
        - message: The complete commit message.
        - shortmessage: Only the first line of the commit message.
        - url: URL to the changeset on GitHub.
        - reporturl: URL to the build results at Travis CI.
        - statusmessage: Travis CI status message.
        """

        commit = {}
        for (data_key, key) in [("author_name", "author"),
                                ("commit", "revision"),
                                ("message", "message"),
                                ("compare_url", "url"),
                                ("branch", "branch"),
                                ("status_message", "statusmessage"),
                                ("build_url", "reporturl")]:
            commit[key] = payload[data_key]

        commit["shortmessage"] = short_commit_message(commit["message"])

        return commit

class WebhookListenerFactory(object):
    def create(self, service, project, config, observer):
        message_format = string.Template(config["message"])
        resource = service.get_resource_for_project(project)
        child = WebhookListener(
            project, observer, message_format, self.commit_extractor,
            config.get("max commit messages per push"))
        resource.putChild(self.name, child)

class BitbucketListenerFactory(WebhookListenerFactory):
    name = u"bitbucket"
    commit_extractor = staticmethod(extract_bitbucket_commit)

class GitHubListenerFactory(WebhookListenerFactory):
    name = u"github"
    commit_extractor = staticmethod(extract_github_commit)

class TravisCIListenerFactory(object):
    name = u"travisci"

    def create(self, service, project, config, observer):
        message_format = string.Template(config["message"])
        travis_token = config["token"]
        resource = service.get_resource_for_project(project)
        child = TravisCIWebhookListener(project, observer, message_format,
                                        travis_token)
        resource.putChild(self.name, child)

registry.register(BitbucketListenerFactory())
registry.register(GitHubListenerFactory())
registry.register(TravisCIListenerFactory())
