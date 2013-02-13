=======
trompet
=======

trompet is an IRC bot for transmitting commit messages to IRC
channels. It comes with an XML-RPC interface for receiving messages as
well as a Bitbucket POST Service receiver.


Requirements
============

trompet requires Python_ 2.5 or newer (not including any of the Python
3 releases) as well as Twisted_ (only tested with Twisted 12).


Configuration
=============

trompet uses JSON for its configuration file. It's a single JSON
object with the following keys: networks_, web_ and projects_.

See `config.sample` for a sample configuration.


networks
--------

The IRC networks to which trompet should connect. Every network
requires at least the keys `servers` and `nick`. The key
`nickserv-password` is optional. trompet uses a randomly chosen item
out of ``servers`` for connecting.

Example:

::

   "networks": {
        "example": {
	    "servers": [["irc.example.org", 6667]],
            "nick": "trompet",
            "nickserv-password": "secret"
	}
    }

.. note::

  You might have noticed that no channels are configured for the
  networks. That is because every project in the projects_ section has
  a list of channels to which trompet should announce commits.


web
---

An object with only one key, `port`. Specifies on which port trompet
listens to service requests.

Example:

::

   "web": {
        "port": 8080
    }

projects
--------

Each project requires at least the following keys: `channels` and
`token`. `token` should be a random, not easily guessable string.

Example:

::

   "projects": {
        "example project": {
            "channels": {"example": ["#example"]},
	    "token": "my secret token",
            "bitbucket": {
                "message": "$author committed rev $revision to $project/$branch: $shortmessage - $url"
            },
	    "xmlrpc": true
        }
    }


Service listeners
-----------------

bitbucket
^^^^^^^^^

Just add something like the following to your project configuration:

::

   "bitbucket": {
       "message": "$author committed rev $revision to $project/$branch: $shortmessage - $url"
    }

You can then point your POST Service URL at your bitbucket repository
to ``http://host:port/<project token>/bitbucket``.

The following variables can be used in ``message``:

- author: The commit's author.
- branch: The branch into which the commit was pushed.
- revision: Commit's (short) hash.
- message: The complete commit message.
- shortmessage: Only the first line of the commit message.
- url: URL to the changeset on bitbucket.


GitHub
^^^^^^

Like bitbucket_, but replace `bitbucket` with `github`.


XML-RPC
^^^^^^^

Add the following snippet to you project configuration:

::

   "xmlrpc": true


The XML-RPC interface can be reached under
``http://host:port/<project token>/xmlrpc``. For sending messages,
one can use the method ``notify(message)``.


Usage
=====

trompet is started using `twistd`. Just run

::
   
   twistd trompet <path to config file>

See `twistd(1)` for additional options.


Reporting Bugs
==============

Bugs are reported best at trompet's `project page`_ on github.


License
=======

trompet is distributed under a 3-clause BSD license. See `LICENSE` for
details.

trompet is a `buffer.io`_ project.

.. _buffer.io: http://buffer.io/
.. _Python: http://python.org/
.. _Twisted: http://twistedmatrix.com/
.. _project page: https://github.com/bufferio/trompet
