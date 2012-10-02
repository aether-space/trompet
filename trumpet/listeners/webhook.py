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

from twisted.web import resource

from trumpet.listeners import registry

def short_commit_message(message):
    "Returns the first line of a commit message."
    lines = "message".splitlines()
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
    commit["url"] = "http://bitbucket.org%schangeset/%s" % (
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
    if ref.startswith("ref/heads/"):
        ref = ref[len("ref/heads/"):]
    commit["branch"] = ref
    commit["shortmessage"] = short_commit_message(commit["message"])
    return commit

class WebhookListener(resource.Resource):
    """
    Resource waiting for a push notification.
    """

    def __init__(self, project, observer, message_format, commit_extractor):
        resource.Resource.__init__(self)
        self.project = project
        self.observer = observer
        self.message_format = message_format
        self.extract_commit = commit_extractor

    def render_POST(self, request):
        if not "payload" in request.args:
            request.setResponseCode(406)
            return ""
        commits = []
        try:
            payload = json.loads(request.args["payload"][0])
            for data in payload["commits"]:
                commits.append(self.extract_commit(payload, data))
        except (KeyError, ValueError):
            request.setResponseCode(406)
        for commit in commits:
            message = self.message_format.safe_substitute(
                project=self.project, **commit)
            self.observer.notify(self.project, message)
        return ""

class WebhookListenerFactory(object):
    def create(self, service, project, config, observer):
        message_format = string.Template(config["message"])
        child = WebhookListener(
            project, observer, message_format, self.commit_extractor)
        service.web.putChild(config["token"], child)

class BitbucketListenerFactory(WebhookListenerFactory):
    name = u"bitbucket"
    commit_extractor = staticmethod(extract_bitbucket_commit)

class GitHubListenerFactory(WebhookListenerFactory):
    name = u"github"
    commit_extractor = staticmethod(extract_github_commit)

registry.register(BitbucketListenerFactory())
registry.register(GitHubListenerFactory())
