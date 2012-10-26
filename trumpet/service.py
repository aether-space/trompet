# encoding: utf-8

try:
    import json
except ImportError:
    import simplejson as json
import random

from twisted import plugin
from twisted.application import internet, service
from twisted.python import usage
from twisted.web import resource, server
from zope.interface import implements

from trumpet import irc, listeners


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


class TrumpetOptions(usage.Options):
    def parseArgs(self, *args):
        if len(args) == 1:
            self.config = args[0]
        else:
            self.opt_help()

    def getSynopsis(self):
        return 'Usage: twistd [options] trumpet <config file>'

class TrumpetMaker(object):
    implements(service.IServiceMaker, plugin.IPlugin)

    tapname = "trumpet"
    description = "The commit message spambot."
    options = TrumpetOptions

    def makeService(self, options):
        with open(options.config) as config_file:
            config = json.load(config_file)

        networks = config["networks"]
        for network in networks.values():
            network["channels"] = set()

        trumpet = Trumpet(config)

        trumpet.web = resource.Resource()
        web = internet.TCPServer(config["web"]["port"],
                                 server.Site(trumpet.web))
        web.setServiceParent(trumpet)

        for (project_name, project) in config["projects"].iteritems():
            try:
                trumpet.add_project(project_name, project)
            except trumpet_service.ConfigurationError, e:
                sys.stderr.write(e.args[0] + "\n")
                sys.exit(1)
            for (network, channels) in project["channels"].iteritems():
                networks[network]["channels"].update(channels)

        for (name, network) in networks.iteritems():
            (host, port) = random.choice(network["servers"])
            factory = irc.IRCFactory(trumpet, name, network["nick"],
                                     network["channels"],
                                     network.get("nickserv-password", None))
            ircbot = internet.TCPClient(host, port, factory)
            ircbot.setName("irc-" + name)
            ircbot.setServiceParent(trumpet)

        return trumpet
