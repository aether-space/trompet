# encoding: utf-8

from twisted.web import xmlrpc

from trumpet.listeners import registry


class XMLRPCInterface(xmlrpc.XMLRPC):
    def __init__(self, project, observer, *args, **kwargs):
        xmlrpc.XMLRPC.__init__(self, *args, **kwargs)
        self.project = project
        self.observer = observer

    def xmlrpc_notify(self, message):
        self.observer.notify(self.project, message)
        return True

class ListenerFactory(object):
    name = u"xmlrpc"

    def create(self, service, project, config, observer):
        if config:
            resource = service.get_resource_for_project(project)
            resource.putChild("xmlrpc", XMLRPCInterface(project, observer))

listener_factory = ListenerFactory()
registry.register(listener_factory)
