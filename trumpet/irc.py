from twisted.internet import protocol
from twisted.words.protocols import irc

class IRCBot(irc.IRCClient):
    encoding = "utf8"
    nickname = property(lambda self: self.factory.nickname)

    def sendLine(self, line):
        if isinstance(line, unicode):
            line = line.encode(self.encoding)
        return irc.IRCClient.sendLine(self, line)

    def signedOn(self):
        if self.factory.nickserv_pw:
            self.msg("NickServ", "IDENTIFY " + self.factory.nickserv_pw)
        for channel in self.factory.channels:
            self.join(channel)

class IRCFactory(protocol.ClientFactory):
    protocol = IRCBot

    def __init__(self, service, network, nickname, channels=None,
                 nickserv_pw=None):
        if channels is None:
            channels = []
        self.service = service
        self.network = network
        self.nickname = nickname
        self.channels = channels
        self.nickserv_pw = nickserv_pw

    def buildProtocol(self, addr):
        p = protocol.ClientFactory.buildProtocol(self, addr)
        self.service.irc[self.network] = p
        return p
