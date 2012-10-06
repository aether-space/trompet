from __future__ import with_statement
try:
    import json
except ImportError:
    import simplejson as json
import random
import sys

from twisted import plugin
from twisted.application import internet, service
from twisted.python import usage
from twisted.web import resource, server
from zope.interface import implements

from trumpet import irc, service as trumpet_service

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

        trumpet = trumpet_service.Trumpet(config)

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

serviceMaker = TrumpetMaker()
