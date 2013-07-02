from twisted.internet import protocol
from twisted.words.protocols import irc

class IRCBot(irc.IRCClient):
    encoding = "utf8"
    nickname = property(lambda self: self.factory.nickname)
    password = property(lambda self: self.factory.password)

    def sendLine(self, line):
        if isinstance(line, unicode):
            line = line.encode(self.encoding)
        return irc.IRCClient.sendLine(self, line)

    def signedOn(self):
        self.factory.resetDelay()
        if self.factory.nickserv_pw:
            self.msg("NickServ", "IDENTIFY " + self.factory.nickserv_pw)
        for channel in self.factory.channels:
            self.join(channel)


class IRCFactory(protocol.ReconnectingClientFactory):
    protocol = IRCBot

    def __init__(self, service, network, nickname, channels=None,
                 nickserv_pw=None, password=None):
        if channels is None:
            channels = []
        self.service = service
        self.network = network
        self.nickname = nickname
        self.channels = channels
        self.nickserv_pw = nickserv_pw
        self.password = password

    def reconfigure(self, bot, nickname, channels=None, nickserv_pw=None):
        if nickname != self.nickname:
            bot.setNick(nickname)
            self.nickname = nickname
        if nickserv_pw != self.nickserv_pw:
            self.nickserv_pw = nickserv_pw
        new_channels = set(channels or None)
        current_channels = set(self.channels)
        to_join = new_channels - current_channels
        to_leave = current_channels - new_channels
        for channel in to_leave:
            bot.leave(channel)
        for channel in to_join:
            bot.join(channel)
        self.channels = channels

    def buildProtocol(self, addr):
        p = protocol.ClientFactory.buildProtocol(self, addr)
        self.service.add_irc_bot(self.network, p)
        return p
