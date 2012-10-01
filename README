=======
trumpet
=======

trumpet is an IRC bot for transmitting commit messages to IRC
channels. It comes with an XML-RPC interface for receiving messages as
well as a Bitbucket POST Service receiver.


Requirements
============

trumpet requires Python_ 2.5 or newer (not including any of the Python
3 releases) as well as Twisted_ (only tested with Twisted 12).


Configuration
=============

See `config.sample` for a sample configuration.


bitbucket
---------

Just add something like the following to your project configuration:

::

   "bitbucket": {
       "message": "$author committed rev $revision to $project/$branch: $shortmessage - $url",
       "token": "my_secret_token"
    }

where ``my_secret_token`` is some random string. You can then point
your POST Service URL at your bitbucket repository to
``http://host:port/token``.


XML-RPC
-------

XXX to be written


Usage
=====

trumpet is started using `twistd`. Just run

::
   
   twistd trumpet <path to config file>

See `twistd(1)` for additional options.


Reporting Bugs
==============

Bugs are reported best at trumpet's `project page`_ on github.


License
=======

trumpet is distributed under a 3-clause BSD license. See `LICENSE` for
details.

trumpet is a `buffer.io`_ project.

.. _buffer.io: http://buffer.io/
.. _Python: http://python.org/
.. _Twisted: http://twistedmatrix.com/
.. _project page: https://github.com/bufferio/trumpet
