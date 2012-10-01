# encoding: utf-8

class _ServiceRegistry(object):
    def __init__(self):
        self.services = {}

    def get(self, name):
        """
        Return the handler for the given name. Raises `KeyError` if
        the handler does not exist.
        """
        return self.services[name]

    def register(self, service):
        """
        Register the given service. Returns the service so it can
        be used as decorator.
        """
        if service.name in self.services:
            raise ValueError("Service %r already registered" % (service.name, ))
        self.services[service.name] = service
        return service

registry = _ServiceRegistry()
