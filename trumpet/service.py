# encoding: utf-8

from twisted.application import service
from twisted.web import resource

from trumpet import listeners


class ConfigurationError(Exception):
    "Raised when there is an error in the configuration."


class Trumpet(service.MultiService):
    """
    The notify service itself.
    """

    def __init__(self, config):
        service.MultiService.__init__(self)
        self.config = config
        self.irc = {}
        self._resources = {}

    def add_project(self, project_name, config):
        if "token" not in config:
            msg = "Required config setting 'token' not found for project %r"
            raise ConfigurationError(msg % (project_name, ))
        token = config["token"]
        if token in self.web.children:
            raise ConfigurationError("token %r already used" % (token, ))
        child = resource.Resource()
        self.web.putChild(token, child)
        self._resources[project_name] = child
        # Configure listeners
        for (name, value) in config.iteritems():
            if name in ["channels", "token"]:
                continue
            try:
                listener_factory = listeners.registry.get(name)
            except KeyError:
                msg = "Unknown config setting %r for project %r"
                raise ConfigurationError(msg % (name, project_name))
            listener_factory.create(self, project_name, value, self)

    def get_resource_for_project(self, project):
        "Given a project's name, return the corresponding web resource."
        return self._resources[project]

    def notify(self, project_name, message):
        """Inform all IRC channels that are associated with a project
        that something happened.
        """
        project_config = self.config["projects"][project_name]
        for (network, channels) in project_config["channels"].iteritems():
            bot = self.irc[network]
            for channel in channels:
                bot.msg(channel, message)
