# encoding: utf-8

from twisted.application import service

class Trumpet(service.MultiService):
    """
    The notify service itself.
    """

    def __init__(self, config):
        service.MultiService.__init__(self)
        self.config = config
        self.irc = {}

    def notify(self, project_name, message):
        """Inform all IRC channels that are associated with a project
        that something happened.
        """
        project_config = self.config["projects"][project_name]
        for (network, channels) in project_config["channels"].iteritems():
            bot = self.irc[network]
            for channel in channels:
                bot.msg(channel, message)
