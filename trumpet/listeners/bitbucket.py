# encoding: utf-8

"""
    Listener for bitbucket's POST Service.

    See https://confluence.atlassian.com/display/BITBUCKET/Setting+Up+the+Bitbucket+POST+Service
"""

try:
    import json
except ImportError:
    import simplejson as json
import string

from twisted.web import resource

from trumpet.listeners import registry

def extract_commit(repository, commit_data):
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
        repository["absolute_url"], commit_data["node"])
    lines = commit["message"].splitlines()
    commit["shortmessage"] = lines[0]
    if len(lines) > 1:
        commit["shortmessage"] += u"…"
    return commit

class HookListener(resource.Resource):
    """
    Resource waiting for a push notification from bitbucket.
    """

    def __init__(self, project, observer, message_format):
        resource.Resource.__init__(self)
        self.project = project
        self.observer = observer
        self.message_format = message_format

    def render_POST(self, request):
        if not "payload" in request.args:
            request.setResponseCode(406)
            return ""
        commits = []
        try:
            payload = json.loads(request.args["payload"][0])
            for data in payload["commits"]:
                commits.append(extract_commit(payload["repository"], data))
        except (KeyError, ValueError):
            request.setResponseCode(406)
        for commit in commits:
            message = self.message_format.safe_substitute(
                project=self.project, **commit)
            self.observer.notify(self.project, message)
        return ""

class ListenerFactory(object):
    name = u"bitbucket"

    def create(self, service, project, config, observer):
        message_format = string.Template(config["message"])
        child = HookListener(project, observer, message_format)
        service.web.putChild(config["token"], child)

listener_factory = ListenerFactory()
registry.register(listener_factory)
