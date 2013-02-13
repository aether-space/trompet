# encoding: utf-8

from setuptools import setup


def regenerate_dropin_cache():
    """Make Twisted regenerate the dropin.cache, if possible. This is
    necessary because in a site-wide install, dropin.cache cannot be
    rewritten by normal users.
    """
    try:
        from twisted.plugin import IPlugin, getPlugins
    except ImportError:
        pass
    else:
        list(getPlugins(IPlugin))


setup(
    name="trompet",
    description="The commit announcement IRC bot.",
    packages=["trompet", "trompet.listeners", "trompet.test", "twisted.plugins"],
    version="0.1",
    author="Andreas Stührk",
    author_email="andreas@buffer.io",
    install_requires=[
        "twisted"
    ],
    zip_safe=False)


regenerate_dropin_cache()
