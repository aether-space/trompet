#!/usr/bin/env python
# encoding: utf-8

"""
    Post-receive hook for git.
"""

from __future__ import with_statement
import os
import string
import subprocess
import sys
from xmlrpclib import ServerProxy


### CONFIG SETTINGS START HERE

XMLRPC_ADDR =  ('localhost', 1234)
PROJECT_TOKEN = 'example token'
MESSAGE = string.Template(
    "$author committed rev $rev to $repo/$branch: $shortmessage")

### END OF CONFIG SETTINGS


def get_output(*args):
    """Returns a subprocess's output as unicode string. Assumes the
    output is encoded in UTF-8.
    """
    data = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return data.strip().decode("utf-8")

def short_commit_message(message):
    "Returns the first line of a commit message."
    lines = message.splitlines()
    shortmessage = lines[0]
    if len(lines) > 1:
        shortmessage += u"…"
    return shortmessage

def format_commit_message(repo, refname, rev):
    message = get_output('git', 'cat-file', 'commit', rev)

    attributes = dict(branch=refname, repo=repo, rev=rev[:12])
    linesiter = iter(message.splitlines())
    for line in linesiter:
        if not line:
            break
        (key, value) = line.split(None, 1)
        if key in ['author', 'committer']:
            # Remove date
            value = value.rsplit(None, 2)[0]
            # Remove mail address
            try:
                value = value[:value.index(' <')]
            except ValueError:
                pass
        attributes[key] = value
    message = '\n'.join(linesiter)
    attributes['message'] = message
    attributes['shortmessage'] = short_commit_message(message)
    return MESSAGE.safe_substitute(**attributes)

def main():
    addr_params = XMLRPC_ADDR + (PROJECT_TOKEN, )
    bot = ServerProxy('http://%s:%i/%s/xmlrpc' % addr_params)
    repo = os.path.basename(os.getcwd())
    if repo.endswith('.git'):
        repo = repo[:-len('.git')]

    messages = []
    for line in sys.stdin:
        (old, new, refname) = line.split()
        if refname.startswith('refs/heads/'):
            refname = refname[len('refs/heads/'):]
            if new.strip('0'):
                if old.strip('0'):
                    revisions = get_output('git', 'rev-list',
                                            '%s..%s' % (old, new)).splitlines()
                    for revision in reversed(revisions):
                        msg = format_commit_message(repo, refname, revision)
                        messages.append(msg)
                else:
                    messages.append('New branch: %s/%s' % (repo, refname))
                    messages.append(
                        format_commit_message(repo, refname, new))
            else:
                messages.append(
                    'Branch %s/%s deleted (was: %s)' % (repo, refname, old))
    if messages:
        bot.notify("\n".join(messages))

if __name__ == '__main__':
    main()
