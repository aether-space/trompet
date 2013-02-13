from twisted.application import internet
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.web import server
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory
from twisted.web.resource import IResource, Resource
from zope.interface import implements


class Root(Resource):
    isLeaf = True

    HTML = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="robots" content="noindex" />
      <title>Welcome to trompet!</title>
    </head>
    <body>
      <h1>Welcome to trompet</h1>

      <p>Hello, I'm trompet, the commit announcement bot. Learn more about me
      at <a href="http://buffer.io/+trompet">my homepage.</a></p>

      <p>For a list of configured projects, visit
      <a href="/projects">/projects</a> (note: password protected).</p>
    </body>
    </html>
    """

    def render_GET(self, request):
        return self.HTML


class ProjectsListingRealm(object):
    implements(IRealm)

    def __init__(self, config):
        self._config = config

    def requestAvatar(self, avatarID, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, ProjectsListing(self._config), lambda: None)
        raise NotImplementedError()


class ProjectsListing(Resource):
    isLeaf = True

    def __init__(self, config):
        Resource.__init__(self)
        self._config = config

    def render_GET(self, request):
        parts = ["""
            <!DOCTYPE html>
            <html>
              <head>
              <title>Projects</title>
            </head>
            <body>
              <ul>
        """]
        for (name, config) in self._config["projects"].iteritems():
            parts.append(self._render_project(request, name, config))
        parts.append("</ul></body></html>")
        return "".join(parts)

    def _render_project(self, request, project_name, config):
        parts = ["<li>", project_name.encode("utf-8"), "<ul>"]
        root_url = request.prePathURL()[:-len("/projects")]
        for name in config:
            if name not in ["channels", "token"]:
                name = str(name)
                url = "/".join([root_url, str(config["token"]), name])
                parts.append('<li><a href="%s">%s</a></li>' % (url, name))
        parts.append("</ul></li>")
        return "".join(parts)


def create_web_service(config):
    "Creates the web service. Returns a tuple (service, site)."
    site = Resource()
    site.putChild("", Root())
    password = config["web"]["password"]
    portal = Portal(
        ProjectsListingRealm(config),
        [InMemoryUsernamePasswordDatabaseDontUse(admin=password)])
    credential_factory = DigestCredentialFactory('md5', 'trompet login')
    projects_resource = HTTPAuthSessionWrapper(portal, [credential_factory])
    site.putChild("projects", projects_resource)
    service = internet.TCPServer(config["web"]["port"], server.Site(site))
    return (service, site)
