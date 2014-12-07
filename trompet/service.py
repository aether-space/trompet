# encoding: utf-8

try:
    import json
except ImportError:
    import simplejson as json
import random
import re
import signal
import sys

from twisted import plugin
from twisted.application import internet, service
from twisted.python import usage
from twisted.web import resource
from zope.interface import implements

from trompet import irc, listeners
from trompet.web import create_web_service, reconfigure_web_service


class ConfigurationError(Exception):
    "Raised when there is an error in the configuration."


class Project(object):
    def __init__(self, name, token, channels, resource):
        self.name = name
        self.token = token
        self.channels = channels
        self.resource = resource
        self.listeners = []

    def __repr__(self):
        return "<Project(name=%r, token=%r)>" % (self.name, self.token)


class Trompet(service.MultiService):
    """
    The notify service itself.
    """

    _valid_token = re.compile('^[a-zA-Z0-9_-]+$').match

    def __init__(self, maker):
        service.MultiService.__init__(self)
        self._maker = maker
        self._irc = {}
        self.projects = {}
        self._previous_sighup_handler = None

    def add_project(self, project_name, config):
        self._check_project_config(project_name, config)
        token = config["token"]
        if token in self.web.children:
            raise ConfigurationError("token %r already used" % (token, ))
        child = resource.Resource()
        self.web.putChild(token, child)
        project = Project(project_name, token, config["channels"], child)
        self.projects[project_name] = project
        # Configure listeners
        for (name, value) in config.iteritems():
            if name in ["channels", "token"]:
                continue
            try:
                listener_factory = listeners.registry.get(name)
            except KeyError:
                msg = "Unknown config setting %r for project %r"
                raise ConfigurationError(msg % (name, project_name))
            project.listeners.append(name)
            listener_factory.create(self, project_name, value, self)

    def add_irc_bot(self, name, bot):
        self._irc[name] = bot

    def get_irc_bot(self, name):
        return self._irc[name]

    def get_resource_for_project(self, project_name):
        "Given a project's name, return the corresponding web resource."
        return self.projects[project_name].resource

    def notify(self, project_name, message):
        """Inform all IRC channels that are associated with a project
        that something happened.
        """
        project = self.projects[project_name]
        for (network, channels) in project.channels.iteritems():
            bot = self._irc[network]
            for channel in channels:
                bot.msg(channel, message)

    def startService(self):
        service.MultiService.startService(self)
        if hasattr(signal, "SIGHUP"):
            self._previous_sighup_handler = signal.signal(
                signal.SIGHUP, self._handle_sighup)

    def stopService(self):
        service.MultiService.stopService(self)
        if self._previous_sighup_handler is not None:
            signal.signal(signal.SIGHUP, self._previous_sighup_handler)

    def _handle_sighup(self, ignored_signum, ignored_frame):
        # Clean up all projects
        for project in self.projects.values():
            self.web.delEntity(project.token)
        self.projects.clear()
        # …then reconfigure (will add the projects again)
        self._maker.reconfigure(self, self._maker.parse_config())

    def _check_project_config(self, project_name, config):
        if "token" not in config:
            msg = "Required config setting 'token' not found for project %r"
            raise ConfigurationError(msg % (project_name, ))
        elif not self._valid_token(config["token"]):
            msg = ("Project %r: Invalid value for setting 'token': %r "
                   "(allowed: a-z, A-Z, 0-9, _, -)")
            raise ConfigurationError(msg % (project_name, config["token"]))


class TrompetOptions(usage.Options):
    def parseArgs(self, *args):
        if len(args) == 1:
            self.config = args[0]
        else:
            self.opt_help()

    def getSynopsis(self):
        return 'Usage: twistd [options] trompet <config file>'


class TrompetMaker(object):
    implements(service.IServiceMaker, plugin.IPlugin)

    tapname = "trompet"
    description = "The commit message spambot."
    options = TrompetOptions

    def makeService(self, options):
        self.config_path = options.config
        config = self.parse_config()

        trompet = Trompet(self)
        create_web_service(trompet, config)
        self.reconfigure(trompet, config)
        return trompet

    def parse_config(self):
        with open(self.config_path) as config_file:
            config = json.load(config_file)

        for network in config["networks"].values():
            network["channels"] = set()
        return config

    def reconfigure(self, trompet, config):
        reconfigure_web_service(trompet, config)

        networks = config["networks"]
        for (project_name, project) in config["projects"].iteritems():
            try:
                trompet.add_project(project_name, project)
            except ConfigurationError, e:
                sys.stderr.write(e.args[0] + "\n")
                sys.exit(1)
            for (network, channels) in project["channels"].iteritems():
                networks[network]["channels"].update(channels)

        for (name, network) in networks.iteritems():
            try:
                ircbot = trompet.get_irc_bot(name)
            except KeyError:
                (host, port) = random.choice(network["servers"])
                factory = irc.IRCFactory(trompet, name, network["nick"],
                                         network["channels"],
                                         network.get("nickserv-password", None),
                                         network.get("password", None))
                irc_service = internet.TCPClient(host, port, factory)
                irc_service.setName("irc-" + name)
                irc_service.setServiceParent(trompet)
            else:
                ircbot.factory.reconfigure(
                    ircbot, network["nick"], network["channels"],
                    network.get("nickserv-password", None),
                    network.get("password", None))
