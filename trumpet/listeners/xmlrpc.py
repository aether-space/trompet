# encoding: utf-8

from twisted.web import xmlrpc

from trumpet.listeners import registry


class XMLRPCInterface(xmlrpc.XMLRPC):
    def __init__(self, observer, *args, **kwargs):
        xmlrpc.XMLRPC.__init__(self, *args, **kwargs)
        self.projects = {}
        self.observer = observer

    def register(self, project, token):
        "Registers the given project under the given token."
        self.projects[token] = project

    def xmlrpc_notify(self, token, message):
        try:
            project = self.projects[token]
        except KeyError:
            return False
        self.observer.notify(project, message)
        return True

class ListenerFactory(object):
    name = u"xmlrpc"

    def create(self, service, project, config, observer):
        child = service.web.children.get("xmlrpc")
        if child is None:
            child = XMLRPCInterface(observer)
            service.web.putChild("xmlrpc", child)
        child.register(project, config["token"])

listener_factory = ListenerFactory()
registry.register(listener_factory)
